from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.backend.config import ConfigBase

cfg = ConfigBase()  # type: ignore
DB_URL = f"postgresql+asyncpg://{cfg.db_user}:{cfg.db_pass}@{cfg.db_host}:{cfg.db_port}/{cfg.db_name}"
engine = create_async_engine(DB_URL, echo=True)


async def get_session():
    async with AsyncSession(engine) as session:
        yield session
