from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.backend.main import app, get_session

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL)
app.state.engine = test_engine


@pytest.fixture(scope="session")
async def create_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        yield


async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(app.state.engine) as session:
        yield session
    # async with AsyncSession(test_engine) as session:
    #     yield session
    # await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="session")
def app_with_override():
    # app.state.engine = test_engine

    app.dependency_overrides[get_session] = get_test_session
    yield app
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
async def ac(app_with_override: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app_with_override), base_url="http://localhost:8000"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_healthcheck(ac: AsyncClient):
    response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.usefixtures("create_test_db")
@pytest.mark.asyncio
async def test_shorten_url(ac: AsyncClient):
    response1 = await ac.post(
        "/shorten", params={"original_url": "https://www.example.com"}
    )
    response2 = await ac.post(
        "/shorten", params={"original_url": "https://www.example.com"}
    )

    data1 = response1.json()
    data2 = response2.json()

    assert response1.status_code == 201
    assert response2.status_code == 201
    assert data1["id"] == data2["id"]
    assert data1["short_url"] == data2["short_url"]
