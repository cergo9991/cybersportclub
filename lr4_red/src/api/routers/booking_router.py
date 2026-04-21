"""Роутер бронирования."""

from fastapi import APIRouter, Depends, status

from src.api.deps import get_booking_service
from src.schemas.booking import BookingCreate, BookingPaymentResponse, BookingRead
from src.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(payload: BookingCreate, service: BookingService = Depends(get_booking_service)) -> BookingRead:
    """Создание брони."""
    return await service.create_booking(payload)


@router.post("/{booking_id}/pay", response_model=BookingPaymentResponse, status_code=status.HTTP_200_OK)
async def pay_booking(booking_id: int, service: BookingService = Depends(get_booking_service)) -> BookingPaymentResponse:
    """Оплата брони."""
    return await service.pay_booking(booking_id)


@router.get("/user/{user_id}", response_model=list[BookingRead], status_code=status.HTTP_200_OK)
async def list_user_bookings(user_id: int, service: BookingService = Depends(get_booking_service)) -> list[BookingRead]:
    """Список броней пользователя."""
    return await service.list_user_bookings(user_id)

