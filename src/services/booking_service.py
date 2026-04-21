"""Сервис бронирований."""

from decimal import Decimal

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
        if await self._booking_repository.has_overlap(
            arena_id=payload.arena_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
        ):
            raise ValueError("Игровое место уже занято в выбранный интервал.")

        strategy = self._pricing_context.get_strategy(
            start_time=payload.start_time,
            end_time=payload.end_time,
            is_tournament_participant=payload.is_tournament_participant,
        )
        total_cost = strategy.calculate(
            arena_price_per_hour=Decimal(str(arena.price_per_hour)),
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
        booking = await self._booking_repository.create(
            user_id=payload.user_id,
            arena_id=payload.arena_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            total_cost=total_cost,
        )
        return BookingRead.model_validate(booking)

    async def pay_booking(self, booking_id: int) -> BookingPaymentResponse:
        """Оплачивает бронь и списывает средства с баланса."""
        booking = await self._booking_repository.get_by_id(booking_id)
        if booking is None:
            raise LookupError("Бронь не найдена.")

        if booking.is_paid:
            return BookingPaymentResponse(booking_id=booking.id, paid=True)

        user = await self._user_repository.get_by_id(booking.user_id)
        if user is None:
            raise LookupError("Пользователь не найден.")

        amount = Decimal(str(booking.total_cost))
        user_balance = Decimal(str(getattr(user, "balance", Decimal("999999999.00"))))
        if user_balance < amount:
            raise ValueError("Недостаточно средств на балансе для оплаты брони.")

        if hasattr(self._user_repository, "subtract_balance") and hasattr(user, "balance"):
            await self._user_repository.subtract_balance(user=user, amount=amount)

        booking = await self._booking_repository.mark_paid(booking)
        return BookingPaymentResponse(booking_id=booking.id, paid=booking.is_paid)

    async def list_user_bookings(self, user_id: int) -> list[BookingRead]:
        """Возвращает список броней пользователя."""
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise LookupError("Пользователь не найден.")
        bookings = await self._booking_repository.list_by_user(user_id)
        return [BookingRead.model_validate(booking) for booking in bookings]
