 
# Url Shortener

Лёгкий сервис для сокращения URL на базе FastAPI и SQLModel.

**Коротко:** сервис предоставляет API для создания коротких ссылок, редиректа по короткой ссылке и получения деталей ссылки.

**Ключевые технологии:** `FastAPI`, `SQLModel`, `Alembic` (миграции), `asyncpg` (Postgres драйвер), `uvicorn`.

**Требования:** Python >= `3.13.7` (см. `pyproject.toml`).

**Основные endpoint'ы** (см. `src/backend/main.py`):

- `GET /health` — проверка статуса сервиса.
- `POST /shorten?original_url=...` — создать короткую ссылку (возвращает модель `Link`).
- `GET /{short_link}` — редирект (301) на исходный URL или возвращает `410` если ссылка истекла.
- `GET /details/{short_link}` — получить модель `Link` с метаданными.

Устройство проекта
- `src/backend/main.py` — HTTP API, lifespan фазa, DI для `AsyncSession`.
- `src/backend/model.py` — модель `Link` (SQLModel), поля: `original_url`, `short_url`, `created_at`, `last_accessed_at`, `expires_at`.
- `src/backend/repository.py` — функции доступа к данным (`get_short_link`, `get_link_by_full_url`).
- `src/backend/db/session.py` — глобальный engine (используется в проде), вспомогательный `get_session`.
- `alembic/` + `alembic.ini` — миграции схемы базы данных.
- `tests/` — тесты и fixtures (используются `sqlite+aiosqlite` и alembic для тестовой БД).

Запуск локально (development)

1) Установите зависимости в виртуальном окружении (пример с pip):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r <(python - <<'PY'
import tomllib,sys
print('\n'.join([]))
PY)
```

Примечание: проект использует `pyproject.toml` и списки зависимостей; можно использовать `pip`/`uv`/`poetry` по вашему выбору.

2) Создайте файл `.env` в корне (пример):

```env
DB_USER=postgres
DB_PASS=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=url_shortener
```

3) Запуск сервера (dev):

```bash
python -m src.backend.main
# либо
uvicorn "src.backend.main:app" --reload --host 0.0.0.0 --port 8000
```

Запуск в Docker / compose

```bash
docker compose -f compose.yml up --build
```

Файл `compose.yml` уже настраивает сервис `url_shortener` и контейнер `postgres`.

Миграции (Alembic)

- Чтобы создать ревизию: `alembic revision --autogenerate -m "msg"`
- Применить миграции: `alembic upgrade head`
- В тестах fixture `apply_migrations` переключает `sqlalchemy.url` на `sqlite+aiosqlite:///test.db` перед применением миграций.

Тестирование

Запуск тестов локально:

```bash
pytest
```

Особенности тестовой среды:
- `tests/conftest.py` создаёт `AsyncEngine` для `sqlite+aiosqlite:///test.db` и подменяет зависимость `get_session` в `app.dependency_overrides`.
- Тесты используют fixture `apply_migrations`, которая делает `alembic downgrade base` и `alembic upgrade head` для чистой схемы.

Особенности кода и важные заметки для модификаций

- В `src/backend/main.py` engine создаётся в `lifespan` и сохраняется в `app.state.engine`. Тесты ожидают такую стратегию и подменяют `app.state.engine` в `tests/conftest.py`.
- Функции в `src/backend/repository.py` возвращают результат `session.exec(...)`. Вызывающая сторона (endpoint) использует `.first()` / `.one()` — учитывайте это при рефакторинге.
- Временные метки в `Link` — naive UTC (`datetime.now(timezone.utc).replace(tzinfo=None)`). Не переводите в aware объекты без комплексной проверки тестов.

PR / рефакторинг рекомендации

- При добавлении полей в модель: обновите `src/backend/model.py`, создайте alembic-revision и примените миграции; затем обновите/дополните тесты.
- Не менять сигнатуры публичных endpoint'ов без необходимости — тесты и внешние клиенты завязаны на них.

Дополнительно

- Если хотите, могу добавить `./.env.example`, CI workflow (`.github/workflows/ci.yml`) для автоматического запуска `pytest`, или более подробный пример установки зависимостей.

Контакты и обратная связь

Если часть инструкций неясна или хотите расширить README (например, добавить архитектурную диаграмму или последовательность вызовов), скажите — доработаю.

