from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    token_hash,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories import refresh_tokens_repo, users_repo


async def create_user(
    db: AsyncSession, email: str, password: str, full_name: str | None, timezone_name: str
) -> User:
    user = await users_repo.create(
        db,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        timezone=timezone_name,
    )
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await users_repo.get_by_email(db, email)


async def issue_tokens(db: AsyncSession, user: User, device_id: str) -> tuple[str, str]:
    access = create_access_token(subject=user.email, user_id=str(user.id))
    refresh = create_refresh_token(subject=user.email, user_id=str(user.id), device_id=device_id)

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.REFRESH_TOKEN_TTL_SECONDS)
    rt = RefreshToken(user_id=user.id, device_id=device_id, token_hash=token_hash(refresh), expires_at=expires_at)
    await refresh_tokens_repo.create(db, rt)

    return access, refresh


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


class RefreshError(Exception):
    code: str

    def __init__(self, code: str):
        self.code = code


async def refresh_tokens(db: AsyncSession, refresh_token: str, device_id: str) -> tuple[User, str, str]:
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise RefreshError("invalid_refresh")

    if payload.get("type") != "refresh":
        raise RefreshError("invalid_refresh")

    token_device = payload.get("device_id")
    if token_device != device_id:
        # required by Backend Lead: invalid device -> 401 refresh_invalid_device
        raise RefreshError("refresh_invalid_device")

    raw_uid = payload.get("uid")
    if not raw_uid:
        raise RefreshError("invalid_refresh")

    try:
        uid = uuid.UUID(str(raw_uid))
    except Exception:
        raise RefreshError("invalid_refresh")

    now = datetime.now(timezone.utc)
    h = token_hash(refresh_token)
    stored = await refresh_tokens_repo.find_valid(db, user_id=uid, device_id=device_id, token_hash=h, now=now)
    if not stored:
        raise RefreshError("invalid_refresh")

    user = await users_repo.get_by_id(db, uid)
    if not user:
        raise RefreshError("invalid_refresh")

    # rotation: revoke old token and issue new
    await refresh_tokens_repo.revoke(db, token_id=stored.id)
    access, new_refresh = await issue_tokens(db, user, device_id)
    return user, access, new_refresh


async def revoke_device_tokens(db: AsyncSession, user: User, device_id: str) -> None:
    await refresh_tokens_repo.revoke_device(db, user_id=user.id, device_id=device_id)
