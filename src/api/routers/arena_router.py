"""Роутер игровых мест."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_arena_service
from src.schemas.arena import ArenaCreate, ArenaRead, ArenaUpdate
from src.services.arena_service import ArenaService

router = APIRouter(prefix="/arenas", tags=["arenas"])


@router.post("", response_model=ArenaRead, status_code=status.HTTP_201_CREATED)
async def create_arena(payload: ArenaCreate, service: ArenaService = Depends(get_arena_service)) -> ArenaRead:
    """Создание игрового места."""
    try:
        return await service.create_arena(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.get("", response_model=list[ArenaRead], status_code=status.HTTP_200_OK)
async def list_arenas(service: ArenaService = Depends(get_arena_service)) -> list[ArenaRead]:
    """Список игровых мест."""
    try:
        return await service.list_arenas()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.get("/free-count", response_model=int, status_code=status.HTTP_200_OK)
async def get_free_count(
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    service: ArenaService = Depends(get_arena_service),
) -> int:
    """Количество свободных ПК в заданном интервале."""
    try:
        return await service.count_free_arenas(start_time=start_time, end_time=end_time)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.put("/{arena_id}", response_model=ArenaRead, status_code=status.HTTP_200_OK)
async def update_arena(
    arena_id: int,
    payload: ArenaUpdate,
    service: ArenaService = Depends(get_arena_service),
) -> ArenaRead:
    """Обновление игрового места."""
    try:
        return await service.update_arena(arena_id=arena_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.delete("/{arena_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_arena(
    arena_id: int,
    service: ArenaService = Depends(get_arena_service),
) -> None:
    """Удаление игрового места."""
    try:
        await service.delete_arena(arena_id=arena_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc
