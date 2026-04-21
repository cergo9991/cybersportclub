"""Репозиторий команд."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Team


class TeamRepository:
    """Доступ к данным команд."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, captain_id: int) -> Team:
        """Создает команду."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

