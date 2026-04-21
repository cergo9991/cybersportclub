"""Web-интерфейс: отдельные страницы игрока и администратора."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.api.deps import get_arena_service, get_auth_service, get_booking_service, get_tournament_service
from src.schemas.arena import ArenaCreate, ArenaUpdate
from src.schemas.auth import LoginRequest
from src.schemas.booking import BookingCreate
from src.schemas.tournament import TournamentCreate
from src.schemas.user import UserCreate, UserRead
from src.services.arena_service import ArenaService
from src.services.auth_service import AuthService
from src.services.booking_service import BookingService
from src.services.tournament_service import TournamentService

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


def _set_flash(request: Request, message: str, level: str = "info") -> None:
    request.session["flash"] = {"message": message, "level": level}


def _pop_flash(request: Request) -> dict[str, str] | None:
    return request.session.pop("flash", None)


def _get_user_id(request: Request) -> int | None:
    value = request.session.get("user_id")
    return value if isinstance(value, int) else None


def _is_admin_session(request: Request) -> bool:
    value = request.session.get("is_admin")
    return bool(value)


def _redirect_by_role(request: Request) -> str:
    if _is_admin_session(request):
        return "/admin"
    if _get_user_id(request) is not None:
        return "/player"
    return "/"


def _booking_min_datetime() -> str:
    now = datetime.now().replace(second=0, microsecond=0)
    return now.isoformat(timespec="minutes")


async def _resolve_current_user(request: Request, auth_service: AuthService) -> UserRead | None:
    user_id = _get_user_id(request)
    if user_id is None:
        return None
    try:
        return await auth_service.get_user_by_id(user_id)
    except LookupError:
        request.session.clear()
        _set_flash(request, "Сессия устарела, войдите снова.", "warning")
        return None


async def _collect_public_context(
    arena_service: ArenaService,
    tournament_service: TournamentService,
) -> dict[str, Any]:
    arenas = await arena_service.list_arenas()
    tournaments = await tournament_service.list_tournaments()
    categories = await tournament_service.list_categories()
    teams = await tournament_service.list_teams()
    free_count = await arena_service.count_free_arenas()
    return {
        "arenas": arenas,
        "tournaments": tournaments,
        "categories": categories,
        "teams": teams,
        "free_count": free_count,
        "tournament_map": {item.id: item for item in tournaments},
        "arena_map": {item.id: item for item in arenas},
        "booking_min_datetime": _booking_min_datetime(),
    }


@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    arena_service: ArenaService = Depends(get_arena_service),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> HTMLResponse:
    """Лендинг с регистрацией и переходом в личные кабинеты."""
    user = await _resolve_current_user(request, auth_service)
    context = {
        "request": request,
        "flash": _pop_flash(request),
        "user": user.model_dump() if user is not None else None,
        "is_admin": _is_admin_session(request),
        "now": datetime.now(UTC),
        **(await _collect_public_context(arena_service, tournament_service)),
    }
    return templates.TemplateResponse(request=request, name="index.html", context=context)


@router.get("/player", response_class=HTMLResponse)
async def player_page(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    arena_service: ArenaService = Depends(get_arena_service),
    booking_service: BookingService = Depends(get_booking_service),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> HTMLResponse:
    """Страница игрока: брони, заявки и турниры."""
    user = await _resolve_current_user(request, auth_service)
    if user is None:
        _set_flash(request, "Для доступа к странице игрока выполните вход.", "warning")
        return _redirect("/")

    context = {
        "request": request,
        "flash": _pop_flash(request),
        "user": user.model_dump(),
        "is_admin": _is_admin_session(request),
        "bookings": await booking_service.list_user_bookings(user.id),
        "user_applications": await tournament_service.list_user_applications(user.id),
        "now": datetime.now(UTC),
        **(await _collect_public_context(arena_service, tournament_service)),
    }
    return templates.TemplateResponse(request=request, name="player.html", context=context)


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    arena_service: ArenaService = Depends(get_arena_service),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> HTMLResponse:
    """Страница администратора: D2-D5 по схеме."""
    user = await _resolve_current_user(request, auth_service)
    if user is None:
        _set_flash(request, "Для доступа к панели администратора выполните вход.", "warning")
        return _redirect("/")
    if not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для панели администратора.", "error")
        return _redirect("/player")

    public_context = await _collect_public_context(arena_service, tournament_service)
    tournaments = public_context["tournaments"]
    participants_by_tournament: dict[int, list[Any]] = {}
    for tournament in tournaments:
        applications = await tournament_service.list_tournament_applications(tournament.id)
        participants_by_tournament[tournament.id] = [item for item in applications if item.status != "rejected"]

    context = {
        "request": request,
        "flash": _pop_flash(request),
        "user": user.model_dump(),
        "is_admin": True,
        "users": await auth_service.list_users(),
        "pending_applications": await tournament_service.list_pending_applications(),
        "hall_assignments": await tournament_service.list_hall_assignments(),
        "archive_events": await tournament_service.list_archive_events(limit=30),
        "tournament_archive": await tournament_service.list_tournament_archive(),
        "participants_by_tournament": participants_by_tournament,
        "now": datetime.now(UTC),
        **public_context,
    }
    return templates.TemplateResponse(request=request, name="admin.html", context=context)


@router.post("/web/register")
async def web_register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    """Регистрация игрока."""
    try:
        await auth_service.register(UserCreate(username=username, email=email, password=password))
        _set_flash(request, "Игрок успешно зарегистрирован.", "success")
    except ValueError as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/")


@router.post("/web/login")
async def web_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    """Вход игрока или администратора."""
    try:
        token = await auth_service.login(LoginRequest(email=email, password=password))
        user_id = int(token.access_token.removeprefix("user-"))
        user = await auth_service.get_user_by_id(user_id)
    except (ValueError, LookupError) as exc:
        _set_flash(request, str(exc), "error")
        return _redirect("/")

    is_admin = auth_service.is_admin_email(user.email)
    request.session["user_id"] = user.id
    request.session["is_admin"] = is_admin
    request.session["username"] = user.username
    request.session["email"] = user.email
    _set_flash(request, f"Вход выполнен: {user.username}.", "success")
    return _redirect("/admin" if is_admin else "/player")


@router.post("/web/logout")
async def web_logout(request: Request) -> RedirectResponse:
    """Выход из системы."""
    request.session.clear()
    _set_flash(request, "Вы вышли из аккаунта.", "info")
    return _redirect("/")


@router.post("/web/bookings")
async def web_create_booking(
    request: Request,
    arena_id: int = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    is_tournament_participant: bool = Form(False),
    booking_service: BookingService = Depends(get_booking_service),
) -> RedirectResponse:
    """Бронирование ПК игроком."""
    user_id = _get_user_id(request)
    if user_id is None:
        _set_flash(request, "Для бронирования требуется вход.", "warning")
        return _redirect("/")
    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        now_local = datetime.now().replace(second=0, microsecond=0)
        if start_dt < now_local:
            raise ValueError("Нельзя бронировать прошедшие даты и время.")

        payload = BookingCreate(
            user_id=user_id,
            arena_id=arena_id,
            start_time=start_dt,
            end_time=end_dt,
            is_tournament_participant=is_tournament_participant,
        )
        booking = await booking_service.create_booking(payload)
        _set_flash(request, f"Бронь #{booking.id} создана.", "success")
    except (ValueError, LookupError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/player")


@router.post("/web/bookings/{booking_id}/pay")
async def web_pay_booking(
    request: Request,
    booking_id: int,
    booking_service: BookingService = Depends(get_booking_service),
) -> RedirectResponse:
    """Оплата брони из web-интерфейса."""
    if _get_user_id(request) is None:
        _set_flash(request, "Для оплаты брони требуется вход.", "warning")
        return _redirect("/")
    try:
        await booking_service.pay_booking(booking_id=booking_id)
        _set_flash(request, "Бронь оплачена.", "success")
    except (ValueError, LookupError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/player")


@router.post("/web/player/applications")
async def web_submit_application(
    request: Request,
    tournament_id: int = Form(...),
    team_name: str = Form(""),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> RedirectResponse:
    """D4: игрок подает заявку на участие в турнире."""
    user_id = _get_user_id(request)
    if user_id is None:
        _set_flash(request, "Для подачи заявки требуется вход.", "warning")
        return _redirect("/")
    try:
        await tournament_service.submit_application(
            user_id=user_id,
            tournament_id=tournament_id,
            team_name=team_name,
        )
        _set_flash(request, "Заявка отправлена администратору.", "success")
    except (ValueError, LookupError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/player")


@router.post("/web/tournaments/{tournament_id}/register")
async def web_register_tournament(
    request: Request,
    tournament_id: int,
    team_name: str = Form(""),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> RedirectResponse:
    """Совместимость со старым роутом регистрации на турнир."""
    return await web_submit_application(
        request=request,
        tournament_id=tournament_id,
        team_name=team_name,
        tournament_service=tournament_service,
    )


@router.post("/web/admin/tournaments")
async def web_create_tournament(
    request: Request,
    name: str = Form(...),
    game_type: str = Form(...),
    category_name: str = Form(...),
    tournament_type: str = Form(...),
    entry_fee: str = Form("0"),
    prize_pool: str = Form("0"),
    start_datetime: str = Form(""),
    start_date: str = Form(""),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> RedirectResponse:
    """D2: администратор создает турнир."""
    user_id = _get_user_id(request)
    if user_id is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для создания турнира.", "error")
        return _redirect(_redirect_by_role(request))

    try:
        start_dt = datetime.fromisoformat(start_datetime) if start_datetime else None
        start_day = date.fromisoformat(start_date) if start_date else (start_dt.date() if start_dt else None)
        payload = TournamentCreate(
            name=name,
            game_type=game_type,
            category_name=category_name,
            tournament_type=tournament_type,
            entry_fee=Decimal(entry_fee),
            prize_pool=Decimal(prize_pool),
            start_date=start_day,
            start_datetime=start_dt,
        )
        await tournament_service.create_tournament(payload=payload, admin_user_id=user_id)
        _set_flash(request, "Турнир создан.", "success")
    except (ValueError, LookupError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")


@router.post("/web/admin/tournaments/{tournament_id}/delete")
async def web_delete_tournament(
    request: Request,
    tournament_id: int,
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> RedirectResponse:
    """Админ удаляет турнир."""
    admin_id = _get_user_id(request)
    if admin_id is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для удаления турнира.", "error")
        return _redirect(_redirect_by_role(request))
    try:
        await tournament_service.delete_tournament(tournament_id=tournament_id, admin_user_id=admin_id)
        _set_flash(request, "Турнир удален.", "success")
    except LookupError as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")


@router.post("/web/admin/tournaments/{tournament_id}/close")
async def web_close_tournament(
    request: Request,
    tournament_id: int,
    result_text: str = Form(...),
    winner_user_ids: list[int] = Form([]),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> RedirectResponse:
    """Админ закрывает турнир и распределяет выплаты победителям."""
    admin_id = _get_user_id(request)
    if admin_id is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для закрытия турнира.", "error")
        return _redirect(_redirect_by_role(request))
    try:
        result = await tournament_service.close_tournament(
            tournament_id=tournament_id,
            winner_user_ids=winner_user_ids,
            result_text=result_text,
            admin_user_id=admin_id,
        )
        _set_flash(
            request,
            f"Турнир закрыт. Участников: {result.participant_count}. Выплата каждому победителю: {result.payout_per_winner}.",
            "success",
        )
    except (LookupError, ValueError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")


@router.post("/web/admin/arenas")
async def web_create_arena(
    request: Request,
    number: int = Form(...),
    arena_type: str = Form(...),
    price_per_hour: str = Form(...),
    arena_service: ArenaService = Depends(get_arena_service),
) -> RedirectResponse:
    """Админ добавляет новый ПК."""
    if _get_user_id(request) is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для добавления ПК.", "error")
        return _redirect(_redirect_by_role(request))
    try:
        await arena_service.create_arena(
            ArenaCreate(number=number, type=arena_type, price_per_hour=Decimal(price_per_hour))
        )
        _set_flash(request, "Игровое место добавлено.", "success")
    except ValueError as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")


@router.post("/web/admin/arenas/{arena_id}/update")
async def web_update_arena(
    request: Request,
    arena_id: int,
    number: int = Form(...),
    arena_type: str = Form(...),
    price_per_hour: str = Form(...),
    arena_service: ArenaService = Depends(get_arena_service),
) -> RedirectResponse:
    """Админ редактирует ПК."""
    if _get_user_id(request) is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для изменения ПК.", "error")
        return _redirect(_redirect_by_role(request))
    try:
        await arena_service.update_arena(
            arena_id=arena_id,
            payload=ArenaUpdate(number=number, type=arena_type, price_per_hour=Decimal(price_per_hour)),
        )
        _set_flash(request, "Игровое место обновлено.", "success")
    except (ValueError, LookupError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")


@router.post("/web/admin/arenas/{arena_id}/delete")
async def web_delete_arena(
    request: Request,
    arena_id: int,
    arena_service: ArenaService = Depends(get_arena_service),
) -> RedirectResponse:
    """Админ удаляет ПК."""
    if _get_user_id(request) is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для удаления ПК.", "error")
        return _redirect(_redirect_by_role(request))
    try:
        await arena_service.delete_arena(arena_id=arena_id)
        _set_flash(request, "Игровое место удалено.", "success")
    except (ValueError, LookupError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")


@router.post("/web/admin/users/{target_user_id}/balance")
async def web_update_balance(
    request: Request,
    target_user_id: int,
    new_balance: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    """Админ редактирует баланс пользователя."""
    admin_id = _get_user_id(request)
    if admin_id is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для изменения баланса.", "error")
        return _redirect(_redirect_by_role(request))
    try:
        await auth_service.update_balance(
            user_id=target_user_id,
            new_balance=Decimal(new_balance),
            admin_user_id=admin_id,
        )
        _set_flash(request, "Баланс пользователя обновлен.", "success")
    except (ValueError, LookupError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")


@router.post("/web/admin/assignments")
async def web_assign_hall(
    request: Request,
    tournament_id: int = Form(...),
    arena_id: int = Form(...),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> RedirectResponse:
    """D3: администратор назначает компьютерный зал турниру."""
    user_id = _get_user_id(request)
    if user_id is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для распределения залов.", "error")
        return _redirect(_redirect_by_role(request))
    try:
        await tournament_service.assign_hall(
            tournament_id=tournament_id,
            arena_id=arena_id,
            admin_user_id=user_id,
        )
        _set_flash(request, "Зал назначен турниру.", "success")
    except (ValueError, LookupError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")


@router.post("/web/admin/applications/{application_id}/review")
async def web_review_application(
    request: Request,
    application_id: int,
    action: str = Form(...),
    assigned_arena_id: str | None = Form(None),
    admin_comment: str | None = Form(None),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> RedirectResponse:
    """D4: администратор одобряет или отклоняет заявку."""
    user_id = _get_user_id(request)
    if user_id is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для обработки заявок.", "error")
        return _redirect(_redirect_by_role(request))

    approve = action == "approve"
    assigned_arena_id_int = int(assigned_arena_id) if assigned_arena_id else None
    try:
        await tournament_service.review_application(
            application_id=application_id,
            admin_user_id=user_id,
            approve=approve,
            assigned_arena_id=assigned_arena_id_int if approve else None,
            admin_comment=admin_comment,
        )
        _set_flash(request, "Заявка обработана.", "success")
    except (ValueError, LookupError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")


@router.post("/web/admin/archive-result")
async def web_add_result(
    request: Request,
    tournament_id: int = Form(...),
    result_text: str = Form(...),
    winner_team_id: str | None = Form(None),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> RedirectResponse:
    """D5: администратор добавляет событие/результат в архив."""
    user_id = _get_user_id(request)
    if user_id is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для ведения архива.", "error")
        return _redirect(_redirect_by_role(request))
    try:
        winner_team_id_int = int(winner_team_id) if winner_team_id else None
        await tournament_service.add_result_to_archive(
            tournament_id=tournament_id,
            result_text=result_text,
            admin_user_id=user_id,
            winner_team_id=winner_team_id_int,
        )
        _set_flash(request, "Событие добавлено в архив.", "success")
    except (LookupError, ValueError) as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")


@router.post("/web/admin/archive-events/{event_id}/edit")
async def web_edit_archive_event(
    request: Request,
    event_id: int,
    event_type: str = Form(...),
    details: str = Form(...),
    tournament_service: TournamentService = Depends(get_tournament_service),
) -> RedirectResponse:
    """Админ редактирует запись архива."""
    user_id = _get_user_id(request)
    if user_id is None or not _is_admin_session(request):
        _set_flash(request, "Недостаточно прав для редактирования архива.", "error")
        return _redirect(_redirect_by_role(request))
    try:
        await tournament_service.edit_archive_event(
            event_id=event_id,
            event_type=event_type,
            details=details,
            admin_user_id=user_id,
        )
        _set_flash(request, "Событие архива обновлено.", "success")
    except LookupError as exc:
        _set_flash(request, str(exc), "error")
    return _redirect("/admin")
