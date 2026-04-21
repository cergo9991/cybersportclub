"""Схемы регистрации на турнир."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TournamentRegistrationRead(BaseModel):
    """Ответ по регистрации пользователя на турнир."""

    id: int
    user_id: int
    tournament_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

