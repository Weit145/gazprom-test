import uuid
import datetime
from fastapi import APIRouter, status, Body, Path, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional
from app.repositories.storage.postgres.db_helper import db_helper
from app.transport.api.v1.schemas.device import CreateDevice, OutDevice, DeviceAnalytics
from app.usecase.service import service

router = APIRouter(tags=["Devices"])


@router.post(
    "/devices/{device_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=OutDevice,
)
async def create_device_data(
    device_id: Annotated[uuid.UUID, Path(title="The ID of the device")],
    device: Annotated[CreateDevice, Body(title="The device data")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
) -> OutDevice:
    return await service.create_device_data(device_id, device, session)


@router.get(
    "/devices/{device_id}/analytics",
    status_code=status.HTTP_200_OK,
    response_model=DeviceAnalytics,
)
async def get_device_analytics(
    device_id: Annotated[uuid.UUID, Path(title="The ID of the device to retrieve")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
    date_from: Annotated[
        Optional[datetime.datetime], Query(title="Start date of the period")
    ] = None,
    date_to: Annotated[
        Optional[datetime.datetime], Query(title="End date of the period")
    ] = None,
) -> DeviceAnalytics:
    return await service.get_device_analytics(device_id, date_from, date_to, session)
