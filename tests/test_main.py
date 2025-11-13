from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from src.backend.main import app, get_session

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL)


@pytest.fixture
async def session_fixture() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(test_engine) as session:
        yield session
        # await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
def override_get_session(session_fixture: AsyncSession):
    async def _get_session_override():
        yield session_fixture

    app.dependency_overrides[get_session] = _get_session_override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def ac(override_get_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_healthcheck(ac: AsyncClient):
    response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
