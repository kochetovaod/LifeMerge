from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subtask import Subtask


async def get_by_id(db: AsyncSession, *, subtask_id: uuid.UUID, user_id: uuid.UUID) -> Subtask | None:
    res = await db.execute(
        select(Subtask).where(Subtask.id == subtask_id, Subtask.user_id == user_id, Subtask.deleted == False)  # noqa: E712
    )
    return res.scalar_one_or_none()


async def list_by_task(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    task_id: uuid.UUID,
    cursor: str | None,
    limit: int,
) -> tuple[list[Subtask], str | None]:
    q = select(Subtask).where(
        Subtask.user_id == user_id,
        Subtask.task_id == task_id,
        Subtask.deleted == False,  # noqa: E712
    )

    if cursor:
        try:
            ts_str, id_str = cursor.split("|")
            ts = datetime.fromisoformat(ts_str)
            cid = uuid.UUID(id_str)
            q = q.where((Subtask.updated_at, Subtask.id) < (ts, cid))
        except Exception:
            pass

    q = q.order_by(Subtask.updated_at.desc(), Subtask.id.desc()).limit(max(1, min(limit, 100)) + 1)
    res = await db.execute(q)
    rows = res.scalars().all()

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = f"{last.updated_at.isoformat()}|{last.id}"
        rows = rows[:limit]

    return rows, next_cursor


async def create(db: AsyncSession, subtask: Subtask) -> Subtask:
    db.add(subtask)
    await db.flush()
    return subtask


async def patch(db: AsyncSession, *, subtask_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(Subtask).where(Subtask.id == subtask_id).values(**values))


async def soft_delete(db: AsyncSession, *, subtask_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(Subtask).where(Subtask.id == subtask_id).values(**values))
