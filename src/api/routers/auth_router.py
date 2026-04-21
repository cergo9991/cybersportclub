"""Роутер аутентификации."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_auth_service
from src.schemas.auth import LoginRequest, TokenResponse
from src.schemas.user import UserCreate, UserRead
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, service: AuthService = Depends(get_auth_service)) -> UserRead:
    """Регистрация пользователя."""
    try:
        return await service.register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_user(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    """Авторизация пользователя."""
    try:
        return await service.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc
