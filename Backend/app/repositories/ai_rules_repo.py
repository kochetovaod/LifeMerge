from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_user_rule import AiUserRule


async def get_by_user_id(db: AsyncSession, *, user_id: uuid.UUID) -> AiUserRule | None:
    res = await db.execute(select(AiUserRule).where(AiUserRule.user_id == user_id, AiUserRule.deleted == False))  # noqa: E712
    return res.scalar_one_or_none()


async def create(db: AsyncSession, rules: AiUserRule) -> AiUserRule:
    db.add(rules)
    await db.flush()
    return rules


async def update_rules(db: AsyncSession, *, rule_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(AiUserRule).where(AiUserRule.id == rule_id).values(**values))
