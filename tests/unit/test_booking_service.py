"""Тесты сервиса бронирования (Green Phase)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import pytest

from src.schemas.booking import BookingCreate
from src.services.booking_service import BookingService
from src.services.pricing import PricingContext


class DummyBookingRepository:
    """Тестовая заглушка репозитория броней."""

    def __init__(self) -> None:
        self._items: dict[int, FakeBooking] = {}
        self._last_id = 0

    async def create(
        self,
        user_id: int,
        arena_id: int,
        start_time: datetime,
        end_time: datetime,
        total_cost: Decimal,
    ) -> "FakeBooking":
        self._last_id += 1
        booking = FakeBooking(
            id=self._last_id,
            user_id=user_id,
            arena_id=arena_id,
            start_time=start_time,
            end_time=end_time,
            total_cost=total_cost,
            is_paid=False,
        )
        self._items[booking.id] = booking
        return booking

    async def get_by_id(self, booking_id: int) -> "FakeBooking | None":
        return self._items.get(booking_id)

    async def mark_paid(self, booking: "FakeBooking") -> "FakeBooking":
        booking.is_paid = True
        self._items[booking.id] = booking
        return booking

    async def list_by_user(self, user_id: int) -> list["FakeBooking"]:
        return [item for item in self._items.values() if item.user_id == user_id]

    async def has_overlap(self, arena_id: int, start_time: datetime, end_time: datetime) -> bool:
        return False


class DummyArenaRepository:
    """Тестовая заглушка репозитория арен."""

    async def get_by_id(self, arena_id: int) -> "FakeArena | None":
        if arena_id != 2:
            return None
        return FakeArena(id=arena_id, price_per_hour=Decimal("500.00"))


class DummyUserRepository:
    """Тестовая заглушка репозитория пользователей."""

    async def get_by_id(self, user_id: int) -> "FakeUser | None":
        if user_id != 1:
            return None
        return FakeUser(id=user_id)


@dataclass
class FakeUser:
    """Минимальная модель пользователя."""

    id: int


@dataclass
class FakeArena:
    """Минимальная модель арены."""

    id: int
    price_per_hour: Decimal


@dataclass
class FakeBooking:
    """Минимальная модель брони."""

    id: int
    user_id: int
    arena_id: int
    start_time: datetime
    end_time: datetime
    total_cost: Decimal
    is_paid: bool


@pytest.mark.asyncio
async def test_create_booking_calculates_positive_total_cost(booking_window: tuple[datetime, datetime]) -> None:
    """Ожидаем создание брони с положительной стоимостью."""
    start_time, end_time = booking_window
    service = BookingService(
        booking_repository=DummyBookingRepository(),  # type: ignore[arg-type]
        arena_repository=DummyArenaRepository(),  # type: ignore[arg-type]
        user_repository=DummyUserRepository(),  # type: ignore[arg-type]
        pricing_context=PricingContext(),
    )
    payload = BookingCreate(user_id=1, arena_id=2, start_time=start_time, end_time=end_time)

    booking = await service.create_booking(payload)

    assert booking.total_cost == Decimal("1000.00")


@pytest.mark.asyncio
async def test_create_booking_rejects_invalid_interval() -> None:
    """Ожидаем ошибку для интервала end_time <= start_time."""
    service = BookingService(
        booking_repository=DummyBookingRepository(),  # type: ignore[arg-type]
        arena_repository=DummyArenaRepository(),  # type: ignore[arg-type]
        user_repository=DummyUserRepository(),  # type: ignore[arg-type]
        pricing_context=PricingContext(),
    )
    payload = BookingCreate(
        user_id=1,
        arena_id=2,
        start_time=datetime(2026, 4, 20, 15, 0, 0),
        end_time=datetime(2026, 4, 20, 15, 0, 0),
    )

    with pytest.raises(ValueError):
        await service.create_booking(payload)


@pytest.mark.asyncio
async def test_pay_booking_marks_booking_as_paid() -> None:
    """Ожидаем смену флага оплаты на True."""
    service = BookingService(
        booking_repository=DummyBookingRepository(),  # type: ignore[arg-type]
        arena_repository=DummyArenaRepository(),  # type: ignore[arg-type]
        user_repository=DummyUserRepository(),  # type: ignore[arg-type]
        pricing_context=PricingContext(),
    )

    created = await service.create_booking(
        BookingCreate(
            user_id=1,
            arena_id=2,
            start_time=datetime(2026, 4, 20, 11, 0, 0),
            end_time=datetime(2026, 4, 20, 12, 0, 0),
        )
    )
    result = await service.pay_booking(booking_id=created.id)

    assert result.booking_id == created.id
    assert result.paid is True


@pytest.mark.asyncio
async def test_tournament_booking_is_free() -> None:
    """Ожидаем нулевую стоимость для участника турнира."""
    service = BookingService(
        booking_repository=DummyBookingRepository(),  # type: ignore[arg-type]
        arena_repository=DummyArenaRepository(),  # type: ignore[arg-type]
        user_repository=DummyUserRepository(),  # type: ignore[arg-type]
        pricing_context=PricingContext(),
    )
    booking = await service.create_booking(
        BookingCreate(
            user_id=1,
            arena_id=2,
            start_time=datetime(2026, 4, 20, 14, 0, 0),
            end_time=datetime(2026, 4, 20, 17, 0, 0),
            is_tournament_participant=True,
        )
    )
    assert booking.total_cost == Decimal("0.00")


@pytest.mark.asyncio
async def test_create_booking_returns_not_found_when_user_missing() -> None:
    """Ожидаем LookupError при отсутствии пользователя."""
    service = BookingService(
        booking_repository=DummyBookingRepository(),  # type: ignore[arg-type]
        arena_repository=DummyArenaRepository(),  # type: ignore[arg-type]
        user_repository=DummyUserRepository(),  # type: ignore[arg-type]
        pricing_context=PricingContext(),
    )

    with pytest.raises(LookupError):
        await service.create_booking(
            BookingCreate(
                user_id=99,
                arena_id=2,
                start_time=datetime(2026, 4, 20, 14, 0, 0),
                end_time=datetime(2026, 4, 20, 15, 0, 0),
            )
        )
