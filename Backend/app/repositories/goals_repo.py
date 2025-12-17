from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal


async def list(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    updated_from: datetime | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[Goal], str | None]:
    q = select(Goal).where(Goal.user_id == user_id, Goal.deleted == False)  # noqa: E712
    if updated_from:
        q = q.where(Goal.updated_at >= updated_from)

    if cursor:
        try:
            ts_str, id_str = cursor.split("|")
            ts = datetime.fromisoformat(ts_str)
            cid = uuid.UUID(id_str)
            q = q.where((Goal.updated_at, Goal.id) < (ts, cid))
        except Exception:
            pass

    q = q.order_by(Goal.updated_at.desc(), Goal.id.desc()).limit(max(1, min(limit, 100)) + 1)
    res = await db.execute(q)
    rows = res.scalars().all()

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = f"{last.updated_at.isoformat()}|{last.id}"
        rows = rows[:limit]

    return rows, next_cursor


async def get_by_id(db: AsyncSession, *, user_id: uuid.UUID, goal_id: uuid.UUID) -> Goal | None:
    res = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id, Goal.deleted == False))  # noqa: E712
    return res.scalar_one_or_none()


async def create(db: AsyncSession, goal: Goal) -> Goal:
    db.add(goal)
    await db.flush()
    return goal


async def patch(db: AsyncSession, *, goal_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(Goal).where(Goal.id == goal_id).values(**values))
