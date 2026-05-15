import uuid
import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class Device(BaseModel):
    pass


class CreateDevice(Device):
    x: float = Field(..., description="X coordinate of the device")
    y: float = Field(..., description="Y coordinate of the device")
    z: float = Field(..., description="Z coordinate of the device")


class OutDevice(Device):
    id: uuid.UUID
    x: float = Field(..., description="X coordinate of the device")
    y: float = Field(..., description="Y coordinate of the device")
    z: float = Field(..., description="Z coordinate of the device")
    created_at: datetime.datetime


class DataPoint(BaseModel):
    min: float = Field(..., description="Minimum value of the data point")
    max: float = Field(..., description="Maximum value of the data point")
    count: int = Field(..., description="Count of the data points")
    sum: float = Field(..., description="Sum of the data points")
    median: float = Field(..., description="Median of the data points")


class Period(BaseModel):
    date_from: Optional[datetime.datetime] = Field(None, description="Start date of the period")
    date_to: Optional[datetime.datetime] = Field(None, description="End date of the period")


class Analytics(BaseModel):
    period: Annotated[Period, Field(..., description="Period for which the analytics are calculated")]
    x: Annotated[DataPoint, Field(..., description="Analytics for X coordinate")]
    y: Annotated[DataPoint, Field(..., description="Analytics for Y coordinate")]
    z: Annotated[DataPoint, Field(..., description="Analytics for Z coordinate")]


class DeviceAnalytics(Analytics):
    id: uuid.UUID
