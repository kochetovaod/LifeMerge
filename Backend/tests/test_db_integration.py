from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.user import User


async def test_can_create_user_record(db_session):
    user = User(
        email="test@example.com",
        password_hash="hashed-password",
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)

    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    stored_user = result.scalar_one()
    assert stored_user.email == "test@example.com"
    assert stored_user.password_hash == "hashed-password"
