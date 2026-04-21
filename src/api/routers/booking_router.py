"""Роутер бронирования."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_booking_service
from src.schemas.booking import BookingCreate, BookingPaymentResponse, BookingRead
from src.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(payload: BookingCreate, service: BookingService = Depends(get_booking_service)) -> BookingRead:
    """Создание брони."""
    try:
        return await service.create_booking(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.post("/{booking_id}/pay", response_model=BookingPaymentResponse, status_code=status.HTTP_200_OK)
async def pay_booking(booking_id: int, service: BookingService = Depends(get_booking_service)) -> BookingPaymentResponse:
    """Оплата брони."""
    try:
        return await service.pay_booking(booking_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.get("/user/{user_id}", response_model=list[BookingRead], status_code=status.HTTP_200_OK)
async def list_user_bookings(user_id: int, service: BookingService = Depends(get_booking_service)) -> list[BookingRead]:
    """Список броней пользователя."""
    try:
        return await service.list_user_bookings(user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc
