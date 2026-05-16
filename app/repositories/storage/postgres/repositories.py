import datetime
import uuid
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.storage.models import (
    Device,
    DeviceAnalyticsCache,
    DeviceData,
    User,
)


class SQLAlchemyRepository:
    async def create_user(self, user: User, session: AsyncSession) -> User:
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def get_user_by_id(
        self,
        user_id: uuid.UUID,
        session: AsyncSession,
    ) -> User | None:
        return await session.get(User, user_id)

    async def create_device(self, device: Device, session: AsyncSession) -> Device:
        session.add(device)
        await session.flush()
        await session.refresh(device)
        return device

    async def get_device_by_id(
        self,
        device_id: uuid.UUID,
        session: AsyncSession,
    ) -> Device | None:
        return await session.get(Device, device_id)

    async def get_or_create_device(
        self,
        device_id: uuid.UUID,
        session: AsyncSession,
    ) -> Device:
        device = await self.get_device_by_id(device_id, session)
        if device is not None:
            return device

        device = Device(id=device_id)
        return await self.create_device(device, session)

    async def create_device_data(
        self,
        device_data: DeviceData,
        session: AsyncSession,
    ) -> DeviceData:
        session.add(device_data)
        await session.flush()
        await session.refresh(device_data)
        return device_data

    async def add_device_to_user(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        session: AsyncSession,
    ) -> Optional[Device]:
        user = await self.get_user_by_id(user_id, session)
        if user is None:
            return None

        device = await self.get_or_create_device(device_id, session)
        device.user_id = user.id
        session.add(device)
        await session.flush()
        await session.refresh(device)
        return device

    async def list_user_devices(
        self,
        user_id: uuid.UUID,
        session: AsyncSession,
    ) -> list[Device]:
        stmt = select(Device).where(Device.user_id == user_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_device_analytics(
        self,
        device_id: uuid.UUID,
        date_from: Optional[datetime.datetime],
        date_to: Optional[datetime.datetime],
        session: AsyncSession,
    ) -> RowMapping:
        stmt = (
            select(*self._analytics_columns())
            .select_from(DeviceData)
            .where(DeviceData.device_id == device_id)
        )
        stmt = self._with_period(stmt, date_from, date_to)
        result = await session.execute(stmt)
        return result.mappings().one()

    async def get_device_analytics_cache(
        self,
        device_id: uuid.UUID,
        session: AsyncSession,
    ) -> Optional[DeviceAnalyticsCache]:
        stmt = select(DeviceAnalyticsCache).where(
            DeviceAnalyticsCache.device_id == device_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_device_analytics_cache_fresh(
        self,
        device_id: uuid.UUID,
        updated_at: datetime.datetime,
        session: AsyncSession,
    ) -> bool:
        stmt = select(func.max(DeviceData.created_at)).where(
            DeviceData.device_id == device_id
        )
        result = await session.execute(stmt)
        latest_data_created_at = result.scalar_one_or_none()
        return latest_data_created_at is None or updated_at >= latest_data_created_at

    # Вставить или обновить
    async def upsert_device_analytics_cache(
        self,
        device_id: uuid.UUID,
        analytics: RowMapping,
        session: AsyncSession,
    ) -> DeviceAnalyticsCache:
        values = self._analytics_cache_values(device_id, analytics)
        insert_stmt = insert(DeviceAnalyticsCache).values(**values)
        # update_values словарь для обновления, исключая device_id
        update_values = {
            key: getattr(insert_stmt.excluded, key)
            for key in values
            if key != "device_id"
        }
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=[DeviceAnalyticsCache.device_id],
            set_=update_values,
        ).returning(DeviceAnalyticsCache)
        result = await session.execute(stmt)
        return result.scalar_one()

    async def get_user_analytics(
        self,
        user_id: uuid.UUID,
        date_from: Optional[datetime.datetime],
        date_to: Optional[datetime.datetime],
        session: AsyncSession,
    ) -> RowMapping:
        stmt = (
            select(*self._analytics_columns())
            .select_from(DeviceData)
            .join(Device, Device.id == DeviceData.device_id)
            .where(Device.user_id == user_id)
        )
        stmt = self._with_period(stmt, date_from, date_to)
        result = await session.execute(stmt)
        return result.mappings().one()

    async def list_user_devices_analytics(
        self,
        user_id: uuid.UUID,
        date_from: Optional[datetime.datetime],
        date_to: Optional[datetime.datetime],
        session: AsyncSession,
    ) -> list[RowMapping]:
        join_condition = self._device_data_join_condition(date_from, date_to)
        stmt = (
            select(Device.id.label("device_id"), *self._analytics_columns())
            .select_from(Device)
            .outerjoin(DeviceData, join_condition)
            .where(Device.user_id == user_id)
            .group_by(Device.id)
        )
        result = await session.execute(stmt)
        return list(result.mappings().all())

    def _device_data_join_condition(self, date_from, date_to):
        conditions = [Device.id == DeviceData.device_id]
        if date_from is not None:
            conditions.append(DeviceData.created_at >= date_from)
        if date_to is not None:
            conditions.append(DeviceData.created_at <= date_to)
        return and_(*conditions)

    def _with_period(self, stmt, date_from, date_to):
        if date_from is not None:
            stmt = stmt.where(DeviceData.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(DeviceData.created_at <= date_to)
        return stmt

    # Аналитика coalesce если вывод None то делает по дефолту 2 аргумент
    def _analytics_columns(self):
        return (
            func.coalesce(func.min(DeviceData.x), 0.0).label("x_min"),
            func.coalesce(func.max(DeviceData.x), 0.0).label("x_max"),
            func.count(DeviceData.x).label("x_count"),
            func.coalesce(func.sum(DeviceData.x), 0.0).label("x_sum"),
            func.coalesce(
                func.percentile_cont(0.5).within_group(DeviceData.x), 0.0
            ).label("x_median"),
            func.coalesce(func.min(DeviceData.y), 0.0).label("y_min"),
            func.coalesce(func.max(DeviceData.y), 0.0).label("y_max"),
            func.count(DeviceData.y).label("y_count"),
            func.coalesce(func.sum(DeviceData.y), 0.0).label("y_sum"),
            func.coalesce(
                func.percentile_cont(0.5).within_group(DeviceData.y), 0.0
            ).label("y_median"),
            func.coalesce(func.min(DeviceData.z), 0.0).label("z_min"),
            func.coalesce(func.max(DeviceData.z), 0.0).label("z_max"),
            func.count(DeviceData.z).label("z_count"),
            func.coalesce(func.sum(DeviceData.z), 0.0).label("z_sum"),
            func.coalesce(
                func.percentile_cont(0.5).within_group(DeviceData.z), 0.0
            ).label("z_median"),
        )

    def _analytics_cache_values(
        self,
        device_id: uuid.UUID,
        analytics: RowMapping,
    ) -> dict[str, float | int | uuid.UUID | datetime.datetime]:
        values: dict[str, float | int | uuid.UUID | datetime.datetime] = {
            "device_id": device_id,
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
        }
        for prefix in ("x", "y", "z"):
            values[f"{prefix}_min"] = float(analytics[f"{prefix}_min"] or 0.0)
            values[f"{prefix}_max"] = float(analytics[f"{prefix}_max"] or 0.0)
            values[f"{prefix}_count"] = int(analytics[f"{prefix}_count"] or 0)
            values[f"{prefix}_sum"] = float(analytics[f"{prefix}_sum"] or 0.0)
            values[f"{prefix}_median"] = float(analytics[f"{prefix}_median"] or 0.0)
        return values


repository = SQLAlchemyRepository()
