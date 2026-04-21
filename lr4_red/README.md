# ЛР4 - CyberSport Club (Red Phase)

## Назначение

ЛР4 содержит архитектурный скелет проекта с разделением на слои и падающие unit-тесты по TDD.

## Стек

- Python 3.10+
- FastAPI
- SQLAlchemy AsyncIO
- Pydantic v2
- pytest + pytest-asyncio

## Установка

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Запуск API

```bash
uvicorn src.main:app --reload
```

## Запуск тестов (ожидаемо с ошибками)

```bash
pytest -q
```

Пример ожидаемого вывода:

```text
FAILED tests/unit/test_auth_service.py::test_register_returns_created_user - NotImplementedError
FAILED tests/unit/test_booking_service.py::test_create_booking_calculates_positive_total_cost - NotImplementedError
```

