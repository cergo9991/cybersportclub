"""Общие фикстуры тестов ЛР4."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture
def booking_window() -> tuple[datetime, datetime]:
    """Временной интервал для тестов бронирования."""
    return datetime(2026, 4, 20, 14, 0, 0), datetime(2026, 4, 20, 16, 0, 0)

