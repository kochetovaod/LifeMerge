from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    res = await db.execute(select(User).where(User.email == email.lower(), User.deleted == False))  # noqa: E712
    return res.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id) -> User | None:
    res = await db.execute(select(User).where(User.id == user_id, User.deleted == False))  # noqa: E712
    return res.scalar_one_or_none()


async def create(db: AsyncSession, *, email: str, password_hash: str, full_name: str | None, timezone: str) -> User:
    user = User(email=email.lower(), password_hash=password_hash, full_name=full_name, timezone=timezone)
    db.add(user)
    await db.flush()
    return user
