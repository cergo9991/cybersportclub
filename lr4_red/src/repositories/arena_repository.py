"""Репозиторий игровых мест."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Arena


class ArenaRepository:
    """Доступ к данным игровых мест."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, number: int, arena_type: str, price_per_hour: float) -> Arena:
        """Создает игровое место."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

    async def get_by_id(self, arena_id: int) -> Arena | None:
        """Возвращает игровое место по id."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

    async def list_all(self) -> list[Arena]:
        """Возвращает список игровых мест."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

