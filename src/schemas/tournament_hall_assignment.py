"""Схемы распределения залов (D3)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TournamentHallAssignmentRead(BaseModel):
    """Ответ по назначению компьютерного зала на турнир."""

    id: int
    tournament_id: int
    arena_id: int
    assigned_by_admin_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

