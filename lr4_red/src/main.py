"""Точка входа FastAPI приложения (ЛР4)."""

from fastapi import FastAPI

from src.api.routers.arena_router import router as arena_router
from src.api.routers.auth_router import router as auth_router
from src.api.routers.booking_router import router as booking_router
from src.api.routers.tournament_router import router as tournament_router
from src.db.base import Base
from src.db.session import engine

app = FastAPI(title="CyberSport Club API - LR4")
app.include_router(auth_router)
app.include_router(arena_router)
app.include_router(booking_router)
app.include_router(tournament_router)


@app.on_event("startup")
async def on_startup() -> None:
    """Создает таблицы для локальной разработки."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

