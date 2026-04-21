"""Репозиторий пользователей."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User


class UserRepository:
    """Доступ к данным пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, username: str, email: str, password_hash: str) -> User:
        """Создает пользователя."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

    async def get_by_email(self, email: str) -> User | None:
        """Возвращает пользователя по email."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

    async def get_by_id(self, user_id: int) -> User | None:
        """Возвращает пользователя по id."""
        raise NotImplementedError("ЛР4: реализация в ЛР5.")

