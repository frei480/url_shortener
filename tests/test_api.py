from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.backend.model import Link


@pytest.mark.asyncio
async def test_healthcheck(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.usefixtures("apply_migrations", "test_user")
@pytest.mark.asyncio
async def test_link_redirect(client: AsyncClient, session: AsyncSession):
    url: str = "http://www.example.com"
    response = await client.post("/shorten", params={"original_url": url})
    short_url = response.json()["short_url"]

    response2 = await client.get(f"/{short_url}", follow_redirects=False)

    assert response2.status_code == 301


@pytest.mark.usefixtures("apply_migrations", "test_user")
@pytest.mark.asyncio
async def test_link_expiration(client: AsyncClient, session: AsyncSession):
    url: str = "http://www.example.com"
    response = await client.post("/shorten", params={"original_url": url})
    short_url = response.json()["short_url"]
    link_result = await session.exec(select(Link).where(Link.short_url == short_url))
    link: Link = link_result.one()
    link.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        days=1
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)

    response_expired = await client.get(f"/{short_url}", follow_redirects=False)

    assert response_expired.status_code == 410
    assert response_expired.json()["detail"] == "Link has expired"


@pytest.mark.usefixtures("apply_migrations", "test_user")
@pytest.mark.asyncio
async def test_shorten_url_really_short(client: AsyncClient):
    response = await client.post(
        "/shorten", params={"original_url": "https://www.example.com"}
    )

    data = response.json()

    assert response.status_code == 201
    assert len(data["short_url"]) == 8


@pytest.mark.asyncio
async def test_redirect_404(client: AsyncClient):
    response = await client.get("/notexists")

    data = response.json()
    assert data == {"detail": "Link not found"}
    assert response.status_code == 404


@pytest.mark.usefixtures("apply_migrations", "test_user")
@pytest.mark.asyncio
async def test_link_details(client: AsyncClient, session: AsyncSession):
    url: str = "http://www.example.com"
    response = await client.post("/shorten", params={"original_url": url})
    short_url = response.json()["short_url"]

    response2 = await client.get(f"/details/{short_url}", follow_redirects=False)

    assert response2.json()["short_url"] == short_url
    assert response2.json()["original_url"] == url


@pytest.mark.asyncio
async def test_auth_current_user(client: AsyncClient):
    response = await client.get("/users/me")
    assert response.status_code == 401


@pytest.mark.usefixtures("test_user")
@pytest.mark.asyncio
async def test_auth_current_user_success(client: AsyncClient):
    response = await client.get("/users/me")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_unauthorized(client: AsyncClient):
    response = await client.delete("/ihavenoidea")
    assert response.status_code == 401


@pytest.mark.usefixtures("apply_migrations", "test_user")
async def test_delete_authorized(client: AsyncClient):
    url: str = "http://www.example.com"
    response = await client.post("/shorten", params={"original_url": url})
    short_url = response.json()["short_url"]

    response = await client.delete(f"/{short_url}")
    assert response.status_code == 200
    assert response.json() == {f"{short_url}": "deleted"}
