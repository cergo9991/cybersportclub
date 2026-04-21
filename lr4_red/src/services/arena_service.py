"""Сервис игровых мест."""

from src.repositories.arena_repository import ArenaRepository
from src.schemas.arena import ArenaCreate, ArenaRead


class ArenaService:
    """Бизнес-логика управления игровыми местами."""

    def __init__(self, arena_repository: ArenaRepository) -> None:
        self._arena_repository = arena_repository

    async def create_arena(self, payload: ArenaCreate) -> ArenaRead:
        """Создает игровое место."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

    async def list_arenas(self) -> list[ArenaRead]:
        """Возвращает список игровых мест."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

