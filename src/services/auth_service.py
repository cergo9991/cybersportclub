"""Сервис аутентификации."""

from decimal import Decimal

from src.core.config import settings
from src.core.security import hash_password, verify_password
from src.repositories.archive_event_repository import ArchiveEventRepository
from src.repositories.user_repository import UserRepository
from src.schemas.auth import LoginRequest, TokenResponse
from src.schemas.user import UserCreate, UserRead


class AuthService:
    """Бизнес-логика регистрации и входа."""

    def __init__(
        self,
        user_repository: UserRepository,
        archive_event_repository: ArchiveEventRepository | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._archive_event_repository = archive_event_repository

    async def register(self, payload: UserCreate) -> UserRead:
        """Регистрирует нового пользователя."""
        existing_by_email = await self._user_repository.get_by_email(payload.email)
        if existing_by_email is not None:
            raise ValueError("Пользователь с таким email уже существует.")
        existing_by_username = await self._user_repository.get_by_username(payload.username)
        if existing_by_username is not None:
            raise ValueError("Пользователь с таким username уже существует.")

        user = await self._user_repository.create(
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
        if self._archive_event_repository is not None:
            await self._archive_event_repository.create(
                event_type="PLAYER_REGISTERED",
                details=f"Игрок {payload.username} зарегистрирован в системе.",
                actor_user_id=user.id,
            )
        return UserRead.model_validate(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """Авторизует пользователя."""
        user = await self._user_repository.get_by_email(payload.email)
        if user is None:
            raise ValueError("Неверные учетные данные.")
        if not verify_password(payload.password, user.password_hash):
            raise ValueError("Неверные учетные данные.")
        return TokenResponse(access_token=f"user-{user.id}")

    async def get_user_by_id(self, user_id: int) -> UserRead:
        """Возвращает пользователя по id."""
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise LookupError("Пользователь не найден.")
        return UserRead.model_validate(user)

    async def list_users(self) -> list[UserRead]:
        """Возвращает всех пользователей."""
        users = await self._user_repository.list_all()
        return [UserRead.model_validate(item) for item in users]

    async def update_balance(self, user_id: int, new_balance: Decimal, admin_user_id: int | None = None) -> UserRead:
        """Обновляет баланс пользователя (админ-инструмент)."""
        if new_balance < Decimal("0.00"):
            raise ValueError("Баланс не может быть отрицательным.")
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise LookupError("Пользователь не найден.")
        updated = await self._user_repository.set_balance(user=user, amount=new_balance)
        if self._archive_event_repository is not None:
            await self._archive_event_repository.create(
                event_type="BALANCE_UPDATED",
                details=f"Баланс пользователя {updated.username} обновлен до {updated.balance}.",
                actor_user_id=admin_user_id,
            )
        return UserRead.model_validate(updated)

    def is_admin_email(self, email: str) -> bool:
        """Проверяет, является ли email администраторским."""
        return email.lower() in settings.admin_emails
