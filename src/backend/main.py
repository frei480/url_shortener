import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.backend.config import cfg
from src.backend.model import Link, UserCreate
from src.backend.repository import (
    get_link_by_full_url,
    get_short_link,
    get_user,
)
from src.backend.users import User, fake_hash_password, get_current_active_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = f"postgresql+asyncpg://{cfg.db_user}:{cfg.db_pass}@{cfg.db_host}:{cfg.db_port}/{cfg.db_name}"


async def get_session():
    async with AsyncSession(app.state.engine) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[User, Depends(get_current_active_user)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = create_async_engine(DB_URL, echo=True)
    app.state.logined = False
    logger.info("Start app")

    yield


app = FastAPI(title="Url shortener", lifespan=lifespan)


@app.get("/health", status_code=200)
def health_check():
    return {"status": "ok"}


@app.get("/details/{short_link}", response_model=Link)
async def get_details(short_link: str, session: SessionDep) -> Link:
    result = await get_short_link(session, short_link)
    link = result.first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


async def short_lnk_generator(session: SessionDep) -> str:
    short_link: str = uuid4().hex[:8]
    while True:
        check_short_link = await get_short_link(session, short_link)
        if check_short_link.first() is None:
            break
        short_link = uuid4().hex[:8]
    return short_link


@app.post("/shorten", response_model=Link, status_code=201)
async def create_short_url(
    original_url: str,
    session: SessionDep,
    current_user: UserDep,
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await get_link_by_full_url(session, original_url)
    exists_link = result.first()

    if exists_link:
        return exists_link

    short_link: str = await short_lnk_generator(session)

    link = Link(original_url=original_url, short_url=short_link)
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


@app.get("/{short_link}", response_class=RedirectResponse)
async def redirect_to_original_url(short_link: str, session: SessionDep):
    result = await get_short_link(session, short_link)
    link = result.first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        await session.delete(link)
        await session.commit()
        raise HTTPException(status_code=410, detail="Link has expired")

    link.update_access_time()

    str_to_jump: str = link.original_url
    session.add(link)
    await session.commit()
    return RedirectResponse(str_to_jump, status_code=301)


@app.delete("/{short_link}")
async def erase_short_link(
    short_link: str,
    session: SessionDep,
    _: UserDep,
):
    result = await get_short_link(session, short_link)
    link = result.first()
    if link:
        await session.delete(link)
        await session.commit()
    return {f"{short_link}": "deleted"}


@app.post("/users/add", status_code=201)
async def create_user(payload: UserCreate, session: SessionDep):
    result = await get_user(session, payload)
    existing = result.first()
    conflict = ""
    if existing:
        if existing.username:
            conflict = f"username {existing.username}"
        if existing.email:
            conflict = f"e-mail {existing.email}"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with {conflict} already exists",
        )
    new_user = User(
        username=payload.username,
        full_name=payload.username,
        email=payload.email,
        hashed_password=fake_hash_password(payload.passwd),
        disabled=False,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return {"status": "ok", "user_id": new_user.id}


@app.get("/users/me")
def read_current_user(user: UserDep):
    return {"user": user}


if __name__ == "__main__":
    uvicorn.run("src.backend.main:app", host="0.0.0.0", reload=True)
