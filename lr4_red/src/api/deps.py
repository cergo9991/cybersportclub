"""Зависимости API слоя."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.repositories.arena_repository import ArenaRepository
from src.repositories.booking_repository import BookingRepository
from src.repositories.user_repository import UserRepository
from src.services.arena_service import ArenaService
from src.services.auth_service import AuthService
from src.services.booking_service import BookingService
from src.services.pricing import PricingContext


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    """DI для сервиса авторизации."""
    return AuthService(user_repository=UserRepository(session))


def get_arena_service(session: AsyncSession = Depends(get_session)) -> ArenaService:
    """DI для сервиса игровых мест."""
    return ArenaService(arena_repository=ArenaRepository(session))


def get_booking_service(session: AsyncSession = Depends(get_session)) -> BookingService:
    """DI для сервиса бронирования."""
    return BookingService(
        booking_repository=BookingRepository(session),
        arena_repository=ArenaRepository(session),
        user_repository=UserRepository(session),
        pricing_context=PricingContext(),
    )

