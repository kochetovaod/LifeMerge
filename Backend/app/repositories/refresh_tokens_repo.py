from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


async def create(db: AsyncSession, token: RefreshToken) -> RefreshToken:
    db.add(token)
    await db.flush()
    return token


async def find_valid(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    device_id: str,
    token_hash: str,
    now: datetime,
) -> RefreshToken | None:
    res = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.device_id == device_id,
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > now,
        )
    )
    return res.scalar_one_or_none()


async def revoke(db: AsyncSession, *, token_id: uuid.UUID) -> None:
    await db.execute(update(RefreshToken).where(RefreshToken.id == token_id).values(revoked=True))


async def revoke_device(db: AsyncSession, *, user_id: uuid.UUID, device_id: str) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.device_id == device_id)
        .values(revoked=True)
    )
