"""Схемы архива событий (D5)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArchiveEventUpdate(BaseModel):
    """Запрос на изменение архивного события."""

    event_type: str
    details: str


class ArchiveEventRead(BaseModel):
    """Ответ по событию архива."""

    id: int
    event_type: str
    details: str
    actor_user_id: int | None = None
    tournament_id: int | None = None
    application_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
