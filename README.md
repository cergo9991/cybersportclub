# CyberSport Club — ЛР4 + ЛР5

Учебный сквозной проект по дисциплине **«Проектирование программных средств»**.

Репозиторий содержит два этапа:
- `lr4_red` — архитектурный скелет и тесты (TDD Red).
- корень репозитория — реализованное приложение ЛР5 (TDD Green): API + web + БД.

## Структура репозитория

```text
.
├─ lr4_red/                # ЛР4 (red phase)
│  ├─ src/
│  ├─ tests/
│  ├─ docs/
│  ├─ requirements.txt
│  └─ README.md
├─ src/                    # ЛР5 (green phase)
├─ tests/                  # Тесты ЛР5 (unit + e2e)
├─ docs/
├─ requirements.txt
├─ .gitignore
└─ README.md
```

## Технологический стек

- Python 3.10+
- FastAPI
- SQLAlchemy 2.x AsyncIO + SQLite (`aiosqlite`)
- Pydantic v2
- Jinja2 (web-шаблоны)
- Passlib (`bcrypt`) для хеширования паролей
- Pytest + Pytest-asyncio + HTTPX

## Функциональность ЛР5

- регистрация/вход пользователей;
- роли игрока и администратора;
- создание, удаление и закрытие турниров;
- заявки на участие + обработка заявок администратором;
- создание команд при подаче заявки;
- бронирование и оплата игровых ПК;
- учет баланса пользователя;
- распределение залов/ПК;
- архив событий и результатов турниров.

## Быстрый запуск (ЛР5)

```powershell
cd <папка_репозитория>
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload
```

Открыть:
- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

Демо-админ:
- `admin@cyberclub.com`
- `admin123`

## Тестирование

### ЛР5 (в корне)

```powershell
python -m pytest tests -q
```

Актуальный результат:
- `12 passed`

### ЛР4

```powershell
cd lr4_red
python -m pytest -q
```

Актуальный результат:
- `5 passed`

## Важно по БД

Приложение ЛР5 использует локальную SQLite БД и на startup выполняет совместимые миграции.  
Если требуется чистый запуск, удалите локальный файл БД (`*.db`) и запустите приложение снова.

## Материалы для отчётов

- ЛР4: архитектура и сценарии — `lr4_red/docs/architecture.md`, `lr4_red/tests/e2e/scenarios.md`
- ЛР5: архитектура и сценарии — `docs/architecture.md`, `tests/e2e/scenarios.md`
