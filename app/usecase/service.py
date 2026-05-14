# from fastapi import HTTPException, status
# import logging
# import uuid
# from app.core.config import settings
# from typing import List
# from app.storage.postgres.db_helper import db_helper
# from datetime import datetime, timedelta, timezone, date
# from app.api.schemas import (
#     JWT,
#     Auth,
#     CreateRoom,
#     OutRoom,
#     CreateSchedule,
#     OutSchedule,
#     CreateBooking,
#     OutBooking,
#     OutSlot,
# )
# from app.storage.repositories.repositories import SQLAlchemyAuthRepository
# from app.infrastructure.jwt_service import JWTService
# from app.mappers import room as map_room
# from app.mappers import schedule as map_schedule
# from app.mappers import slot as map_slot
# from app.mappers import booking as map_booking


# logger = logging.getLogger(__name__)


# class Service:
#     def __init__(self):
#         self.repo = SQLAlchemyAuthRepository()
#         self.jwt = JWTService()

#     # Token
#     def create_token(self, role: str) -> JWT:
#         user_id = settings.admin_id if role == "admin" else settings.user_id
#         encoded_jwt = self.jwt.create_token(user_id, role)
#         logger.info(f"Create {role}")
#         return JWT(jwt=encoded_jwt)

#     # Room
#     async def create_room(self, room: CreateRoom) -> OutRoom:
#         room_bd = map_room.to_bd(room)
#         async with db_helper.transaction() as session:
#             result = await self.repo.create_room(room_bd, session)
#         logger.info("Create room")
#         return map_room.to_out(result)

#     async def list_rooms(self, page: int, page_size: int) -> List[OutRoom]:
#         async with db_helper.transaction() as session:
#             total = await self.repo.get_rooms_count(session)
#             if total is None:
#                 return []
#             offset = (page - 1) * page_size
#             result = await self.repo.list_rooms_paginated(offset, page_size, session)
#         return map_room.list_to_out(result)

#     # Schedule
#     async def create_schedule(
#         self, roomId: uuid.UUID, schedule: CreateSchedule
#     ) -> OutSchedule:
#         async with db_helper.transaction() as session:
#             room = await self.repo.get_room_by_id(roomId, session)
#             if room is None:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail="Room not found",
#                 )

#             existing_schedule = await self.repo.get_schedule_by_room_id(roomId, session)
#             if existing_schedule is not None:
#                 raise HTTPException(
#                     status_code=status.HTTP_409_CONFLICT,
#                     detail="Schedule already create",
#                 )

#             schedule_bd = map_schedule.to_bd(schedule, roomId)
#             result = await self.repo.create_schedule(schedule_bd, session)
#         logger.info("Create schedule")
#         return map_schedule.to_out(result)

#     # Slot
#     async def list_slots(self, roomId: uuid.UUID, date: date) -> List[OutSlot]:
#         async with db_helper.transaction() as session:
#             schedule = await self.repo.get_schedule_by_room_id(roomId, session)

#             if schedule is None or date.isoweekday() not in schedule.days_of_week:
#                 return []
#             elif date < datetime.now(timezone.utc).date():
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail="Slots is in the past",
#                 )

#             start_of_day = datetime.combine(
#                 date, schedule.start_time, tzinfo=timezone.utc
#             )
#             end_of_day = datetime.combine(date, schedule.end_time, tzinfo=timezone.utc)
#             check = await self.repo.exists_slots_in_range(
#                 roomId, start_of_day, end_of_day, session
#             )

#             if not check:
#                 list_slot = []
#                 current = start_of_day
#                 step = timedelta(minutes=30)
#                 while current + step <= end_of_day:
#                     list_slot.append(map_slot.to_bd(roomId, current, current + step))
#                     current += step

#                 result = await self.repo.create_slots(list_slot, session)
#             else:
#                 result = await self.repo.list_available_slots(
#                     roomId, start_of_day, end_of_day, session
#                 )
#         return map_slot.list_to_out(result)

#     # Booking
#     async def create_booking(self, user: Auth, booking: CreateBooking) -> OutBooking:
#         async with db_helper.transaction() as session:
#             slot = await self.repo.get_slot_by_id(booking.slotId, session)
#             if not slot:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail="Slot not found",
#                 )

#             if slot.end < datetime.now(timezone.utc):
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail="Slot is in the past",
#                 )

#             check_brooked = await self.repo.get_booking_by_slot_id(
#                 booking.slotId, session
#             )
#             if check_brooked is not None and check_brooked.status == "active":
#                 raise HTTPException(
#                     status_code=status.HTTP_409_CONFLICT,
#                     detail="Slot already booked",
#                 )

#             link = None
#             if booking.conferenceLink:
#                 link = "https://kload.ru/"
#             booking_bd = map_booking.to_bd(booking, user.uuid, link)

#             if check_brooked is not None and check_brooked.status == "cancel":
#                 check_brooked.status = "active"
#                 check_brooked.user_id = user.uuid
#                 check_brooked.conference_link = link
#                 result = await self.repo.create_booking(check_brooked, session)
#             else:
#                 result = await self.repo.create_booking(booking_bd, session)
#         logger.info(f"Create booking by {user.uuid}")
#         return map_booking.to_out(result)

#     async def list_bookings(self, page: int, page_size: int) -> List[OutBooking]:
#         async with db_helper.transaction() as session:
#             total = await self.repo.get_bookings_count(session)
#             if total is None:
#                 return []
#             offset = (page - 1) * page_size
#             result = await self.repo.list_bookings_paginated(offset, page_size, session)
#         return map_booking.list_to_out(result)

#     async def read_my_bookings(self, user: Auth) -> List[OutBooking]:
#         time_now = datetime.now(timezone.utc)
#         async with db_helper.transaction() as session:
#             result = await self.repo.list_user_bookings(time_now, user.uuid, session)
#         return map_booking.list_to_out(result)

#     async def cancel_booking(self, user: Auth, bookingId: uuid.UUID) -> None:
#         async with db_helper.transaction() as session:
#             booking_db = await self.repo.read_booking_by_id(bookingId, session)
#             if booking_db is None:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail="Booking not found",
#                 )
#             elif booking_db.user_id != user.uuid:
#                 raise HTTPException(
#                     status_code=status.HTTP_403_FORBIDDEN,
#                     detail="Not you booking",
#                 )

#             slot = await self.repo.get_slot_by_id(booking_db.slot_id, session)
#             if slot is None:
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="Not found slot",
#                 )
#             if slot.end < datetime.now(timezone.utc):
#                 raise HTTPException(
#                     status_code=status.HTTP_403_FORBIDDEN,
#                     detail="Booking is in the past",
#                 )

#             booking_db.status = "cancel"
#             await self.repo.update_booking(booking_db, session)
#         logger.info(f"Cancel booking by {user.uuid}")
#         return


# service = Service()
