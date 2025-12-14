from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.backend.deps import SessionDep
from src.backend.model import Link, User, UserCreate
from src.backend.utils import fake_hash_password


async def get_short_link(session: AsyncSession, short_link: str):
    result = await session.exec(select(Link).where(Link.short_url == short_link))
    return result


async def get_link_by_full_url(session: AsyncSession, original_url: str):
    result = await session.exec(select(Link).where(Link.original_url == original_url))
    return result


async def get_user(username: str, session: SessionDep):
    result = await session.exec(
        select(User).where((User.username == username) | (User.email == username))
    )
    if result:
        return result.first()
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def creating_user(session: AsyncSession, payload: UserCreate):
    result = await session.exec(
        select(User).where(
            (User.username == payload.username) | (User.email == payload.email)
        )
    )

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
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=fake_hash_password(payload.passwd),
        disabled=False,
    )
    return new_user
