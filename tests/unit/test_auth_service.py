"""Тесты сервиса аутентификации (Green Phase)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.core.security import hash_password
from src.schemas.auth import LoginRequest
from src.schemas.user import UserCreate
from src.services.auth_service import AuthService


@dataclass
class FakeUser:
    """Минимальная модель пользователя для unit-тестов."""

    id: int
    username: str
    email: str
    password_hash: str


class DummyUserRepository:
    """Тестовый репозиторий в памяти."""

    def __init__(self) -> None:
        self._items: list[FakeUser] = []
        self._last_id = 0

    async def create(self, username: str, email: str, password_hash: str) -> FakeUser:
        self._last_id += 1
        user = FakeUser(id=self._last_id, username=username, email=email, password_hash=password_hash)
        self._items.append(user)
        return user

    async def get_by_email(self, email: str) -> FakeUser | None:
        return next((item for item in self._items if item.email == email), None)

    async def get_by_username(self, username: str) -> FakeUser | None:
        return next((item for item in self._items if item.username == username), None)


@pytest.mark.asyncio
async def test_register_returns_created_user() -> None:
    """Проверка успешной регистрации."""
    repository = DummyUserRepository()
    service = AuthService(user_repository=repository)  # type: ignore[arg-type]
    payload = UserCreate(username="neo", email="neo@example.com", password="strongpass")

    result = await service.register(payload)

    assert result.username == "neo"
    assert result.email == "neo@example.com"


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email() -> None:
    """Проверка ошибки при дубликате email."""
    repository = DummyUserRepository()
    repository._items.append(FakeUser(id=1, username="alpha", email="dup@example.com", password_hash=hash_password("123456")))
    service = AuthService(user_repository=repository)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        await service.register(UserCreate(username="beta", email="dup@example.com", password="strongpass"))


@pytest.mark.asyncio
async def test_login_returns_token_for_valid_credentials() -> None:
    """Проверка входа с валидными данными."""
    repository = DummyUserRepository()
    repository._items.append(
        FakeUser(id=7, username="neo", email="exists@example.com", password_hash=hash_password("strongpass"))
    )
    service = AuthService(user_repository=repository)  # type: ignore[arg-type]
    payload = LoginRequest(email="exists@example.com", password="strongpass")

    token = await service.login(payload)

    assert token.access_token == "user-7"
    assert token.token_type == "bearer"


@pytest.mark.asyncio
async def test_login_rejects_invalid_password() -> None:
    """Проверка отклонения неверного пароля."""
    repository = DummyUserRepository()
    repository._items.append(FakeUser(id=1, username="neo", email="exists@example.com", password_hash=hash_password("good")))
    service = AuthService(user_repository=repository)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        await service.login(LoginRequest(email="exists@example.com", password="bad"))
