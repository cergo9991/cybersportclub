"""Зависимости API слоя."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.repositories.archive_event_repository import ArchiveEventRepository
from src.repositories.arena_repository import ArenaRepository
from src.repositories.booking_repository import BookingRepository
from src.repositories.game_category_repository import GameCategoryRepository
from src.repositories.team_repository import TeamRepository
from src.repositories.tournament_application_repository import TournamentApplicationRepository
from src.repositories.tournament_archive_repository import TournamentArchiveRepository
from src.repositories.tournament_hall_assignment_repository import TournamentHallAssignmentRepository
from src.repositories.tournament_repository import TournamentRepository
from src.repositories.user_repository import UserRepository
from src.services.arena_service import ArenaService
from src.services.auth_service import AuthService
from src.services.booking_service import BookingService
from src.services.pricing import PricingContext
from src.services.tournament_service import TournamentService


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    """DI для сервиса авторизации."""
    return AuthService(
        user_repository=UserRepository(session),
        archive_event_repository=ArchiveEventRepository(session),
    )


def get_arena_service(session: AsyncSession = Depends(get_session)) -> ArenaService:
    """DI для сервиса игровых мест."""
    return ArenaService(
        arena_repository=ArenaRepository(session),
        booking_repository=BookingRepository(session),
    )


def get_booking_service(session: AsyncSession = Depends(get_session)) -> BookingService:
    """DI для сервиса бронирования."""
    return BookingService(
        booking_repository=BookingRepository(session),
        arena_repository=ArenaRepository(session),
        user_repository=UserRepository(session),
        pricing_context=PricingContext(),
    )


def get_tournament_service(session: AsyncSession = Depends(get_session)) -> TournamentService:
    """DI для сервиса турниров."""
    return TournamentService(
        tournament_repository=TournamentRepository(session),
        tournament_application_repository=TournamentApplicationRepository(session),
        tournament_hall_assignment_repository=TournamentHallAssignmentRepository(session),
        game_category_repository=GameCategoryRepository(session),
        user_repository=UserRepository(session),
        arena_repository=ArenaRepository(session),
        archive_event_repository=ArchiveEventRepository(session),
        tournament_archive_repository=TournamentArchiveRepository(session),
        team_repository=TeamRepository(session),
    )
