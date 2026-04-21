# Киберспортивный клуб (ЛР4/ЛР5) — FastAPI + SQLAlchemy

Учебный сквозной проект по дисциплине **«Проектирование программных средств»**.

Система автоматизирует процессы киберспортивного клуба:
- регистрацию игроков;
- создание и сопровождение турниров;
- распределение игровых ПК/залов;
- подачу и обработку заявок на участие;
- ведение архива событий и итогов;
- бронирование игровых мест с учетом баланса.

Проект реализован по слоистой архитектуре и покрыт unit/e2e тестами.

---

## Содержание

1. [Функциональность](#функциональность)
2. [Бизнес-процессы по схеме D1–D5](#бизнес-процессы-по-схеме-d1d5)
3. [Архитектура и связи между файлами](#архитектура-и-связи-между-файлами)
4. [Структура репозитория](#структура-репозитория)
5. [Стек технологий](#стек-технологий)
6. [Запуск на новом ПК (с нуля)](#запуск-на-новом-пк-с-нуля)
7. [Как пользоваться системой](#как-пользоваться-системой)
8. [REST API (краткая карта)](#rest-api-краткая-карта)
9. [Тестирование](#тестирование)
10. [Подготовка к загрузке на GitHub](#подготовка-к-загрузке-на-github)
11. [Типовые проблемы и решения](#типовые-проблемы-и-решения)

---

## Функциональность

### Роль `Игрок`

- Регистрация и вход.
- Просмотр списка турниров и игровых мест.
- Просмотр количества свободных ПК.
- Подача заявки на турнир.
- Создание команды при подаче заявки (автоматически, если команды с таким именем нет).
- Бронирование ПК с выбором даты/времени (запрет на прошедшие даты).
- Оплата брони с баланса.
- Просмотр собственных заявок и броней.

### Роль `Администратор`

- Создание турниров с датой и временем старта.
- Удаление турниров.
- Закрытие турниров с выбором победителей.
- Автоматическое распределение призового фонда и взносов победителям.
- Обработка заявок игроков (`approve` / `reject`).
- Распределение игровых мест (залов) по турнирам.
- Добавление/редактирование/удаление ПК.
- Редактирование баланса пользователей.
- Добавление и редактирование событий архива.

---

## Бизнес-процессы по схеме D1–D5

### D1 — Регистрация игроков

- Таблица: `users`.
- Сервис: `src/services/auth_service.py`.
- Пароли в БД хранятся в виде хеша (`passlib[bcrypt]`), а не в открытом виде.

### D2 — Создание турниров

- Таблицы: `tournaments`, `game_categories`.
- Сервис: `src/services/tournament_service.py`.
- Поддерживаются типы турниров (`amateur`, `official`), взнос, призовой фонд, статус (`open`, `closed`), `start_datetime`.

### D3 — Распределение компьютерных залов

- Таблицы: `arenas`, `tournament_hall_assignments`.
- Сервис: `src/services/arena_service.py` + `src/services/tournament_service.py`.
- Автоматическое назначение `hall_name` по типу ПК:
  - `STREAM` → `Stream Room N`;
  - `STANDARD` → `Standard Hall`;
  - `VIP` → `VIP Zone (Standard Hall)`;
  - `PRO` → `Pro Room X` (по 5 ПК на комнату).

### D4 — Подача и отслеживание заявок

- Таблица: `tournament_applications`.
- Сервис: `src/services/tournament_service.py`.
- На подаче заявки может списываться `entry_fee`.
- При отклонении заявки взнос возвращается на баланс игрока.
- В заявках отображается имя игрока и команда.

### D5 — Архив событий и результатов

- Таблицы: `archive_events`, `tournament_archives`.
- Сервис: `src/services/tournament_service.py`.
- Все ключевые операции пишутся в архив (создание турнира, обработка заявок, закрытие турнира, изменения и т.д.).
- Архив можно редактировать из админ-панели.

---

## Архитектура и связи между файлами

Проект построен по принципу:

`Web/API -> Services -> Repositories -> DB`

Пользовательский интерфейс и REST API **не обращаются к БД напрямую**.

### 1) Точка входа

- `src/main.py`
- Инициализирует `FastAPI`, middleware сессий и статические файлы.
- Регистрирует web и API роутеры.
- На старте:
  - создает таблицы;
  - выполняет совместимые SQLite-миграции для старых локальных БД;
  - добавляет демо-данные (категории, турниры, админ).

### 2) Слой конфигурации и безопасности

- `src/core/config.py` — переменные окружения (`DATABASE_URL`, `SESSION_SECRET_KEY`, `ADMIN_EMAILS`).
- `src/core/security.py` — хеширование и проверка паролей.

### 3) Слой БД (ORM)

- `src/db/models.py` — модели предметной области (`User`, `Arena`, `Tournament`, `TournamentApplication`, `ArchiveEvent` и др.).
- `src/db/session.py` — `async`-движок SQLAlchemy и фабрика сессий.
- `src/db/base.py` — базовый класс ORM.

### 4) Слой репозиториев

- `src/repositories/*.py`
- Отвечает только за CRUD и выборки.
- Бизнес-правил в репозиториях нет.

### 5) Слой бизнес-логики

- `src/services/auth_service.py` — регистрация/вход/баланс.
- `src/services/booking_service.py` — бронирования, валидации интервалов, оплата.
- `src/services/arena_service.py` — управление ПК и логика залов.
- `src/services/tournament_service.py` — турниры, заявки, команды, архив, закрытие и выплаты.
- `src/services/pricing.py` — стратегия расчета стоимости брони (паттерн Strategy).

### 6) API-слой

- `src/api/deps.py` — DI: сборка сервисов из репозиториев.
- `src/api/routers/*.py` — REST-эндпоинты (`auth`, `arenas`, `bookings`, `tournaments`).

### 7) Web-слой

- `src/web/router.py` — маршруты страниц и обработка HTML-форм.
- `src/web/templates/base.html` — базовый шаблон.
- `src/web/templates/index.html` — публичная страница (гость/авторизация).
- `src/web/templates/player.html` — кабинет игрока.
- `src/web/templates/admin.html` — кабинет администратора.
- `src/web/static/site.css` — стили интерфейса.

### 8) Тестовый слой

- `tests/unit/` — unit-тесты сервисов.
- `tests/e2e/` — сквозные сценарии API + web.
- `tests/conftest.py` — фикстуры, изолированная тестовая БД.

---

## Структура репозитория

```text
lr5_green/
  src/
    api/
      deps.py
      routers/
    core/
      config.py
      security.py
    db/
      base.py
      models.py
      session.py
    repositories/
    schemas/
    services/
    web/
      static/
      templates/
      router.py
    main.py
  tests/
    unit/
    e2e/
    conftest.py
  docs/
    architecture.md
  requirements.txt
  README.md
  .gitignore
```

---

## Стек технологий

- Python 3.10+
- FastAPI
- SQLAlchemy 2.x (AsyncIO)
- SQLite (`aiosqlite`)
- Pydantic v2
- Jinja2 + Starlette Sessions
- Passlib (`bcrypt`)
- Pytest + Pytest-asyncio + HTTPX

---

## Запуск на новом ПК (с нуля)

### 1) Установить инструменты

- Установите Python 3.10+.
- Проверьте:

```powershell
python --version
pip --version
```

- (Опционально) установите Git.

### 2) Клонировать проект

```powershell
git clone <URL_ВАШЕГО_РЕПО>
cd <ИМЯ_РЕПО>\lr5_green
```

### 3) Создать виртуальное окружение

```powershell
python -m venv .venv
```

### 4) Установить зависимости

#### Вариант A (рекомендуется для PowerShell, даже если `ExecutionPolicy` запрещает `Activate.ps1`)

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

#### Вариант B (через активацию окружения)

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5) Запустить приложение

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload
```

Открыть в браузере:
- `http://127.0.0.1:8000/` — главная;
- `http://127.0.0.1:8000/player` — кабинет игрока;
- `http://127.0.0.1:8000/admin` — кабинет админа;
- `http://127.0.0.1:8000/docs` — Swagger.

### 6) Демо-администратор

- Email: `admin@cyberclub.com`
- Password: `admin123`

### 7) Что происходит на первом запуске

`src/main.py` автоматически:
- создаст таблицы в SQLite;
- добавит недостающие колонки для совместимости старых БД;
- заполнит демо-данные (категории, турниры, admin).

База по умолчанию: `esports_lab4.db` (в корне `lr5_green`).

---

## Как пользоваться системой

### Сценарий игрока

1. Открыть `/` и зарегистрироваться.
2. Выполнить вход.
3. Перейти в `/player`.
4. Подать заявку на турнир (при необходимости указать название команды).
5. Создать бронь ПК на будущий интервал времени.
6. Оплатить бронь с баланса.

### Сценарий администратора

1. Войти под админом и перейти в `/admin`.
2. Создать или удалить турнир.
3. Назначить ПК (зал) турниру.
4. Обработать заявки игроков.
5. Закрыть турнир, выбрать победителей.
6. Проверить начисления на балансы и архив событий.
7. При необходимости отредактировать архив/балансы/список ПК.

---

## REST API (краткая карта)

### Auth

- `POST /auth/register`
- `POST /auth/login`

### Arenas

- `GET /arenas`
- `GET /arenas/free-count`
- `POST /arenas`
- `PUT /arenas/{arena_id}`
- `DELETE /arenas/{arena_id}`

### Bookings

- `POST /bookings`
- `POST /bookings/{booking_id}/pay`
- `GET /bookings/user/{user_id}`

### Tournaments

- `GET /tournaments`
- `POST /tournaments`
- `DELETE /tournaments/{tournament_id}`
- `POST /tournaments/{tournament_id}/close`
- `GET /tournaments/categories`
- `GET /tournaments/teams`
- `POST /tournaments/applications`
- `POST /tournaments/applications/{application_id}/review`
- `POST /tournaments/{tournament_id}/assign-hall/{arena_id}`
- `GET /tournaments/archive/events`
- `PUT /tournaments/archive/events/{event_id}`
- `GET /tournaments/archive/results`

Полная и актуальная схема всегда доступна в `/docs`.

---

## Тестирование

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Запустить только unit:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit -q
```

Запустить только e2e:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/e2e -q
```

---

## Подготовка к загрузке на GitHub

Перед публикацией рекомендуется:

1. Проверить, что тесты проходят.
2. Убедиться, что в коммит не попали локальные артефакты (`.venv`, `.pytest_cache`, локальные БД).
3. Заполнить/проверить `README.md` и `requirements.txt`.

Базовые команды:

```powershell
git init
git add .
git commit -m "LR5: cybersport club complete implementation"
git branch -M main
git remote add origin <URL_ВАШЕГО_РЕПО>
git push -u origin main
```

---

## Типовые проблемы и решения

### 1) Ошибка PowerShell: `execution of scripts is disabled`

Используйте запуск без активации окружения:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload
```

### 2) Ошибка SQLite: `no such column ...`

Причина: старая локальная БД не соответствует текущим моделям.

Решение:
- Перезапустить приложение (встроенные совместимые миграции выполняются на startup).
- Если БД сильно устарела: удалить `esports_lab4.db` и запустить снова.

### 3) `500 Internal Server Error` на главной

Чаще всего проблема в локальной БД или неполной установке зависимостей.

Проверьте:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Затем перезапустите сервер.

### 4) Порт 8000 занят

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload --port 8001
```

---

## Переменные окружения

По умолчанию проект запускается без дополнительной настройки.

Поддерживаемые переменные:

- `DATABASE_URL` — строка подключения к БД.
- `SESSION_SECRET_KEY` — ключ сессий Starlette.
- `ADMIN_EMAILS` — список email админов через запятую.

Пример для PowerShell:

```powershell
$env:DATABASE_URL="sqlite+aiosqlite:///./esports_lab4.db"
$env:SESSION_SECRET_KEY="change-me"
$env:ADMIN_EMAILS="admin@cyberclub.com,second_admin@cyberclub.com"
```

---

## Примечание по учебному формату

Проект ориентирован на требования ЛР4/ЛР5:
- TDD-подход (red/green);
- слоистая архитектура;
- изоляция бизнес-логики в сервисах;
- отсутствие прямого доступа UI к БД;
- расширяемость для следующих этапов (миграции, полноценная RBAC-авторизация, CI/CD).
