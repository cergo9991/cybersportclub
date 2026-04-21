"""Конфигурация приложения."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Параметры окружения."""

    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./esports_lab4.db")
    session_secret_key: str = os.getenv("SESSION_SECRET_KEY", "change-me-in-production")
    admin_emails_raw: str = os.getenv("ADMIN_EMAILS", "admin@cyberclub.com")

    @property
    def admin_emails(self) -> tuple[str, ...]:
        """Список email администраторов."""
        return tuple(item.strip().lower() for item in self.admin_emails_raw.split(",") if item.strip())


settings = Settings()
