from typing import AsyncGenerator

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from alembic import command
from src.backend.config import cfg
from src.backend.db.session import get_session
from src.backend.main import app
from src.backend.users import fake_users_db, get_current_active_user, get_user

ALEMBIC_CONFIG_PATH = "./alembic.ini"
TEST_DB_URL = "sqlite:///test.db"
ASYNC_TEST_DB_URL = "sqlite+aiosqlite:///test.db"


@pytest.fixture(scope="session")
def test_user():
    user = get_user(fake_users_db, cfg.username)
    app.dependency_overrides[get_current_active_user] = lambda: user


@pytest.fixture(scope="session")
async def test_engine():
    """Creates the Async Engine."""
    engine = create_async_engine(ASYNC_TEST_DB_URL)

    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
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
    app.state.engine = create_async_engine(ASYNC_TEST_DB_URL)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
        yield ac
