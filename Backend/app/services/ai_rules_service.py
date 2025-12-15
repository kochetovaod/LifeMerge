from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_user_rule import AiUserRule
from app.repositories import ai_rules_repo


async def get_rules(db: AsyncSession, *, user_id: uuid.UUID) -> AiUserRule | None:
    return await ai_rules_repo.get_by_user_id(db, user_id=user_id)


async def upsert_rules(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    quiet_hours: list,
    breaks: list,
    blocked_days: list,
) -> AiUserRule:
    existing = await ai_rules_repo.get_by_user_id(db, user_id=user_id)
    now = datetime.now(timezone.utc)

    payload = {
        "quiet_hours": quiet_hours,
        "breaks": breaks,
        "blocked_days": blocked_days,
        "updated_at": now,
        "deleted": False,
    }

    if existing:
        await ai_rules_repo.update_rules(db, rule_id=existing.id, values=payload)
        await db.refresh(existing)
        return existing

    new_rules = AiUserRule(user_id=user_id, created_at=now, **payload)
    return await ai_rules_repo.create(db, new_rules)
