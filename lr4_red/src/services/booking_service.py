"""Сервис бронирований."""

from decimal import Decimal
from typing import Any

from src.repositories.arena_repository import ArenaRepository
from src.repositories.booking_repository import BookingRepository
from src.repositories.user_repository import UserRepository
from src.schemas.booking import BookingCreate, BookingPaymentResponse, BookingRead
from src.services.pricing import PricingContext


class BookingService:
    """Бизнес-логика бронирования и оплаты."""

    def __init__(
        self,
        booking_repository: BookingRepository,
        arena_repository: ArenaRepository,
        user_repository: UserRepository,
        pricing_context: PricingContext,
    ) -> None:
        self._booking_repository = booking_repository
        self._arena_repository = arena_repository
        self._user_repository = user_repository
        self._pricing_context = pricing_context

    @staticmethod
    def _read(item: Any, field: str) -> Any:
        """Безопасно читает поле из ORM-объекта или dict."""
        if isinstance(item, dict):
            return item.get(field)
        return getattr(item, field, None)

    async def create_booking(self, payload: BookingCreate) -> BookingRead:
        """Создает бронь для пользователя."""
        if payload.end_time <= payload.start_time:
            raise ValueError("Время окончания должно быть больше времени начала.")

        user = await self._user_repository.get_by_id(payload.user_id)
        if user is None:
            raise LookupError("Пользователь не найден.")

        arena = await self._arena_repository.get_by_id(payload.arena_id)
        if arena is None:
            raise LookupError("Игровое место не найдено.")

        arena_price = Decimal(str(self._read(arena, "price_per_hour")))
        strategy = self._pricing_context.get_strategy(
            start_time=payload.start_time,
            end_time=payload.end_time,
            is_tournament_participant=payload.is_tournament_participant,
        )
        total_cost = strategy.calculate(arena_price, payload.start_time, payload.end_time)
        booking = await self._booking_repository.create(
            user_id=payload.user_id,
            arena_id=payload.arena_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            total_cost=total_cost,
        )
        return BookingRead.model_validate(booking)

    async def pay_booking(self, booking_id: int) -> BookingPaymentResponse:
        """Оплачивает бронь."""
        booking = await self._booking_repository.get_by_id(booking_id)
        if booking is None:
            raise LookupError("Бронь не найдена.")

        is_paid = bool(self._read(booking, "is_paid"))
        if not is_paid:
            booking = await self._booking_repository.mark_paid(booking)

        booking_id_value = self._read(booking, "id")
        paid_value = bool(self._read(booking, "is_paid"))
        if not isinstance(booking_id_value, int):
            raise ValueError("Некорректная запись бронирования.")
        return BookingPaymentResponse(booking_id=booking_id_value, paid=paid_value)

    async def list_user_bookings(self, user_id: int) -> list[BookingRead]:
        """Возвращает список броней пользователя."""
        bookings = await self._booking_repository.list_by_user(user_id)
        return [BookingRead.model_validate(booking) for booking in bookings]
