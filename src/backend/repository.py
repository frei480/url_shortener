from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.backend.model import Link


async def get_short_link(session: AsyncSession, short_link: str):
    result = await session.exec(select(Link).where(Link.short_url == short_link))
    return result


async def get_link_by_full_url(session: AsyncSession, original_url: str):
    result = await session.exec(select(Link).where(Link.original_url == original_url))
    return result
