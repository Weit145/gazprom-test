import datetime
import logging
import uuid

from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.tasks import recalculate_device_analytics
from app.repositories.storage.models import DeviceAnalyticsCache, DeviceData, User
from app.repositories.storage.postgres.repositories import repository
from app.transport.api.v1.schemas.device import (
    Analytics,
    CreateDevice,
    DataPoint,
    DeviceAnalytics,
    OutDevice,
    Period,
)
from app.transport.api.v1.schemas.user import (
    CreateUser,
    OutUser,
    UserAnalytics,
    UserDevice,
)


logger = logging.getLogger(__name__)


class Service:
    def __init__(self):
        self.repo = repository

    async def create_device_data(
        self,
        device_id: uuid.UUID,
        device: CreateDevice,
        session: AsyncSession,
    ) -> OutDevice:
        await self.repo.get_or_create_device(device_id, session)
        result = await self.repo.create_device_data(
            DeviceData(
                device_id=device_id,
                x=device.x,
                y=device.y,
                z=device.z,
            ),
            session,
        )
        await session.commit()
        try:
            recalculate_device_analytics.delay(str(device_id))
        except Exception as e:
            logger.error(f"Failed send device analytics task error:{e}")
        return OutDevice(
            id=device_id,
            x=result.x,
            y=result.y,
            z=result.z,
            created_at=result.created_at,
        )

    async def get_device_analytics(
        self,
        device_id: uuid.UUID,
        date_from: Optional[datetime.datetime],
        date_to: Optional[datetime.datetime],
        session: AsyncSession,
    ) -> DeviceAnalytics:
        self._validate_period(date_from, date_to)
        device = await self.repo.get_device_by_id(device_id, session)
        if device is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        if date_from is None and date_to is None:
            cache = await self.repo.get_device_analytics_cache(device_id, session)
            if cache is not None and await self.repo.is_device_analytics_cache_fresh(
                device_id,
                cache.updated_at,
                session,
            ):
                return self._to_device_analytics_from_cache(cache)

        row = await self.repo.get_device_analytics(
            device_id, date_from, date_to, session
        )
        return self._to_device_analytics(device_id, row, date_from, date_to)

    async def create_user(
        self,
        user: CreateUser,
        session: AsyncSession,
    ) -> OutUser:
        try:
            result = await self.repo.create_user(User(name=user.name), session)
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this name already exists",
            ) from exc

        await session.commit()
        return OutUser(
            id=result.id,
            name=result.name,
            created_at=result.created_at,
        )

    async def add_device_to_user(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        session: AsyncSession,
    ) -> UserDevice:
        device = await self.repo.add_device_to_user(user_id, device_id, session)
        if device is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        await session.commit()
        return UserDevice(
            user_id=user_id,
            device_id=device.id,
            created_at=device.created_at,
        )

    async def get_user_analytics(
        self,
        user_id: uuid.UUID,
        date_from: Optional[datetime.datetime],
        date_to: Optional[datetime.datetime],
        session: AsyncSession,
    ) -> UserAnalytics:
        self._validate_period(date_from, date_to)
        user = await self.repo.get_user_by_id(user_id, session)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        total_row = await self.repo.get_user_analytics(
            user_id, date_from, date_to, session
        )
        device_rows = await self.repo.list_user_devices_analytics(
            user_id,
            date_from,
            date_to,
            session,
        )
        return UserAnalytics(
            id=user_id,
            total=self._to_analytics(total_row, date_from, date_to),
            devices=[
                self._to_device_analytics(row["device_id"], row, date_from, date_to)
                for row in device_rows
            ],
        )

    def _to_device_analytics(
        self,
        device_id: uuid.UUID,
        row: RowMapping,
        date_from: Optional[datetime.datetime],
        date_to: Optional[datetime.datetime],
    ) -> DeviceAnalytics:
        analytics = self._to_analytics(row, date_from, date_to)
        return DeviceAnalytics(
            id=device_id,
            period=analytics.period,
            x=analytics.x,
            y=analytics.y,
            z=analytics.z,
        )

    def _to_device_analytics_from_cache(
        self,
        cache: DeviceAnalyticsCache,
    ) -> DeviceAnalytics:
        return DeviceAnalytics(
            id=cache.device_id,
            period=Period(date_from=None, date_to=None),
            x=self._to_data_point_from_cache(cache, "x"),
            y=self._to_data_point_from_cache(cache, "y"),
            z=self._to_data_point_from_cache(cache, "z"),
        )

    def _to_analytics(
        self,
        row: RowMapping,
        date_from: Optional[datetime.datetime],
        date_to: Optional[datetime.datetime],
    ) -> Analytics:
        return Analytics(
            period=Period(date_from=date_from, date_to=date_to),
            x=self._to_data_point(row, "x"),
            y=self._to_data_point(row, "y"),
            z=self._to_data_point(row, "z"),
        )

    def _to_data_point(self, row: RowMapping, prefix: str) -> DataPoint:
        return DataPoint(
            min=float(row[f"{prefix}_min"] or 0.0),
            max=float(row[f"{prefix}_max"] or 0.0),
            count=int(row[f"{prefix}_count"] or 0),
            sum=float(row[f"{prefix}_sum"] or 0.0),
            median=float(row[f"{prefix}_median"] or 0.0),
        )

    def _to_data_point_from_cache(
        self,
        cache: DeviceAnalyticsCache,
        prefix: str,
    ) -> DataPoint:
        return DataPoint(
            min=getattr(cache, f"{prefix}_min"),
            max=getattr(cache, f"{prefix}_max"),
            count=getattr(cache, f"{prefix}_count"),
            sum=getattr(cache, f"{prefix}_sum"),
            median=getattr(cache, f"{prefix}_median"),
        )

    def _validate_period(
        self,
        date_from: Optional[datetime.datetime],
        date_to: Optional[datetime.datetime],
    ) -> None:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="date_from must be less than or equal to date_to",
            )


service = Service()
