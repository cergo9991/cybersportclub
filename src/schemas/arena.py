"""Схемы игрового места."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ArenaCreate(BaseModel):
    """Создание игрового места."""

    number: int = Field(gt=0)
    type: str = Field(min_length=2, max_length=64)
    price_per_hour: Decimal = Field(gt=0)


class ArenaRead(BaseModel):
    """Ответ по игровому месту."""

    id: int
    number: int
    type: str
    hall_name: str
    price_per_hour: Decimal

    model_config = ConfigDict(from_attributes=True)


class ArenaUpdate(BaseModel):
    """Редактирование игрового места."""

    number: int = Field(gt=0)
    type: str = Field(min_length=2, max_length=64)
    price_per_hour: Decimal = Field(gt=0)
