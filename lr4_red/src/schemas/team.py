"""Схемы команды."""

from pydantic import BaseModel, ConfigDict, Field


class TeamCreate(BaseModel):
    """Создание команды."""

    name: str = Field(min_length=2, max_length=64)
    captain_id: int = Field(gt=0)


class TeamRead(BaseModel):
    """Ответ по команде."""

    id: int
    name: str
    captain_id: int

    model_config = ConfigDict(from_attributes=True)

