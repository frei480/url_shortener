import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.backend.deps import SessionDep
from src.backend.model import User
from src.backend.repository import get_user
from src.backend.utils import fake_hash_password

security = HTTPBasic()


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> User | None:
    current_username_bytes = credentials.username.encode("utf8")
    user = await get_user(
        credentials.username,
        session,
    )

    correct_username_bytes = user.username.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = fake_hash_password(credentials.password).encode("utf8")
    correct_password_bytes = user.hashed_password.encode("utf-8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
