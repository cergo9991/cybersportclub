"""Репозиторий архива турниров и результатов."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TournamentArchive


class TournamentArchiveRepository:
    """Доступ к архиву завершенных турниров."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, tournament_id: int, result_summary: str, winner_name: str | None = None) -> TournamentArchive:
        """Создает или обновляет архивную запись турнира."""
        result = await self._session.execute(
            select(TournamentArchive).where(TournamentArchive.tournament_id == tournament_id)
        )
        item = result.scalar_one_or_none()
        if item is None:
            item = TournamentArchive(
                tournament_id=tournament_id,
                result_summary=result_summary,
                winner_name=winner_name,
            )
            self._session.add(item)
        else:
            item.result_summary = result_summary
            item.winner_name = winner_name
            item.archived_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.commit()
        await self._session.refresh(item)
        return item

    async def list_all(self) -> list[TournamentArchive]:
        """Возвращает архив турниров и результатов."""
        result = await self._session.execute(
            select(TournamentArchive).order_by(TournamentArchive.archived_at.desc())
        )
        return list(result.scalars().all())

