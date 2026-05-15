from datetime import datetime, timezone
import uuid
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Device(Base):
    __tablename__ = "device"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="devices")
    data: Mapped[list["DeviceData"]] = relationship(back_populates="device")
    analytics: Mapped[Optional["DeviceAnalyticsCache"]] = relationship(back_populates="device")


class DeviceData(Base):
    __tablename__ = "device_data"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("device.id"),
        nullable=False,
    )
    x: Mapped[float] = mapped_column(nullable=False)
    y: Mapped[float] = mapped_column(nullable=False)
    z: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    device: Mapped["Device"] = relationship(back_populates="data")


class DeviceAnalyticsCache(Base):
    __tablename__ = "device_analytics"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("device.id"),
        nullable=False,
    )
    x_min: Mapped[float] = mapped_column(nullable=False, default=0.0)
    x_max: Mapped[float] = mapped_column(nullable=False, default=0.0)
    x_count: Mapped[int] = mapped_column(nullable=False, default=0)
    x_sum: Mapped[float] = mapped_column(nullable=False, default=0.0)
    x_median: Mapped[float] = mapped_column(nullable=False, default=0.0)

    y_min: Mapped[float] = mapped_column(nullable=False, default=0.0)
    y_max: Mapped[float] = mapped_column(nullable=False, default=0.0)
    y_count: Mapped[int] = mapped_column(nullable=False, default=0)
    y_sum: Mapped[float] = mapped_column(nullable=False, default=0.0)
    y_median: Mapped[float] = mapped_column(nullable=False, default=0.0)

    z_min: Mapped[float] = mapped_column(nullable=False, default=0.0)
    z_max: Mapped[float] = mapped_column(nullable=False, default=0.0)
    z_count: Mapped[int] = mapped_column(nullable=False, default=0)
    z_sum: Mapped[float] = mapped_column(nullable=False, default=0.0)
    z_median: Mapped[float] = mapped_column(nullable=False, default=0.0)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    device: Mapped["Device"] = relationship(back_populates="analytics")

    __table_args__ = (
        UniqueConstraint("device_id", name="unique_device_analytics_device_id"),
    )
