"""Репозиторий бронирований."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Booking


class BookingRepository:
    """Доступ к данным бронирований."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: int,
        arena_id: int,
        start_time: datetime,
        end_time: datetime,
        total_cost: Decimal,
    ) -> Booking:
        """Создает бронь."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

    async def get_by_id(self, booking_id: int) -> Booking | None:
        """Возвращает бронь по id."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

    async def list_by_user(self, user_id: int) -> list[Booking]:
        """Возвращает брони пользователя."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

    async def mark_paid(self, booking: Booking) -> Booking:
        """Отмечает бронь оплаченной."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

