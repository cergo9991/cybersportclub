"""Схемы матча."""

from pydantic import BaseModel, ConfigDict, Field


class MatchCreate(BaseModel):
    """Создание матча турнира."""

    tournament_id: int = Field(gt=0)
    team1_id: int = Field(gt=0)
    team2_id: int = Field(gt=0)
    score: str = Field(min_length=1, max_length=32)


class MatchRead(BaseModel):
    """Ответ по матчу."""

    id: int
    tournament_id: int
    team1_id: int
    team2_id: int
    score: str

    model_config = ConfigDict(from_attributes=True)

