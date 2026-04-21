"""Репозиторий матчей."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Match


class MatchRepository:
    """Доступ к данным матчей."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, tournament_id: int, team1_id: int, team2_id: int, score: str) -> Match:
        """Создает матч."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

