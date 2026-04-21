"""Конфигурация приложения."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Параметры окружения."""

    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./esports_lab4.db")


settings = Settings()

