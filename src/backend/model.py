from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


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
    user_id: UUID | None = Field(default=None, foreign_key="user.id")
    user: User | None = Relationship(back_populates="links")

    def update_access_time(self):
        self.last_accessed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            days=365
        )


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    username: str
    full_name: str
    email: str
    hashed_password: str
    disabled: bool
    links: list["Link"] = Relationship(back_populates="user")
