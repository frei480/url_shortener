from typing import AsyncGenerator

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from alembic import command
from src.backend.db.session import get_session
from src.backend.main import app

ALEMBIC_CONFIG_PATH = "./alembic.ini"
TEST_DB_URL = "sqlite:///test.db"
ASYNC_TEST_DB_URL = "sqlite+aiosqlite:///test.db"

# test_engine = create_async_engine(TEST_DB_URL)


# @pytest.fixture(scope="session")
# def event_loop():
#     """Overrides pytest default loop to be session-scoped."""
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Creates the Async Engine."""
    engine = create_async_engine(ASYNC_TEST_DB_URL)

    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
# async def apply_migrations(test_engine: AsyncEngine):
#     """
#     Applies Alembic migrations to the in-memory DB.
#     """
#     async with test_engine.begin() as conn:
#         alembic_cfg = Config("alembic.ini")
#         alembic_cfg.attributes["connection"] = conn
#         await conn.run_sync(lambda c: command.upgrade(alembic_cfg, "head"))
#     yield

def apply_migrations():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", ASYNC_TEST_DB_URL)
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(name="session")
async def session_fixture(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(test_engine) as session:
        yield session


@pytest.fixture(name="client")
async def client_fixture(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
        yield ac
    # client = TestClient(app, base_url="http://localhost:8000")
    # yield client
