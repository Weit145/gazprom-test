
# class SQLAlchemyAuthRepository:
#     async def create_room(self, room: Room, session: AsyncSession) -> Room:
#         session.add(room)
#         await session.flush()
#         await session.refresh(room)
#         return room

#     async def get_rooms_count(self, session: AsyncSession) -> int | None:
#         stmt = select(func.count()).select_from(Room)
#         result = await session.execute(stmt)
#         return result.scalar()

#     async def list_rooms_paginated(
#         self, offset: int, page_size: int, session: AsyncSession
#     ) -> List[Room]:
#         stmt = (
#             select(Room)
#             .offset(offset)
#             .limit(page_size)
#             .order_by(Room.created_at.desc())
#         )
#         result = await session.execute(stmt)
#         return list(result.scalars().all())

#     async def get_room_by_id(
#         self, roomId: uuid.UUID, session: AsyncSession
#     ) -> Room | None:
#         return await session.get(Room, roomId)

#     async def get_schedule_by_room_id(
#         self, roomId: uuid.UUID, session: AsyncSession
#     ) -> Schedule | None:
#         stmt = select(Schedule).where(Schedule.room_id == roomId)
#         result = await session.execute(stmt)
#         return result.scalar_one_or_none()

#     async def create_schedule(
#         self, schedule: Schedule, session: AsyncSession
#     ) -> Schedule:
#         session.add(schedule)
#         await session.flush()
#         await session.refresh(schedule)
#         return schedule

#     async def exists_slots_in_range(
#         self,
#         roomId: uuid.UUID,
#         start_of_day: datetime,
#         end_of_day: datetime,
#         session: AsyncSession,
#     ) -> bool | None:
#         stmt = select(
#             exists().where(
#                 Slot.room_id == roomId,
#                 Slot.start >= start_of_day,
#                 Slot.start < end_of_day,
#             )
#         )
#         result = await session.execute(stmt)
#         return result.scalar()

#     async def list_available_slots(
#         self,
#         roomId: uuid.UUID,
#         start_of_day: datetime,
#         end_of_day: datetime,
#         session: AsyncSession,
#     ) -> List[Slot]:
#         stmt = (
#             select(Slot)
#             .where(
#                 Slot.room_id == roomId,
#                 Slot.start >= start_of_day,
#                 Slot.start < end_of_day,
#                 ~Slot.booking.has(Booking.status == "active"),
#             )
#             .order_by(Slot.start)
#         )
#         result = await session.execute(stmt)
#         return list(result.scalars().all())

#     async def create_slots(
#         self, slots: List[Slot], session: AsyncSession
#     ) -> List[Slot]:
#         session.add_all(slots)
#         await session.flush()
#         return slots

#     async def get_slot_by_id(self, id: uuid.UUID, session: AsyncSession) -> Slot | None:
#         stmt = select(Slot).where(Slot.id == id).with_for_update()
#         result = await session.execute(stmt)
#         return result.scalar_one_or_none()

#     async def get_booking_by_slot_id(
#         self, slot_id: uuid.UUID, session: AsyncSession
#     ) -> Booking | None:
#         stmt = select(Booking).where(Booking.slot_id == slot_id).with_for_update()
#         result = await session.execute(stmt)
#         return result.scalar_one_or_none()

#     async def create_booking(self, booking: Booking, session: AsyncSession) -> Booking:
#         session.add(booking)
#         await session.flush()
#         await session.refresh(booking)
#         return booking

#     async def get_bookings_count(self, session: AsyncSession) -> int | None:
#         stmt = select(func.count()).select_from(Booking)
#         result = await session.execute(stmt)
#         return result.scalar()

#     async def list_bookings_paginated(
#         self, offset: int, page_size: int, session: AsyncSession
#     ) -> List[Booking]:
#         stmt = (
#             select(Booking)
#             .offset(offset)
#             .limit(page_size)
#             .order_by(Booking.created_at.desc())
#         )
#         result = await session.execute(stmt)
#         return list(result.scalars().all())

#     async def list_user_bookings(
#         self, time_now: datetime, user_id: uuid.UUID, session: AsyncSession
#     ) -> List[Booking]:
#         stmt = (
#             select(Booking)
#             .join(Slot, Booking.slot_id == Slot.id)
#             .where(
#                 Booking.user_id == user_id,
#                 Booking.status == "active",
#                 Slot.start >= time_now,
#             )
#             .order_by(Slot.start)
#         )
#         result = await session.execute(stmt)
#         return list(result.scalars().all())

#     async def read_booking_by_id(
#         self, bookingId: uuid.UUID, session: AsyncSession
#     ) -> Booking | None:
#         return await session.get(Booking, bookingId)

#     async def update_booking(self, booking: Booking, session: AsyncSession) -> Booking:
#         session.add(booking)
#         await session.flush()
#         await session.refresh(booking)
#         return booking
