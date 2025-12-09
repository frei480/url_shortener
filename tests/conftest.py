import asyncio
import uuid
from typing import AsyncGenerator

import asyncpg
import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from alembic import command
from src.backend.config import cfg
from src.backend.db.session import get_session
from src.backend.main import app
from src.backend.users import fake_users_db, get_current_active_user, get_user

ALEMBIC_CONFIG_PATH = "./alembic.ini"

ASYNC_TEST_DB_URL = (
    f"postgresql+asyncpg://{cfg.db_user}:{cfg.db_pass}@{cfg.db_host}:{cfg.db_port}"
)


@pytest.fixture(scope="function")
def temp_db_name() -> str:
    cfg.db_name = "_".join((uuid.uuid4().hex, "pytest"))
    return cfg.db_name


@pytest.fixture(scope="function")
async def temp_db(temp_db_name: str) -> AsyncGenerator[str]:
    SYNC_TEST_URL = (
        f"postgresql://{cfg.db_user}:{cfg.db_pass}@{cfg.db_host}:{cfg.db_port}"
    )

    # Create temp database
    conn = await asyncpg.connect(dsn=SYNC_TEST_URL)
    await conn.execute(f'CREATE DATABASE "{temp_db_name}" OWNER "{cfg.db_user}"')
    await conn.close()

    try:
        yield ASYNC_TEST_DB_URL + f"/{temp_db_name}"
    finally:
        pass
        conn = await asyncpg.connect(dsn=SYNC_TEST_URL)
        await conn.execute(f'DROP DATABASE "{temp_db_name}"')
        await conn.close()


@pytest.fixture(scope="function")
def test_user():
    user = get_user(fake_users_db, cfg.username)
    app.dependency_overrides[get_current_active_user] = lambda: user
    yield
    del app.dependency_overrides[get_current_active_user]


@pytest.fixture(scope="function")
async def test_engine(temp_db: str) -> AsyncGenerator[AsyncEngine, None]:
    """Creates the Async Engine."""
    engine = create_async_engine(temp_db, echo=True)

    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
def apply_migrations(temp_db_name, test_engine):
    alembic_cfg = Config("alembic.ini")
    cfg.db_name = temp_db_name

    # command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(name="session")
async def session_fixture(
    test_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(test_engine) as session:
        yield session


@pytest.fixture(name="client")
async def client_fixture(
    session: AsyncSession, test_engine: AsyncEngine
) -> AsyncGenerator[AsyncClient]:
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    app.state.engine = test_engine  # create_async_engine(ASYNC_TEST_DB_URL)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
        yield ac
