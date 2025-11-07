from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class Link(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    original_url: str = Field(index=True)
    short_url: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=365)
    )


engine = create_async_engine(DB_URL, echo=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async with AsyncSession(engine) as session:
        yield session
