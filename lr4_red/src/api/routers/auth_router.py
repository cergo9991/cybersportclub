"""Роутер аутентификации."""

from fastapi import APIRouter, Depends, status

from src.api.deps import get_auth_service
from src.schemas.auth import LoginRequest, TokenResponse
from src.schemas.user import UserCreate, UserRead
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, service: AuthService = Depends(get_auth_service)) -> UserRead:
    """Регистрация пользователя."""
    return await service.register(payload)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_user(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    """Авторизация пользователя."""
    return await service.login(payload)

