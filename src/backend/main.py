import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.backend.config import ConfigBase as cfg
from src.backend.model import Link

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


DB_URL = f"postgresql+asyncpg://{cfg.db_user}:{cfg.db_pass}@{cfg.db_host}:{cfg.db_port}/{cfg.db_name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = create_async_engine(DB_URL, echo=True)
    logger.info("before init db")
    await init_db()
    yield


app = FastAPI(title="Url shortener", lifespan=lifespan)


async def init_db():
    async with app.state.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async with AsyncSession(app.state.engine) as session:
        yield session


@app.get("/health", status_code=200)
def health_check():
    return {"status": "ok"}


@app.get("/details/{short_link}", response_model=Link)
async def get_details(short_link: str, session: AsyncSession = Depends(get_session)):
    link = await session.exec(select(Link).where(Link.short_url == short_link))
    link_obj = link.first()
    if not link_obj:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


async def short_lnk_generator(session: AsyncSession) -> str:
    short_link: str = uuid4().hex[:8]
    while True:
        check_short_link = await session.exec(
            select(Link).where(Link.short_url == short_link)
        )
        if check_short_link.first() is None:
            break
        short_link = uuid4().hex[:8]
    return short_link


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

    short_link: str = await short_lnk_generator(session)

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

    if link_obj.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        await session.delete(link)
        await session.commit()
        raise HTTPException(status_code=410, detail="Link has expired")

    link_obj.update_access_time()

    str_to_jump: str = link_obj.original_url
    session.add(link_obj)
    await session.commit()
    return RedirectResponse(str_to_jump, status_code=301)


def main():
    print("Hello from url-shortener!")


if __name__ == "__main__":
    uvicorn.run("src.backend.main:app", host="0.0.0.0", reload=True)
