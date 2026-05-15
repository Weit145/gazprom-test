import asyncio
import datetime
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.transport.api.v1.schemas.user import CreateUser
from app.usecase.service import Service


def make_row(x_count: int = 2) -> dict[str, float | int]:
    return {
        "x_min": 1.0,
        "x_max": 3.0,
        "x_count": x_count,
        "x_sum": 4.0,
        "x_median": 2.0,
        "y_min": 10.0,
        "y_max": 30.0,
        "y_count": x_count,
        "y_sum": 40.0,
        "y_median": 20.0,
        "z_min": 100.0,
        "z_max": 300.0,
        "z_count": x_count,
        "z_sum": 400.0,
        "z_median": 200.0,
    }


def make_cache(device_id: uuid.UUID) -> SimpleNamespace:
    return SimpleNamespace(
        device_id=device_id,
        updated_at=datetime.datetime.now(datetime.timezone.utc),
        **make_row(),
    )


class DeviceAnalyticsRepo:
    def __init__(self, device_id: uuid.UUID, cache=None, cache_is_fresh: bool = False):
        self.device_id = device_id
        self.cache = cache
        self.cache_is_fresh = cache_is_fresh
        self.queried_analytics = False

    async def get_device_by_id(self, device_id, session):
        return SimpleNamespace(id=device_id)

    async def get_device_analytics_cache(self, device_id, session):
        return self.cache

    async def is_device_analytics_cache_fresh(self, device_id, updated_at, session):
        return self.cache_is_fresh

    async def get_device_analytics(self, device_id, date_from, date_to, session):
        self.queried_analytics = True
        return make_row(x_count=3)


class DuplicateUserRepo:
    async def create_user(self, user, session):
        raise IntegrityError("insert user", {}, Exception("duplicate"))


class DummySession:
    def __init__(self):
        self.rolled_back = False

    async def rollback(self):
        self.rolled_back = True


def test_get_device_analytics_uses_fresh_cache_for_all_time():
    device_id = uuid.uuid4()
    repo = DeviceAnalyticsRepo(
        device_id,
        cache=make_cache(device_id),
        cache_is_fresh=True,
    )
    service = Service()
    service.repo = repo

    result = asyncio.run(service.get_device_analytics(device_id, None, None, None))

    assert result.id == device_id
    assert result.x.count == 2
    assert result.y.median == 20.0
    assert repo.queried_analytics is False


def test_get_device_analytics_recalculates_when_cache_is_stale():
    device_id = uuid.uuid4()
    repo = DeviceAnalyticsRepo(
        device_id,
        cache=make_cache(device_id),
        cache_is_fresh=False,
    )
    service = Service()
    service.repo = repo

    result = asyncio.run(service.get_device_analytics(device_id, None, None, None))

    assert result.id == device_id
    assert result.x.count == 3
    assert repo.queried_analytics is True


def test_period_validation_rejects_inverted_range():
    service = Service()
    date_from = datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc)
    date_to = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)

    with pytest.raises(HTTPException) as exc_info:
        service._validate_period(date_from, date_to)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_create_user_returns_conflict_on_duplicate_name():
    service = Service()
    service.repo = DuplicateUserRepo()
    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.create_user(CreateUser(name="alex"), session))

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert session.rolled_back is True
