"""Схемы аутентификации."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Запрос на вход."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    """Ответ с учебным токеном."""

    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)

