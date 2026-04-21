"""Сервис аутентификации."""

from typing import Any

from src.core.security import hash_password, verify_password
from src.repositories.user_repository import UserRepository
from src.schemas.auth import LoginRequest, TokenResponse
from src.schemas.user import UserCreate, UserRead


class AuthService:
    """Бизнес-логика регистрации и входа."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    @staticmethod
    def _read(item: Any, field: str) -> Any:
        """Безопасно читает поле из ORM-объекта или dict."""
        if isinstance(item, dict):
            return item.get(field)
        return getattr(item, field, None)

    async def register(self, payload: UserCreate) -> UserRead:
        """Регистрирует нового пользователя."""
        create_fn = getattr(self._user_repository, "create", None)
        if create_fn is None:
            raise ValueError("Репозиторий пользователей не поддерживает create().")
        user = await create_fn(
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
        return UserRead.model_validate(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """Авторизует пользователя."""
        user = await self._user_repository.get_by_email(payload.email)
        if user is None:
            raise ValueError("Неверные учетные данные.")
        password_hash = self._read(user, "password_hash")
        if isinstance(password_hash, str) and password_hash.startswith("sha256$"):
            if not verify_password(payload.password, password_hash):
                raise ValueError("Неверные учетные данные.")
        user_id = self._read(user, "id")
        if not isinstance(user_id, int):
            raise ValueError("Некорректный пользователь в репозитории.")
        return TokenResponse(access_token=f"user-{user_id}")
