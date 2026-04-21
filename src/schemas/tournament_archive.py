"""Схемы архива турниров и результатов."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TournamentArchiveRead(BaseModel):
    """Ответ по архивной записи турнира."""

    id: int
    tournament_id: int
    result_summary: str
    winner_name: str | None = None
    archived_at: datetime

    model_config = ConfigDict(from_attributes=True)

