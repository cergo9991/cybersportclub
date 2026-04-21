"""Сервис игровых мест."""

from datetime import UTC, datetime, timedelta

from src.repositories.arena_repository import ArenaRepository
from src.repositories.booking_repository import BookingRepository
from src.schemas.arena import ArenaCreate, ArenaRead, ArenaUpdate


class ArenaService:
    """Бизнес-логика управления игровыми местами."""

    def __init__(self, arena_repository: ArenaRepository, booking_repository: BookingRepository | None = None) -> None:
        self._arena_repository = arena_repository
        self._booking_repository = booking_repository

    @staticmethod
    def _hall_for_arena(arena_type: str, number: int) -> str:
        """Определяет название зала/комнаты по типу ПК."""
        normalized = arena_type.strip().upper()
        if "STREAM" in normalized:
            return f"Stream Room {number}"
        if "STANDARD" in normalized:
            return "Standard Hall"
        if "VIP" in normalized:
            return "VIP Zone (Standard Hall)"
        if "PRO" in normalized:
            room_number = ((number - 1) // 5) + 1
            return f"Pro Room {room_number}"
        return "General Hall"

    async def create_arena(self, payload: ArenaCreate) -> ArenaRead:
        """Создает игровое место."""
        arenas = await self._arena_repository.list_all()
        if any(arena.number == payload.number for arena in arenas):
            raise ValueError("Игровое место с таким номером уже существует.")
        arena = await self._arena_repository.create(
            number=payload.number,
            arena_type=payload.type,
            hall_name=self._hall_for_arena(payload.type, payload.number),
            price_per_hour=payload.price_per_hour,
        )
        return ArenaRead.model_validate(arena)

    async def update_arena(self, arena_id: int, payload: ArenaUpdate) -> ArenaRead:
        """Обновляет параметры игрового места."""
        arena = await self._arena_repository.get_by_id(arena_id)
        if arena is None:
            raise LookupError("Игровое место не найдено.")

        arenas = await self._arena_repository.list_all()
        if any(item.number == payload.number and item.id != arena_id for item in arenas):
            raise ValueError("Игровое место с таким номером уже существует.")

        updated = await self._arena_repository.update(
            arena=arena,
            number=payload.number,
            arena_type=payload.type,
            hall_name=self._hall_for_arena(payload.type, payload.number),
            price_per_hour=payload.price_per_hour,
        )
        return ArenaRead.model_validate(updated)

    async def delete_arena(self, arena_id: int) -> None:
        """Удаляет игровое место, если оно не используется."""
        arena = await self._arena_repository.get_by_id(arena_id)
        if arena is None:
            raise LookupError("Игровое место не найдено.")
        if await self._arena_repository.has_links(arena_id=arena_id):
            raise ValueError("Нельзя удалить ПК: он используется в бронях или турнирах.")
        await self._arena_repository.delete(arena)

    async def list_arenas(self) -> list[ArenaRead]:
        """Возвращает список игровых мест."""
        arenas = await self._arena_repository.list_all()
        return [ArenaRead.model_validate(arena) for arena in arenas]

    async def count_free_arenas(self, start_time: datetime | None = None, end_time: datetime | None = None) -> int:
        """Возвращает количество свободных ПК в заданном интервале."""
        if self._booking_repository is None:
            raise RuntimeError("BookingRepository не настроен в ArenaService.")

        interval_start = start_time or datetime.now(UTC).replace(tzinfo=None)
        interval_end = end_time or (interval_start + timedelta(hours=1))
        if interval_end <= interval_start:
            raise ValueError("Неверный временной интервал.")

        total = len(await self._arena_repository.list_all())
        busy = await self._booking_repository.count_busy_arenas(interval_start, interval_end)
        return max(total - busy, 0)
