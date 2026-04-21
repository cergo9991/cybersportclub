"""E2E тесты API киберспортивного клуба."""

from __future__ import annotations

from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_login_booking_payment_flow(api_client: AsyncClient) -> None:
    """Сквозной сценарий Login -> Booking -> Payment."""
    register_response = await api_client.post(
        "/auth/register",
        json={"username": "player1", "email": "player1@example.com", "password": "strongpass"},
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]

    login_response = await api_client.post(
        "/auth/login",
        json={"email": "player1@example.com", "password": "strongpass"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["access_token"] == f"user-{user_id}"

    arena_response = await api_client.post(
        "/arenas",
        json={"number": 1, "type": "VIP-PC", "price_per_hour": "500.00"},
    )
    assert arena_response.status_code == 201
    arena_id = arena_response.json()["id"]

    booking_response = await api_client.post(
        "/bookings",
        json={
            "user_id": user_id,
            "arena_id": arena_id,
            "start_time": "2026-04-20T14:00:00",
            "end_time": "2026-04-20T16:00:00",
            "is_tournament_participant": False,
        },
    )
    assert booking_response.status_code == 201
    booking_id = booking_response.json()["id"]
    assert booking_response.json()["total_cost"] == "1000.00"

    payment_response = await api_client.post(f"/bookings/{booking_id}/pay")
    assert payment_response.status_code == 200
    assert payment_response.json() == {"booking_id": booking_id, "paid": True}

    list_response = await api_client.get(f"/bookings/user/{user_id}")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["is_paid"] is True


@pytest.mark.asyncio
async def test_pay_unknown_booking_returns_404(api_client: AsyncClient) -> None:
    """Проверка статуса 404 для несуществующей брони."""
    response = await api_client.post("/bookings/999/pay")
    assert response.status_code == 404
