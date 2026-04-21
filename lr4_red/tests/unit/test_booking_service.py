"""Падающие тесты сервиса бронирования (Red Phase)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from src.schemas.booking import BookingCreate
from src.services.booking_service import BookingService
from src.services.pricing import PricingContext


class DummyBookingRepository:
    """Тестовая заглушка репозитория броней."""

    async def create(
        self,
        user_id: int,
        arena_id: int,
        start_time: datetime,
        end_time: datetime,
        total_cost: Decimal,
    ) -> object:
        return {
            "id": 10,
            "user_id": user_id,
            "arena_id": arena_id,
            "start_time": start_time,
            "end_time": end_time,
            "total_cost": total_cost,
            "is_paid": False,
        }

    async def get_by_id(self, booking_id: int) -> object | None:
        return {"id": booking_id, "is_paid": False}

    async def mark_paid(self, booking: object) -> object:
        return {"id": 10, "is_paid": True}

    async def list_by_user(self, user_id: int) -> list[object]:
        return []


class DummyArenaRepository:
    """Тестовая заглушка репозитория арен."""

    async def get_by_id(self, arena_id: int) -> object | None:
        return {"id": arena_id, "price_per_hour": Decimal("500.00")}


class DummyUserRepository:
    """Тестовая заглушка репозитория пользователей."""

    async def get_by_id(self, user_id: int) -> object | None:
        return {"id": user_id}


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

    assert booking.total_cost > Decimal("0")


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

    result = await service.pay_booking(booking_id=10)

    assert result.booking_id == 10
    assert result.paid is True

