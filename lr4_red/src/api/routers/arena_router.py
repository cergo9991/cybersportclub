"""Роутер игровых мест."""

from fastapi import APIRouter, Depends, status

from src.api.deps import get_arena_service
from src.schemas.arena import ArenaCreate, ArenaRead
from src.services.arena_service import ArenaService

router = APIRouter(prefix="/arenas", tags=["arenas"])


@router.post("", response_model=ArenaRead, status_code=status.HTTP_201_CREATED)
async def create_arena(payload: ArenaCreate, service: ArenaService = Depends(get_arena_service)) -> ArenaRead:
    """Создание игрового места."""
    return await service.create_arena(payload)


@router.get("", response_model=list[ArenaRead], status_code=status.HTTP_200_OK)
async def list_arenas(service: ArenaService = Depends(get_arena_service)) -> list[ArenaRead]:
    """Список игровых мест."""
    return await service.list_arenas()

