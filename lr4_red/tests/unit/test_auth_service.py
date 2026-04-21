"""Падающие тесты сервиса аутентификации (Red Phase)."""

from __future__ import annotations

import pytest

from src.schemas.auth import LoginRequest
from src.schemas.user import UserCreate
from src.services.auth_service import AuthService


class DummyUserRepository:
    """Тестовая заглушка репозитория."""

    async def create(self, username: str, email: str, password_hash: str) -> object:
        return {"id": 1, "username": username, "email": email}

    async def get_by_email(self, email: str) -> object | None:
        if email == "exists@example.com":
            return {
                "id": 1,
                "username": "neo",
                "email": "exists@example.com",
                "password_hash": "$2b$12$fakehash",
            }
        return None


@pytest.mark.asyncio
async def test_register_returns_created_user() -> None:
    """Ожидаем корректный DTO после регистрации."""
    service = AuthService(user_repository=DummyUserRepository())  # type: ignore[arg-type]
    payload = UserCreate(username="neo", email="neo@example.com", password="strongpass")

    result = await service.register(payload)

    assert result.username == "neo"
    assert result.email == "neo@example.com"


@pytest.mark.asyncio
async def test_login_returns_token_for_valid_credentials() -> None:
    """Ожидаем токен для валидных данных."""
    service = AuthService(user_repository=DummyUserRepository())  # type: ignore[arg-type]
    payload = LoginRequest(email="exists@example.com", password="strongpass")

    token = await service.login(payload)

    assert token.access_token
    assert token.token_type == "bearer"

