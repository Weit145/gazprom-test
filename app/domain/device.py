import uuid
from dataclasses import dataclass

from app.domain.base import Entity


@dataclass(slots=True)
class Device(Entity):
    user_id: uuid.UUID | None = None


@dataclass(slots=True)
class DeviceData(Entity):
    device_id: uuid.UUID | None = None
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
