from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.backend.db.session import get_session
from src.backend.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL)


@pytest.fixture(name="session")
async def session_fixture() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(test_engine) as session:
        yield session


@pytest.fixture(name="client")
async def client_fixture(session: AsyncSession) -> AsyncGenerator[TestClient]:
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app, base_url="http://localhost:8000")
    yield client
