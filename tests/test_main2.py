from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.backend.model import Link


@pytest.mark.asyncio
async def test_healthcheck(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_link_redirect(client: TestClient, session: AsyncSession):
    url: str = "http://www.example.com"
    response = client.post("/shorten", params={"original_url": url})
    short_url = response.json()["short_url"]

    response2 = client.get(f"/{short_url}", follow_redirects=False)

    assert response2.status_code == 301


@pytest.mark.asyncio
async def test_link_expiration(client: TestClient, session: AsyncSession):
    url: str = "http://www.example.com"
    response = client.post("/shorten", params={"original_url": url})
    short_url = response.json()["short_url"]
    link_result = await session.exec(select(Link).where(Link.short_url == short_url))
    link: Link = link_result.one()
    link.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        days=1
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)

    response_expired = client.get(f"/{short_url}", follow_redirects=False)

    assert response_expired.status_code == 410
    assert response_expired.json()["detail"] == "Link has expired"


@pytest.mark.asyncio
async def test_shorten_url_really_short(client: TestClient):
    response = client.post(
        "/shorten", params={"original_url": "https://www.example.com"}
    )

    data = response.json()

    assert response.status_code == 201
    assert len(data["short_url"]) == 8


@pytest.mark.asyncio
async def test_redirect_404(client: TestClient):
    response = client.get("/notexists")

    data = response.json()
    assert data == {"detail": "Link not found"}
    assert response.status_code == 404
