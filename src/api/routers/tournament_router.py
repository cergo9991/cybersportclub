"""Роутер турниров, заявок, распределения залов и архива."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_tournament_service
from src.schemas.archive_event import ArchiveEventRead, ArchiveEventUpdate
from src.schemas.game_category import GameCategoryRead
from src.schemas.team import TeamRead
from src.schemas.tournament import TournamentCloseResponse, TournamentCreate, TournamentRead
from src.schemas.tournament_application import TournamentApplicationCreate, TournamentApplicationRead
from src.schemas.tournament_archive import TournamentArchiveRead
from src.schemas.tournament_hall_assignment import TournamentHallAssignmentRead
from src.services.tournament_service import TournamentService

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.post("", response_model=TournamentRead, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    payload: TournamentCreate,
    service: TournamentService = Depends(get_tournament_service),
) -> TournamentRead:
    """Процесс 2: создание турнира."""
    try:
        return await service.create_tournament(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tournament(
    tournament_id: int,
    admin_user_id: int | None = None,
    service: TournamentService = Depends(get_tournament_service),
) -> None:
    """Удаление турнира."""
    try:
        await service.delete_tournament(tournament_id=tournament_id, admin_user_id=admin_user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.post("/{tournament_id}/close", response_model=TournamentCloseResponse, status_code=status.HTTP_200_OK)
async def close_tournament(
    tournament_id: int,
    winner_user_ids: list[int],
    result_text: str,
    admin_user_id: int,
    service: TournamentService = Depends(get_tournament_service),
) -> TournamentCloseResponse:
    """Закрытие турнира и выплата призового фонда победителям."""
    try:
        return await service.close_tournament(
            tournament_id=tournament_id,
            winner_user_ids=winner_user_ids,
            result_text=result_text,
            admin_user_id=admin_user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.get("", response_model=list[TournamentRead], status_code=status.HTTP_200_OK)
async def list_tournaments(service: TournamentService = Depends(get_tournament_service)) -> list[TournamentRead]:
    """Список турниров."""
    try:
        return await service.list_tournaments()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.get("/categories", response_model=list[GameCategoryRead], status_code=status.HTTP_200_OK)
async def list_categories(service: TournamentService = Depends(get_tournament_service)) -> list[GameCategoryRead]:
    """Справочник категорий киберспортивных дисциплин."""
    try:
        return await service.list_categories()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.get("/teams", response_model=list[TeamRead], status_code=status.HTTP_200_OK)
async def list_teams(service: TournamentService = Depends(get_tournament_service)) -> list[TeamRead]:
    """Справочник команд."""
    try:
        return await service.list_teams()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.post("/applications", response_model=TournamentApplicationRead, status_code=status.HTTP_201_CREATED)
async def submit_application_payload(
    payload: TournamentApplicationCreate,
    service: TournamentService = Depends(get_tournament_service),
) -> TournamentApplicationRead:
    """Процесс 4: подача заявки на участие."""
    try:
        return await service.submit_application(
            user_id=payload.user_id,
            tournament_id=payload.tournament_id,
            team_name=payload.team_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.post("/{tournament_id}/applications/{user_id}", response_model=TournamentApplicationRead, status_code=status.HTTP_201_CREATED)
async def submit_application(
    tournament_id: int,
    user_id: int,
    team_name: str | None = None,
    service: TournamentService = Depends(get_tournament_service),
) -> TournamentApplicationRead:
    """Процесс 4: подача заявки (legacy маршрут)."""
    try:
        return await service.submit_application(user_id=user_id, tournament_id=tournament_id, team_name=team_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.post("/{tournament_id}/register/{user_id}", response_model=TournamentApplicationRead, status_code=status.HTTP_201_CREATED)
async def register_user_for_tournament(
    tournament_id: int,
    user_id: int,
    team_name: str | None = None,
    service: TournamentService = Depends(get_tournament_service),
) -> TournamentApplicationRead:
    """Совместимость: старый route регистрации -> заявка."""
    return await submit_application(
        tournament_id=tournament_id,
        user_id=user_id,
        team_name=team_name,
        service=service,
    )


@router.post("/{tournament_id}/assign-hall/{arena_id}", response_model=TournamentHallAssignmentRead, status_code=status.HTTP_200_OK)
async def assign_hall(
    tournament_id: int,
    arena_id: int,
    admin_user_id: int,
    service: TournamentService = Depends(get_tournament_service),
) -> TournamentHallAssignmentRead:
    """Процесс 3: назначение компьютерного зала турниру."""
    try:
        return await service.assign_hall(tournament_id=tournament_id, arena_id=arena_id, admin_user_id=admin_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.get("/applications/pending", response_model=list[TournamentApplicationRead], status_code=status.HTTP_200_OK)
async def list_pending_applications(service: TournamentService = Depends(get_tournament_service)) -> list[TournamentApplicationRead]:
    """Процесс 4: список заявок на рассмотрении."""
    try:
        return await service.list_pending_applications()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.post("/applications/{application_id}/review", response_model=TournamentApplicationRead, status_code=status.HTTP_200_OK)
async def review_application(
    application_id: int,
    admin_user_id: int,
    approve: bool,
    assigned_arena_id: int | None = None,
    admin_comment: str | None = None,
    service: TournamentService = Depends(get_tournament_service),
) -> TournamentApplicationRead:
    """Процесс 4: обработка заявки администратором."""
    try:
        return await service.review_application(
            application_id=application_id,
            admin_user_id=admin_user_id,
            approve=approve,
            assigned_arena_id=assigned_arena_id,
            admin_comment=admin_comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.post("/{tournament_id}/archive-result", response_model=ArchiveEventRead, status_code=status.HTTP_201_CREATED)
async def add_result_to_archive(
    tournament_id: int,
    admin_user_id: int,
    result_text: str,
    winner_team_id: int | None = None,
    service: TournamentService = Depends(get_tournament_service),
) -> ArchiveEventRead:
    """Процесс 5: запись результата в архив."""
    try:
        return await service.add_result_to_archive(
            tournament_id=tournament_id,
            result_text=result_text,
            admin_user_id=admin_user_id,
            winner_team_id=winner_team_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.get("/archive/events", response_model=list[ArchiveEventRead], status_code=status.HTTP_200_OK)
async def list_archive_events(service: TournamentService = Depends(get_tournament_service)) -> list[ArchiveEventRead]:
    """Процесс 5: просмотр архива."""
    try:
        return await service.list_archive_events()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.put("/archive/events/{event_id}", response_model=ArchiveEventRead, status_code=status.HTTP_200_OK)
async def edit_archive_event(
    event_id: int,
    payload: ArchiveEventUpdate,
    admin_user_id: int,
    service: TournamentService = Depends(get_tournament_service),
) -> ArchiveEventRead:
    """Редактирование записи архива."""
    try:
        return await service.edit_archive_event(
            event_id=event_id,
            event_type=payload.event_type,
            details=payload.details,
            admin_user_id=admin_user_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc


@router.get("/archive/results", response_model=list[TournamentArchiveRead], status_code=status.HTTP_200_OK)
async def list_archive_results(service: TournamentService = Depends(get_tournament_service)) -> list[TournamentArchiveRead]:
    """Архив турниров и их результатов."""
    try:
        return await service.list_tournament_archive()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.") from exc
