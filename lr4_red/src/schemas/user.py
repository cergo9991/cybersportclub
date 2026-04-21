"""Схемы пользователя."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Создание пользователя."""

    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserRead(BaseModel):
    """Ответ по пользователю."""

    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

