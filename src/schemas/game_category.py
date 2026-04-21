"""Схемы категорий игр."""

from pydantic import BaseModel, ConfigDict


class GameCategoryRead(BaseModel):
    """Ответ по категории игры."""

    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)

