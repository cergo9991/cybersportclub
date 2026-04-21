"""Точка входа FastAPI приложения (ЛР5)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncConnection
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from src.api.routers.arena_router import router as arena_router
from src.api.routers.auth_router import router as auth_router
from src.api.routers.booking_router import router as booking_router
from src.api.routers.tournament_router import router as tournament_router
from src.core.config import settings
from src.core.security import hash_password
from src.db.base import Base
from src.db.models import Arena, GameCategory, Tournament, User
from src.db.session import SessionLocal, engine
from src.web.router import router as web_router

app = FastAPI(title="CyberSport Club API - LR5")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "web" / "static")),
    name="static",
)

app.include_router(auth_router)
app.include_router(arena_router)
app.include_router(booking_router)
app.include_router(tournament_router)
app.include_router(web_router)


async def _get_table_columns(conn: AsyncConnection, table_name: str) -> set[str]:
    """Возвращает список колонок таблицы SQLite."""
    result = await conn.exec_driver_sql(f"PRAGMA table_info({table_name})")
    return {str(row[1]) for row in result.all()}


async def _apply_sqlite_compat_migrations(conn: AsyncConnection) -> None:
    """Применяет легкие миграции для старой локальной SQLite базы."""
    if not settings.database_url.startswith("sqlite"):
        return

    tournament_columns = await _get_table_columns(conn, "tournaments")
    if "category_id" not in tournament_columns:
        await conn.exec_driver_sql("ALTER TABLE tournaments ADD COLUMN category_id INTEGER")
    if "tournament_type" not in tournament_columns:
        await conn.exec_driver_sql(
            "ALTER TABLE tournaments ADD COLUMN tournament_type VARCHAR(16) DEFAULT 'amateur'"
        )
    if "prize_pool" not in tournament_columns:
        await conn.exec_driver_sql(
            "ALTER TABLE tournaments ADD COLUMN prize_pool NUMERIC(12,2) DEFAULT 0"
        )
    if "entry_fee" not in tournament_columns:
        await conn.exec_driver_sql(
            "ALTER TABLE tournaments ADD COLUMN entry_fee NUMERIC(10,2) DEFAULT 0"
        )
    if "start_datetime" not in tournament_columns:
        await conn.exec_driver_sql("ALTER TABLE tournaments ADD COLUMN start_datetime DATETIME")
    if "status" not in tournament_columns:
        await conn.exec_driver_sql("ALTER TABLE tournaments ADD COLUMN status VARCHAR(16) DEFAULT 'open'")
    if "closed_at" not in tournament_columns:
        await conn.exec_driver_sql("ALTER TABLE tournaments ADD COLUMN closed_at DATETIME")

    arena_columns = await _get_table_columns(conn, "arenas")
    if "hall_name" not in arena_columns:
        await conn.exec_driver_sql("ALTER TABLE arenas ADD COLUMN hall_name VARCHAR(128) DEFAULT 'General Hall'")

    user_columns = await _get_table_columns(conn, "users")
    if "balance" not in user_columns:
        await conn.exec_driver_sql("ALTER TABLE users ADD COLUMN balance NUMERIC(12,2) DEFAULT 5000")

    application_columns = await _get_table_columns(conn, "tournament_applications")
    if application_columns:
        if "team_id" not in application_columns:
            await conn.exec_driver_sql("ALTER TABLE tournament_applications ADD COLUMN team_id INTEGER")
        if "entry_fee_charged" not in application_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE tournament_applications ADD COLUMN entry_fee_charged NUMERIC(10,2) DEFAULT 0"
            )

    await conn.exec_driver_sql(
        "INSERT OR IGNORE INTO game_categories (name, description) VALUES ('General', 'Базовая категория')"
    )
    general_category_result = await conn.exec_driver_sql(
        "SELECT id FROM game_categories WHERE name='General' LIMIT 1"
    )
    general_category_id = general_category_result.scalar_one_or_none()
    if general_category_id is not None:
        await conn.exec_driver_sql(
            "UPDATE tournaments SET category_id = ? WHERE category_id IS NULL",
            (int(general_category_id),),
        )
    await conn.exec_driver_sql(
        "UPDATE tournaments SET tournament_type='amateur' "
        "WHERE tournament_type IS NULL OR trim(tournament_type) = ''"
    )
    await conn.exec_driver_sql(
        "UPDATE tournaments SET status='open' "
        "WHERE status IS NULL OR trim(status) = ''"
    )
    await conn.exec_driver_sql("UPDATE tournaments SET entry_fee=0 WHERE entry_fee IS NULL")
    await conn.exec_driver_sql("UPDATE tournaments SET prize_pool=0 WHERE prize_pool IS NULL")
    await conn.exec_driver_sql(
        "UPDATE tournaments SET start_datetime = start_date || ' 10:00:00' "
        "WHERE start_datetime IS NULL AND start_date IS NOT NULL"
    )
    await conn.exec_driver_sql(
        "UPDATE arenas SET hall_name = CASE "
        "WHEN upper(type) LIKE '%STREAM%' THEN 'Stream Room ' || number "
        "WHEN upper(type) LIKE '%STANDARD%' THEN 'Standard Hall' "
        "WHEN upper(type) LIKE '%VIP%' THEN 'VIP Zone (Standard Hall)' "
        "WHEN upper(type) LIKE '%PRO%' THEN 'Pro Room ' || CAST(((number - 1) / 5) + 1 AS INT) "
        "ELSE 'General Hall' END "
        "WHERE hall_name IS NULL OR trim(hall_name) = ''"
    )
    await conn.exec_driver_sql("UPDATE users SET balance=5000 WHERE balance IS NULL")
    if application_columns:
        await conn.exec_driver_sql(
            "UPDATE tournament_applications SET entry_fee_charged=0 WHERE entry_fee_charged IS NULL"
        )


async def _seed_demo_data() -> None:
    """Заполняет БД демонстрационными данными при первом запуске."""
    async with SessionLocal() as session:
        arenas_count = await session.scalar(select(func.count(Arena.id)))
        if int(arenas_count or 0) == 0:
            session.add_all(
                [
                    Arena(number=1, type="VIP-PC", hall_name="VIP Zone (Standard Hall)", price_per_hour=Decimal("500.00")),
                    Arena(number=2, type="PRO-PC", hall_name="Pro Room 1", price_per_hour=Decimal("450.00")),
                    Arena(number=3, type="STREAM-PC", hall_name="Stream Room 3", price_per_hour=Decimal("550.00")),
                    Arena(number=4, type="STANDARD-PC", hall_name="Standard Hall", price_per_hour=Decimal("300.00")),
                ]
            )

        tournaments_count = await session.scalar(select(func.count(Tournament.id)))
        if int(tournaments_count or 0) == 0:
            category_cs = await session.scalar(select(GameCategory).where(GameCategory.name == "FPS"))
            if category_cs is None:
                category_cs = GameCategory(name="FPS", description="Шутеры от первого лица")
                session.add(category_cs)
                await session.flush()

            category_moba = await session.scalar(select(GameCategory).where(GameCategory.name == "MOBA"))
            if category_moba is None:
                category_moba = GameCategory(name="MOBA", description="Многопользовательские арены")
                session.add(category_moba)
                await session.flush()

            session.add_all(
                [
                    Tournament(
                        name="Spring Clash 2026",
                        game_type="CS2",
                        category_id=category_cs.id,
                        tournament_type="official",
                        status="open",
                        entry_fee=Decimal("1500.00"),
                        prize_pool=Decimal("30000.00"),
                        start_date=date(2026, 5, 5),
                        start_datetime=datetime(2026, 5, 5, 18, 0, 0),
                    ),
                    Tournament(
                        name="Moscow Rift Cup",
                        game_type="League of Legends",
                        category_id=category_moba.id,
                        tournament_type="amateur",
                        status="open",
                        entry_fee=Decimal("500.00"),
                        prize_pool=Decimal("0.00"),
                        start_date=date(2026, 5, 18),
                        start_datetime=datetime(2026, 5, 18, 19, 0, 0),
                    ),
                    Tournament(
                        name="Dota Arena Open",
                        game_type="Dota 2",
                        category_id=category_moba.id,
                        tournament_type="official",
                        status="open",
                        entry_fee=Decimal("2000.00"),
                        prize_pool=Decimal("50000.00"),
                        start_date=date(2026, 6, 2),
                        start_datetime=datetime(2026, 6, 2, 20, 0, 0),
                    ),
                ]
            )

        for admin_email in settings.admin_emails:
            existing_admin = await session.scalar(select(User.id).where(User.email == admin_email))
            if existing_admin is None:
                session.add(
                    User(
                        username=f"admin_{admin_email.split('@')[0]}",
                        email=admin_email,
                        password_hash=hash_password("admin123"),
                        balance=Decimal("100000.00"),
                    )
                )
        await session.commit()


@app.on_event("startup")
async def on_startup() -> None:
    """Создает таблицы и выполняет совместимые миграции для локальной разработки."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _apply_sqlite_compat_migrations(conn)
    await _seed_demo_data()
