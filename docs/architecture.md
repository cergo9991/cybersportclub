# Архитектура ЛР5 (по DFD)

Проект реализует слоистую архитектуру:

- `src/api`: программный интерфейс (REST).
- `src/web`: пользовательский интерфейс (HTML/Jinja2).
- `src/services`: бизнес-логика процессов 1-5.
- `src/repositories`: доступ к данным (SQLAlchemy AsyncIO).
- `src/db`: ORM-модели и сессия.
- `src/schemas`: Pydantic DTO.

DFD-хранилища:

- D1 `users`
- D2 `tournaments`, `game_categories`
- D3 `arenas`, `tournament_hall_assignments`
- D4 `tournament_applications`
- D5 `archive_events`, `tournament_archives`

Ключевой принцип: UI и API не работают с БД напрямую, только через сервисы и репозитории.
