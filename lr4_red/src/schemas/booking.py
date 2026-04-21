"""Схемы бронирования."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BookingCreate(BaseModel):
    """Создание брони."""

    user_id: int = Field(gt=0)
    arena_id: int = Field(gt=0)
    start_time: datetime
    end_time: datetime
    is_tournament_participant: bool = False


class BookingRead(BaseModel):
    """Ответ по брони."""

    id: int
    user_id: int
    arena_id: int
    start_time: datetime
    end_time: datetime
    total_cost: Decimal
    is_paid: bool

    model_config = ConfigDict(from_attributes=True)


class BookingPaymentResponse(BaseModel):
    """Ответ по оплате брони."""

    booking_id: int
    paid: bool

