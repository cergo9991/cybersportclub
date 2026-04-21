"""Репозиторий заявок на участие (D4)."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import TournamentApplication


class TournamentApplicationRepository:
    """Доступ к заявкам игроков на турниры."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: int,
        tournament_id: int,
        team_id: int | None = None,
        entry_fee_charged: Decimal = Decimal("0.00"),
    ) -> TournamentApplication:
        """Создает заявку со статусом pending."""
        application = TournamentApplication(
            user_id=user_id,
            tournament_id=tournament_id,
            team_id=team_id,
            status="pending",
            entry_fee_charged=entry_fee_charged,
        )
        self._session.add(application)
        await self._session.commit()
        await self._session.refresh(application)
        return application

    async def get_by_id(self, application_id: int) -> TournamentApplication | None:
        """Возвращает заявку по id."""
        result = await self._session.execute(
            select(TournamentApplication)
            .options(
                selectinload(TournamentApplication.user),
                selectinload(TournamentApplication.team),
                selectinload(TournamentApplication.tournament),
            )
            .where(TournamentApplication.id == application_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_tournament(self, user_id: int, tournament_id: int) -> TournamentApplication | None:
        """Ищет заявку пользователя на конкретный турнир."""
        result = await self._session.execute(
            select(TournamentApplication).where(
                TournamentApplication.user_id == user_id,
                TournamentApplication.tournament_id == tournament_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[TournamentApplication]:
        """Возвращает заявки конкретного пользователя."""
        result = await self._session.execute(
            select(TournamentApplication)
            .options(selectinload(TournamentApplication.user), selectinload(TournamentApplication.team))
            .where(TournamentApplication.user_id == user_id)
            .order_by(TournamentApplication.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_pending(self) -> list[TournamentApplication]:
        """Возвращает заявки со статусом pending."""
        result = await self._session.execute(
            select(TournamentApplication)
            .options(selectinload(TournamentApplication.user), selectinload(TournamentApplication.team))
            .where(TournamentApplication.status == "pending")
            .order_by(TournamentApplication.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_by_tournament(self, tournament_id: int) -> list[TournamentApplication]:
        """Возвращает заявки конкретного турнира."""
        result = await self._session.execute(
            select(TournamentApplication)
            .options(selectinload(TournamentApplication.user), selectinload(TournamentApplication.team))
            .where(TournamentApplication.tournament_id == tournament_id)
            .order_by(TournamentApplication.created_at.asc())
        )
        return list(result.scalars().all())

    async def review(
        self,
        application: TournamentApplication,
        approved: bool,
        admin_id: int,
        assigned_arena_id: int | None = None,
        admin_comment: str | None = None,
    ) -> TournamentApplication:
        """Подтверждает или отклоняет заявку администратором."""
        application.status = "approved" if approved else "rejected"
        application.processed_by_admin_id = admin_id
        application.processed_at = datetime.now(UTC).replace(tzinfo=None)
        application.assigned_arena_id = assigned_arena_id
        application.admin_comment = admin_comment
        await self._session.commit()
        await self._session.refresh(application)
        return application
