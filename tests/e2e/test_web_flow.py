"""E2E тесты web-логики по схеме D1-D5."""

from __future__ import annotations

from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_web_dfd_flow_player_and_admin(api_client: AsyncClient) -> None:
    """Проверяет полный сценарий: игрок -> заявка -> админ -> архив."""
    arena_response = await api_client.post(
        "/arenas",
        json={"number": 7, "type": "ARENA-HALL", "price_per_hour": "400.00"},
    )
    assert arena_response.status_code == 201
    arena_id = arena_response.json()["id"]

    admin_register_response = await api_client.post(
        "/web/register",
        data={"username": "rootadmin", "email": "admin@cyberclub.com", "password": "admin123"},
    )
    assert admin_register_response.status_code == 303

    admin_login_response = await api_client.post(
        "/web/login",
        data={"email": "admin@cyberclub.com", "password": "admin123"},
    )
    assert admin_login_response.status_code == 303
    admin_page_response = await api_client.get("/admin")
    assert admin_page_response.status_code == 200

    create_tournament_response = await api_client.post(
        "/web/admin/tournaments",
        data={
            "name": "DFD Cup",
            "game_type": "CS2",
            "category_name": "FPS",
            "tournament_type": "official",
            "prize_pool": "25000.00",
            "start_date": "2026-08-01",
        },
    )
    assert create_tournament_response.status_code == 303

    tournaments_response = await api_client.get("/tournaments")
    tournament_id = tournaments_response.json()[0]["id"]

    assign_response = await api_client.post(
        "/web/admin/assignments",
        data={"tournament_id": str(tournament_id), "arena_id": str(arena_id)},
    )
    assert assign_response.status_code == 303

    admin_logout_response = await api_client.post("/web/logout")
    assert admin_logout_response.status_code == 303

    player_register_response = await api_client.post(
        "/web/register",
        data={"username": "player1", "email": "player1@example.com", "password": "strongpass"},
    )
    assert player_register_response.status_code == 303

    player_login_response = await api_client.post(
        "/web/login",
        data={"email": "player1@example.com", "password": "strongpass"},
    )
    assert player_login_response.status_code == 303
    player_page_response = await api_client.get("/player")
    assert player_page_response.status_code == 200

    submit_application_response = await api_client.post(
        "/web/player/applications",
        data={"tournament_id": str(tournament_id)},
    )
    assert submit_application_response.status_code == 303

    player_logout_response = await api_client.post("/web/logout")
    assert player_logout_response.status_code == 303

    admin_login_again_response = await api_client.post(
        "/web/login",
        data={"email": "admin@cyberclub.com", "password": "admin123"},
    )
    assert admin_login_again_response.status_code == 303

    pending_response = await api_client.get("/tournaments/applications/pending")
    assert pending_response.status_code == 200
    assert len(pending_response.json()) == 1
    application_id = pending_response.json()[0]["id"]

    review_response = await api_client.post(
        f"/web/admin/applications/{application_id}/review",
        data={"action": "approve", "assigned_arena_id": str(arena_id), "admin_comment": "approved"},
    )
    assert review_response.status_code == 303

    archive_add_response = await api_client.post(
        "/web/admin/archive-result",
        data={"tournament_id": str(tournament_id), "result_text": "Winner: Team Alpha"},
    )
    assert archive_add_response.status_code == 303

    archive_response = await api_client.get("/tournaments/archive/events")
    assert archive_response.status_code == 200
    assert len(archive_response.json()) >= 3


