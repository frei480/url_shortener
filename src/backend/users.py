import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.backend.config import cfg
from src.backend.model import User

fake_users_db: dict[str, dict[str, str | bool]] = {
    "appleseed": {
        "username": cfg.username,
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": f"fakehashed{cfg.password}",
        "disabled": False,
    },
}

security = HTTPBasic()


def fake_hash_password(password: str):
    return "fakehashed" + password


def get_user(db: dict[str, dict[str, str | bool]], username: str):
    user_data = db.get(username)
    if user_data:
        return User(**user_data)


def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    current_username_bytes = credentials.username.encode("utf8")
    user = get_user(fake_users_db, credentials.username)

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
