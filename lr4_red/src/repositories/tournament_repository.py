"""Репозиторий турниров."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Tournament


class TournamentRepository:
    """Доступ к данным турниров."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, game_type: str, start_date: date) -> Tournament:
        """Создает турнир."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

