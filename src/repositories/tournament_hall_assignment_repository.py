"""Репозиторий распределения залов (D3)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TournamentHallAssignment


class TournamentHallAssignmentRepository:
    """Доступ к назначениям компьютерных залов на турниры."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, tournament_id: int, arena_id: int, admin_id: int) -> TournamentHallAssignment:
        """Создает или обновляет назначение зала на турнир."""
        result = await self._session.execute(
            select(TournamentHallAssignment).where(TournamentHallAssignment.tournament_id == tournament_id)
        )
        assignment = result.scalar_one_or_none()
        if assignment is None:
            assignment = TournamentHallAssignment(tournament_id=tournament_id, arena_id=arena_id, assigned_by_admin_id=admin_id)
            self._session.add(assignment)
        else:
            assignment.arena_id = arena_id
            assignment.assigned_by_admin_id = admin_id
        await self._session.commit()
        await self._session.refresh(assignment)
        return assignment

    async def get_by_tournament_id(self, tournament_id: int) -> TournamentHallAssignment | None:
        """Возвращает назначение зала для турнира."""
        result = await self._session.execute(
            select(TournamentHallAssignment).where(TournamentHallAssignment.tournament_id == tournament_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[TournamentHallAssignment]:
        """Возвращает все назначения залов."""
        result = await self._session.execute(
            select(TournamentHallAssignment).order_by(TournamentHallAssignment.created_at.desc())
        )
        return list(result.scalars().all())

