from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationTrigger


async def create(db: AsyncSession, trig: NotificationTrigger) -> NotificationTrigger:
    db.add(trig)
    await db.flush()
    return trig


async def list_for_entity(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    entity: str,
    entity_id: uuid.UUID,
    cursor: str | None,
    limit: int,
) -> tuple[list[NotificationTrigger], str | None]:
    q = select(NotificationTrigger).where(
        NotificationTrigger.user_id == user_id,
        NotificationTrigger.entity == entity,
        NotificationTrigger.entity_id == entity_id,
        NotificationTrigger.deleted == False,  # noqa: E712
    )

    if cursor:
        try:
            ts_str, id_str = cursor.split("|")
            ts = datetime.fromisoformat(ts_str)
            cid = uuid.UUID(id_str)
            q = q.where((NotificationTrigger.updated_at, NotificationTrigger.id) < (ts, cid))
        except Exception:
            pass

    q = q.order_by(NotificationTrigger.updated_at.desc(), NotificationTrigger.id.desc()).limit(max(1, min(limit, 100)) + 1)
    res = await db.execute(q)
    rows = res.scalars().all()

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = f"{last.updated_at.isoformat()}|{last.id}"
        rows = rows[:limit]

    return rows, next_cursor


async def soft_delete(db: AsyncSession, *, trigger_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(NotificationTrigger).where(NotificationTrigger.id == trigger_id).values(**values))
