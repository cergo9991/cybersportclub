"""Репозиторий турниров."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import (
    ArchiveEvent,
    Match,
    Tournament,
    TournamentApplication,
    TournamentArchive,
    TournamentHallAssignment,
    TournamentRegistration,
)
from src.repositories.game_category_repository import GameCategoryRepository


class TournamentRepository:
    """Доступ к данным турниров."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._game_category_repository = GameCategoryRepository(session)

    async def create(
        self,
        name: str,
        game_type: str,
        category_name: str,
        tournament_type: str,
        entry_fee: Decimal,
        prize_pool: Decimal,
        start_date: date,
        start_datetime: datetime | None = None,
    ) -> Tournament:
        """Создает турнир."""
        category = await self._game_category_repository.get_or_create(category_name)
        tournament = Tournament(
            name=name,
            game_type=game_type,
            category_id=category.id,
            tournament_type=tournament_type,
            status="open",
            entry_fee=entry_fee,
            prize_pool=prize_pool,
            start_date=start_date,
            start_datetime=start_datetime,
        )
        self._session.add(tournament)
        await self._session.commit()
        created = await self.get_by_id(tournament.id)
        if created is None:
            raise RuntimeError("Не удалось загрузить созданный турнир.")
        return created

    async def list_all(self) -> list[Tournament]:
        """Возвращает список турниров."""
        order_field = func.coalesce(Tournament.start_datetime, Tournament.start_date)
        result = await self._session.execute(
            select(Tournament)
            .options(selectinload(Tournament.category))
            .order_by(order_field.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, tournament_id: int) -> Tournament | None:
        """Возвращает турнир по id."""
        result = await self._session.execute(
            select(Tournament)
            .options(selectinload(Tournament.category))
            .where(Tournament.id == tournament_id)
        )
        return result.scalar_one_or_none()

    async def close(self, tournament: Tournament) -> Tournament:
        """Закрывает турнир."""
        tournament.status = "closed"
        tournament.closed_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.commit()
        await self._session.refresh(tournament)
        return tournament

    async def delete_with_relations(self, tournament_id: int) -> bool:
        """Удаляет турнир вместе со связанными записями."""
        tournament = await self.get_by_id(tournament_id)
        if tournament is None:
            return False

        await self._session.execute(delete(ArchiveEvent).where(ArchiveEvent.tournament_id == tournament_id))
        await self._session.execute(delete(TournamentArchive).where(TournamentArchive.tournament_id == tournament_id))
        await self._session.execute(
            delete(TournamentHallAssignment).where(TournamentHallAssignment.tournament_id == tournament_id)
        )
        await self._session.execute(delete(TournamentApplication).where(TournamentApplication.tournament_id == tournament_id))
        await self._session.execute(delete(TournamentRegistration).where(TournamentRegistration.tournament_id == tournament_id))
        await self._session.execute(delete(Match).where(Match.tournament_id == tournament_id))
        await self._session.execute(delete(Tournament).where(Tournament.id == tournament_id))
        await self._session.commit()
        return True
