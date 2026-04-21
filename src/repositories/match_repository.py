"""Репозиторий матчей."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Match


class MatchRepository:
    """Доступ к данным матчей."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, tournament_id: int, team1_id: int, team2_id: int, score: str) -> Match:
        """Создает матч."""
        match = Match(tournament_id=tournament_id, team1_id=team1_id, team2_id=team2_id, score=score)
        self._session.add(match)
        await self._session.commit()
        await self._session.refresh(match)
        return match
