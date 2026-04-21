"""Схемы турнира."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TournamentCreate(BaseModel):
    """Создание турнира."""

    name: str = Field(min_length=3, max_length=128)
    game_type: str = Field(min_length=2, max_length=64)
    category_name: str = Field(default="General", min_length=2, max_length=64)
    tournament_type: Literal["amateur", "official"] = "amateur"
    entry_fee: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    prize_pool: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    start_date: date | None = None
    start_datetime: datetime | None = None

    @model_validator(mode="after")
    def validate_start_fields(self) -> "TournamentCreate":
        """Требует дату старта или дату-время старта."""
        if self.start_date is None and self.start_datetime is None:
            raise ValueError("Необходимо указать start_date или start_datetime.")
        return self


class TournamentRead(BaseModel):
    """Ответ по турниру."""

    id: int
    name: str
    game_type: str
    category_name: str
    tournament_type: str
    status: str
    entry_fee: Decimal
    prize_pool: Decimal
    has_prize: bool
    is_closed: bool
    start_date: date
    start_datetime: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TournamentCloseResponse(BaseModel):
    """Результат закрытия турнира."""

    tournament_id: int
    status: str
    participant_count: int
    winner_user_ids: list[int]
    payout_total: Decimal
    payout_per_winner: Decimal
