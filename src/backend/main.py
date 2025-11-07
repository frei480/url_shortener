from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

import uvicorn
from database import get_session, init_db
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from model import Link
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Url shortener", lifespan=lifespan)


@app.post("/shorten", response_model=Link, status_code=201)
async def create_short_url(
    original_url: str, session: AsyncSession = Depends(get_session)
):
    exists_link = await session.exec(
        select(Link).where(Link.original_url == original_url)
    )
    exists_link_obj = exists_link.first()

    if exists_link_obj:
        return exists_link_obj

    short_link: str = uuid4().hex[8:]
    while True:
        check_short_link = await session.exec(
            select(Link).where(Link.short_url == short_link)
        )
        if check_short_link.first() is None:
            break
        short_link = uuid4().hex[8:]
    link = Link(original_url=original_url, short_url=short_link)
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


@app.get("/{short_link}", response_class=RedirectResponse)
async def redirect_to_original_url(
    short_link: str, session: AsyncSession = Depends(get_session)
):
    link = await session.exec(select(Link).where(Link.short_url == short_link))
    link_obj = link.first()
    if not link_obj:
        raise HTTPException(status_code=404, detail="Link not found")

    if link_obj.expires_at < datetime.now(timezone.utc):
        await session.delete(link)
        await session.commit()
        raise HTTPException(status_code=410, detail="Link has expired")

    link_obj.update_access_time()

    session.add(link)
    await session.commit()

    return RedirectResponse(link_obj.original_url, status_code=302)


@app.get("/health", status_code=200)
def health_check():
    return {"status": "ok"}


def main():
    print("Hello from url-shortener!")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True)
