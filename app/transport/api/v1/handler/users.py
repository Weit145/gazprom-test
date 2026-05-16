import uuid
import datetime
from fastapi import APIRouter, status, Body, Path, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional
from app.repositories.storage.postgres.db_helper import db_helper
from app.transport.api.v1.schemas.user import (
    CreateUser,
    OutUser,
    UserAnalytics,
    UserDevice,
)
from app.usecase.service import service

router = APIRouter(tags=["Users"])


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=OutUser)
async def create_user(
    user: Annotated[CreateUser, Body(title="The user data")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
) -> OutUser:
    return await service.create_user(user, session)


@router.post(
    "/users/{user_id}/devices/{device_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=UserDevice,
)
async def create_user_device(
    user_id: Annotated[uuid.UUID, Path(title="The ID of the user")],
    device_id: Annotated[uuid.UUID, Path(title="The ID of the device")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
) -> UserDevice:
    return await service.add_device_to_user(user_id, device_id, session)


@router.get(
    "/users/{user_id}/analytics",
    status_code=status.HTTP_200_OK,
    response_model=UserAnalytics,
)
async def get_user_analytics(
    user_id: Annotated[
        uuid.UUID, Path(title="The ID of the user to retrieve analytics")
    ],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
    date_from: Annotated[
        Optional[datetime.datetime], Query(title="Start date of the period")
    ] = None,
    date_to: Annotated[
        Optional[datetime.datetime], Query(title="End date of the period")
    ] = None,
) -> UserAnalytics:
    return await service.get_user_analytics(user_id, date_from, date_to, session)
