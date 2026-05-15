import datetime
import uuid
from dataclasses import dataclass, field


@dataclass(slots=True)
class Period:
    date_from: datetime.datetime | None = None
    date_to: datetime.datetime | None = None


@dataclass(slots=True)
class DataPoint:
    min: float = 0.0
    max: float = 0.0
    count: int = 0
    sum: float = 0.0
    median: float = 0.0


@dataclass(slots=True)
class Analytics:
    period: Period = field(default_factory=Period)
    x: DataPoint = field(default_factory=DataPoint)
    y: DataPoint = field(default_factory=DataPoint)
    z: DataPoint = field(default_factory=DataPoint)


@dataclass(slots=True)
class DeviceAnalytics(Analytics):
    id: uuid.UUID | None = None


@dataclass(slots=True)
class UserAnalytics:
    id: uuid.UUID | None = None
    total: Analytics = field(default_factory=Analytics)
    devices: list[DeviceAnalytics] = field(default_factory=list)
