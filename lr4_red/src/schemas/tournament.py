"""Схемы турнира."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class TournamentCreate(BaseModel):
    """Создание турнира."""

    name: str = Field(min_length=3, max_length=128)
    game_type: str = Field(min_length=2, max_length=64)
    start_date: date


class TournamentRead(BaseModel):
    """Ответ по турниру."""

    id: int
    name: str
    game_type: str
    start_date: date

    model_config = ConfigDict(from_attributes=True)

