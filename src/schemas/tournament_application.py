"""Схемы заявок на участие в турнирах (D4)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TournamentApplicationCreate(BaseModel):
    """Запрос на подачу заявки в турнир."""

    user_id: int
    tournament_id: int
    team_name: str | None = None


class TournamentApplicationRead(BaseModel):
    """Ответ по заявке на участие."""

    id: int
    user_id: int
    user_name: str
    tournament_id: int
    team_id: int | None = None
    team_name: str | None = None
    status: str
    assigned_arena_id: int | None = None
    processed_by_admin_id: int | None = None
    admin_comment: str | None = None
    entry_fee_charged: Decimal = Decimal("0.00")
    created_at: datetime
    processed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
