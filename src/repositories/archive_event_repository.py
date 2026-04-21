"""Репозиторий архива событий (D5)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ArchiveEvent


class ArchiveEventRepository:
    """Доступ к архиву событий и результатов."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        event_type: str,
        details: str,
        actor_user_id: int | None = None,
        tournament_id: int | None = None,
        application_id: int | None = None,
    ) -> ArchiveEvent:
        """Добавляет событие в архив."""
        item = ArchiveEvent(
            event_type=event_type,
            details=details,
            actor_user_id=actor_user_id,
            tournament_id=tournament_id,
            application_id=application_id,
        )
        self._session.add(item)
        await self._session.commit()
        await self._session.refresh(item)
        return item

    async def get_by_id(self, event_id: int) -> ArchiveEvent | None:
        """Возвращает событие архива по id."""
        return await self._session.get(ArchiveEvent, event_id)

    async def update(self, item: ArchiveEvent, event_type: str, details: str) -> ArchiveEvent:
        """Редактирует событие архива."""
        item.event_type = event_type
        item.details = details
        await self._session.commit()
        await self._session.refresh(item)
        return item

    async def list_recent(self, limit: int = 50) -> list[ArchiveEvent]:
        """Возвращает последние события архива."""
        result = await self._session.execute(
            select(ArchiveEvent).order_by(ArchiveEvent.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
