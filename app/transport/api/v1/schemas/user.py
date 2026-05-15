import datetime
import uuid
from typing import Annotated, List

from pydantic import BaseModel, Field

from app.transport.api.v1.schemas.device import Analytics, DeviceAnalytics


class User(BaseModel):
    pass


class CreateUser(User):
    name: str = Field(..., description="Name of the user")


class OutUser(User):
    id: uuid.UUID
    name: str = Field(..., description="Name of the user")
    created_at: datetime.datetime


class UserDevice(BaseModel):
    user_id: uuid.UUID
    device_id: uuid.UUID
    created_at: datetime.datetime


class UserAnalytics(User):
    id: uuid.UUID
    total: Annotated[Analytics, Field(..., description="Analytics for all user devices")]
    devices: Annotated[List[DeviceAnalytics], Field(..., description="Analytics for each user device")]
