"""Репозиторий игровых мест."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Arena, Booking, TournamentApplication, TournamentHallAssignment


class ArenaRepository:
    """Доступ к данным игровых мест."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, number: int, arena_type: str, hall_name: str, price_per_hour: Decimal) -> Arena:
        """Создает игровое место."""
        arena = Arena(number=number, type=arena_type, hall_name=hall_name, price_per_hour=price_per_hour)
        self._session.add(arena)
        await self._session.commit()
        await self._session.refresh(arena)
        return arena

    async def get_by_id(self, arena_id: int) -> Arena | None:
        """Возвращает игровое место по id."""
        return await self._session.get(Arena, arena_id)

    async def list_all(self) -> list[Arena]:
        """Возвращает список игровых мест."""
        result = await self._session.execute(select(Arena).order_by(Arena.number.asc()))
        return list(result.scalars().all())

    async def update(
        self,
        arena: Arena,
        number: int,
        arena_type: str,
        hall_name: str,
        price_per_hour: Decimal,
    ) -> Arena:
        """Обновляет параметры игрового места."""
        arena.number = number
        arena.type = arena_type
        arena.hall_name = hall_name
        arena.price_per_hour = price_per_hour
        await self._session.commit()
        await self._session.refresh(arena)
        return arena

    async def has_links(self, arena_id: int) -> bool:
        """Проверяет использование ПК в бронях/назначениях."""
        booking_count = await self._session.scalar(select(func.count(Booking.id)).where(Booking.arena_id == arena_id))
        assignment_count = await self._session.scalar(
            select(func.count(TournamentHallAssignment.id)).where(TournamentHallAssignment.arena_id == arena_id)
        )
        application_count = await self._session.scalar(
            select(func.count(TournamentApplication.id)).where(TournamentApplication.assigned_arena_id == arena_id)
        )
        return int(booking_count or 0) > 0 or int(assignment_count or 0) > 0 or int(application_count or 0) > 0

    async def delete(self, arena: Arena) -> None:
        """Удаляет игровое место."""
        await self._session.delete(arena)
        await self._session.commit()
