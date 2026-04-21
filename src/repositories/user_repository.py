"""Репозиторий пользователей."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User


class UserRepository:
    """Доступ к данным пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, username: str, email: str, password_hash: str) -> User:
        """Создает пользователя."""
        user = User(username=username, email=email, password_hash=password_hash)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Возвращает пользователя по email."""
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Возвращает пользователя по username."""
        result = await self._session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Возвращает пользователя по id."""
        return await self._session.get(User, user_id)

    async def list_all(self) -> list[User]:
        """Возвращает список пользователей."""
        result = await self._session.execute(select(User).order_by(User.username.asc()))
        return list(result.scalars().all())

    async def add_balance(self, user: User, amount: Decimal) -> User:
        """Увеличивает баланс пользователя."""
        user.balance = Decimal(str(user.balance)) + amount
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def subtract_balance(self, user: User, amount: Decimal) -> User:
        """Уменьшает баланс пользователя."""
        user.balance = Decimal(str(user.balance)) - amount
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def set_balance(self, user: User, amount: Decimal) -> User:
        """Устанавливает баланс пользователя."""
        user.balance = amount
        await self._session.commit()
        await self._session.refresh(user)
        return user
