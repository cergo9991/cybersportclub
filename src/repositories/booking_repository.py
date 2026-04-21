"""Репозиторий бронирований."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Booking


class BookingRepository:
    """Доступ к данным бронирований."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _overlap_stmt(start_time: datetime, end_time: datetime) -> Select[tuple[Booking]]:
        """Формирует запрос пересекающихся броней."""
        return select(Booking).where(Booking.start_time < end_time, Booking.end_time > start_time)

    async def create(
        self,
        user_id: int,
        arena_id: int,
        start_time: datetime,
        end_time: datetime,
        total_cost: Decimal,
    ) -> Booking:
        """Создает бронь."""
        booking = Booking(
            user_id=user_id,
            arena_id=arena_id,
            start_time=start_time,
            end_time=end_time,
            total_cost=total_cost,
            is_paid=False,
        )
        self._session.add(booking)
        await self._session.commit()
        await self._session.refresh(booking)
        return booking

    async def get_by_id(self, booking_id: int) -> Booking | None:
        """Возвращает бронь по id."""
        return await self._session.get(Booking, booking_id)

    async def list_by_user(self, user_id: int) -> list[Booking]:
        """Возвращает брони пользователя."""
        result = await self._session.execute(select(Booking).where(Booking.user_id == user_id).order_by(Booking.start_time))
        return list(result.scalars().all())

    async def mark_paid(self, booking: Booking) -> Booking:
        """Отмечает бронь оплаченной."""
        booking.is_paid = True
        await self._session.commit()
        await self._session.refresh(booking)
        return booking

    async def has_overlap(self, arena_id: int, start_time: datetime, end_time: datetime) -> bool:
        """Проверяет пересечение броней для конкретного ПК."""
        result = await self._session.execute(
            self._overlap_stmt(start_time, end_time).where(Booking.arena_id == arena_id)
        )
        return result.scalar_one_or_none() is not None

    async def count_busy_arenas(self, start_time: datetime, end_time: datetime) -> int:
        """Возвращает количество занятых ПК в интервале."""
        result = await self._session.execute(
            select(func.count(func.distinct(Booking.arena_id))).where(
                Booking.start_time < end_time,
                Booking.end_time > start_time,
            )
        )
        return int(result.scalar_one())
