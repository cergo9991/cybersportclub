"""Общие фикстуры тестов ЛР5."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
import sys

from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.base import Base
from src.db.session import get_session
from src.main import app

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture
def booking_window() -> tuple[datetime, datetime]:
    """Временной интервал для тестов бронирования."""
    return datetime(2026, 4, 20, 14, 0, 0), datetime(2026, 4, 20, 16, 0, 0)


@pytest_asyncio.fixture
async def test_session_factory(tmp_path: Path) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Создает изолированную тестовую БД."""
    db_file = tmp_path / "test_esports.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield session_factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def api_client(test_session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncClient, None]:
    """httpx клиент с переопределенной зависимостью БД."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()
