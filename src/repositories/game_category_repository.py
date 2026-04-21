"""Репозиторий категорий игр."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import GameCategory


class GameCategoryRepository:
    """Доступ к категориям киберспортивных дисциплин."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_name(self, name: str) -> GameCategory | None:
        """Возвращает категорию по имени."""
        result = await self._session.execute(select(GameCategory).where(GameCategory.name == name))
        return result.scalar_one_or_none()

    async def create(self, name: str, description: str | None = None) -> GameCategory:
        """Создает новую категорию."""
        category = GameCategory(name=name, description=description)
        self._session.add(category)
        await self._session.flush()
        return category

    async def get_or_create(self, name: str) -> GameCategory:
        """Возвращает категорию или создает новую."""
        found = await self.get_by_name(name)
        if found is not None:
            return found
        return await self.create(name=name)

    async def list_all(self) -> list[GameCategory]:
        """Возвращает список категорий."""
        result = await self._session.execute(select(GameCategory).order_by(GameCategory.name.asc()))
        return list(result.scalars().all())

