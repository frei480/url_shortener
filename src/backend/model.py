from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Link(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    original_url: str = Field(index=True)
    short_url: str = Field(unique=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    last_accessed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=365)
    )

    def update_access_time(self):
        self.last_accessed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            days=365
        )
