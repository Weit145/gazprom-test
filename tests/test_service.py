import asyncio
import datetime
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

import app.usecase.service as service_module
from app.transport.api.v1.schemas.device import CreateDevice
from app.transport.api.v1.schemas.user import CreateUser
from app.usecase.service import Service


def run_async(coro):
    return asyncio.run(coro)


def make_session() -> Mock:
    session = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


def make_service(repo: Mock) -> Service:
    service = Service()
    service.repo = repo
    return service


def make_row(
    x_count: int = 2,
    device_id: uuid.UUID | None = None,
) -> dict[str, float | int | uuid.UUID]:
    row: dict[str, float | int | uuid.UUID] = {
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
    if device_id is not None:
        row["device_id"] = device_id
    return row


def make_cache(device_id: uuid.UUID, x_count: int = 2) -> SimpleNamespace:
    return SimpleNamespace(
        device_id=device_id,
        updated_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        **make_row(x_count=x_count),
    )


def test_create_device_data_creates_data_commits_and_schedules_task(monkeypatch):
    device_id = uuid.uuid4()
    created_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    session = make_session()
    repo = Mock()
    repo.get_or_create_device = AsyncMock(return_value=SimpleNamespace(id=device_id))
    repo.create_device_data = AsyncMock(
        return_value=SimpleNamespace(x=1.0, y=2.0, z=3.0, created_at=created_at)
    )
    delay = Mock()
    monkeypatch.setattr(service_module.recalculate_device_analytics, "delay", delay)
    service = make_service(repo)

    result = run_async(
        service.create_device_data(
            device_id,
            CreateDevice(x=1.0, y=2.0, z=3.0),
            session,
        )
    )

    repo.get_or_create_device.assert_awaited_once_with(device_id, session)
    created_device_data, passed_session = repo.create_device_data.await_args.args
    assert created_device_data.device_id == device_id
    assert created_device_data.x == 1.0
    assert created_device_data.y == 2.0
    assert created_device_data.z == 3.0
    assert passed_session is session
    session.commit.assert_awaited_once_with()
    delay.assert_called_once_with(str(device_id))
    assert result.id == device_id
    assert result.x == 1.0
    assert result.y == 2.0
    assert result.z == 3.0
    assert result.created_at == created_at


def test_get_device_analytics_uses_fresh_cache_for_all_time():
    device_id = uuid.uuid4()
    session = make_session()
    repo = Mock()
    repo.get_device_by_id = AsyncMock(return_value=SimpleNamespace(id=device_id))
    repo.get_device_analytics_cache = AsyncMock(return_value=make_cache(device_id))
    repo.is_device_analytics_cache_fresh = AsyncMock(return_value=True)
    repo.get_device_analytics = AsyncMock()
    service = make_service(repo)

    result = run_async(service.get_device_analytics(device_id, None, None, session))

    assert result.id == device_id
    assert result.x.count == 2
    assert result.y.median == 20.0
    repo.get_device_analytics.assert_not_awaited()


def test_get_device_analytics_recalculates_when_cache_is_stale():
    device_id = uuid.uuid4()
    session = make_session()
    repo = Mock()
    repo.get_device_by_id = AsyncMock(return_value=SimpleNamespace(id=device_id))
    repo.get_device_analytics_cache = AsyncMock(return_value=make_cache(device_id))
    repo.is_device_analytics_cache_fresh = AsyncMock(return_value=False)
    repo.get_device_analytics = AsyncMock(return_value=make_row(x_count=3))
    service = make_service(repo)

    result = run_async(service.get_device_analytics(device_id, None, None, session))

    assert result.id == device_id
    assert result.x.count == 3
    repo.get_device_analytics.assert_awaited_once_with(device_id, None, None, session)


def test_get_device_analytics_returns_not_found_when_device_missing():
    device_id = uuid.uuid4()
    session = make_session()
    repo = Mock()
    repo.get_device_by_id = AsyncMock(return_value=None)
    repo.get_device_analytics_cache = AsyncMock()
    service = make_service(repo)

    with pytest.raises(HTTPException) as exc_info:
        run_async(service.get_device_analytics(device_id, None, None, session))

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    repo.get_device_analytics_cache.assert_not_awaited()


def test_period_validation_rejects_inverted_range():
    service = Service()
    date_from = datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc)
    date_to = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)

    with pytest.raises(HTTPException) as exc_info:
        service._validate_period(date_from, date_to)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_create_user_commits_before_returning_response():
    created_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    user_id = uuid.uuid4()
    session = make_session()
    repo = Mock()
    repo.create_user = AsyncMock(
        return_value=SimpleNamespace(id=user_id, name="alex", created_at=created_at)
    )
    service = make_service(repo)

    result = run_async(service.create_user(CreateUser(name="alex"), session))

    created_user, passed_session = repo.create_user.await_args.args
    assert created_user.name == "alex"
    assert passed_session is session
    session.commit.assert_awaited_once_with()
    session.rollback.assert_not_awaited()
    assert result.id == user_id
    assert result.name == "alex"
    assert result.created_at == created_at


def test_create_user_returns_conflict_on_duplicate_name():
    session = make_session()
    repo = Mock()
    repo.create_user = AsyncMock(
        side_effect=IntegrityError("insert user", {}, Exception("duplicate"))
    )
    service = make_service(repo)

    with pytest.raises(HTTPException) as exc_info:
        run_async(service.create_user(CreateUser(name="alex"), session))

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert isinstance(exc_info.value.__cause__, IntegrityError)
    session.rollback.assert_awaited_once_with()
    session.commit.assert_not_awaited()


def test_add_device_to_user_commits_before_returning_response():
    user_id = uuid.uuid4()
    device_id = uuid.uuid4()
    created_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    session = make_session()
    repo = Mock()
    repo.add_device_to_user = AsyncMock(
        return_value=SimpleNamespace(id=device_id, created_at=created_at)
    )
    service = make_service(repo)

    result = run_async(service.add_device_to_user(user_id, device_id, session))

    repo.add_device_to_user.assert_awaited_once_with(user_id, device_id, session)
    session.commit.assert_awaited_once_with()
    assert result.user_id == user_id
    assert result.device_id == device_id
    assert result.created_at == created_at


def test_add_device_to_user_returns_not_found_when_user_missing():
    user_id = uuid.uuid4()
    device_id = uuid.uuid4()
    session = make_session()
    repo = Mock()
    repo.add_device_to_user = AsyncMock(return_value=None)
    service = make_service(repo)

    with pytest.raises(HTTPException) as exc_info:
        run_async(service.add_device_to_user(user_id, device_id, session))

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    session.commit.assert_not_awaited()


def test_get_user_analytics_maps_total_and_device_rows():
    user_id = uuid.uuid4()
    device_id = uuid.uuid4()
    date_from = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    date_to = datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc)
    session = make_session()
    repo = Mock()
    repo.get_user_by_id = AsyncMock(return_value=SimpleNamespace(id=user_id))
    repo.get_user_analytics = AsyncMock(return_value=make_row(x_count=5))
    repo.list_user_devices_analytics = AsyncMock(
        return_value=[make_row(x_count=2, device_id=device_id)]
    )
    service = make_service(repo)

    result = run_async(service.get_user_analytics(user_id, date_from, date_to, session))

    repo.get_user_by_id.assert_awaited_once_with(user_id, session)
    repo.get_user_analytics.assert_awaited_once_with(
        user_id, date_from, date_to, session
    )
    repo.list_user_devices_analytics.assert_awaited_once_with(
        user_id, date_from, date_to, session
    )
    assert result.id == user_id
    assert result.total.x.count == 5
    assert len(result.devices) == 1
    assert result.devices[0].id == device_id
    assert result.devices[0].x.count == 2


def test_get_user_analytics_returns_not_found_when_user_missing():
    user_id = uuid.uuid4()
    session = make_session()
    repo = Mock()
    repo.get_user_by_id = AsyncMock(return_value=None)
    repo.get_user_analytics = AsyncMock()
    service = make_service(repo)

    with pytest.raises(HTTPException) as exc_info:
        run_async(service.get_user_analytics(user_id, None, None, session))

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    repo.get_user_analytics.assert_not_awaited()
