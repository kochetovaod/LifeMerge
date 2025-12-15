from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task


async def get_by_id(db: AsyncSession, *, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user_id, Task.deleted == False))  # noqa: E712
    return res.scalar_one_or_none()


async def list(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    status: str | None,
    goal_id: uuid.UUID | None,
    due_from: datetime | None,
    due_to: datetime | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[Task], str | None]:
    q = select(Task).where(Task.user_id == user_id, Task.deleted == False)  # noqa: E712
    if status:
        q = q.where(Task.status == status)
    if goal_id:
        q = q.where(Task.goal_id == goal_id)
    if due_from:
        q = q.where(Task.due_at >= due_from)
    if due_to:
        q = q.where(Task.due_at <= due_to)

    if cursor:
        try:
            ts_str, id_str = cursor.split("|")
            ts = datetime.fromisoformat(ts_str)
            cid = uuid.UUID(id_str)
            q = q.where((Task.updated_at, Task.id) < (ts, cid))
        except Exception:
            pass

    q = q.order_by(Task.updated_at.desc(), Task.id.desc()).limit(max(1, min(limit, 100)) + 1)
    res = await db.execute(q)
    rows = res.scalars().all()

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = f"{last.updated_at.isoformat()}|{last.id}"
        rows = rows[:limit]

    return rows, next_cursor


async def create(db: AsyncSession, task: Task) -> Task:
    db.add(task)
    await db.flush()
    return task


async def patch(db: AsyncSession, *, task_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(Task).where(Task.id == task_id).values(**values))


async def soft_delete(db: AsyncSession, *, task_id: uuid.UUID, values: dict) -> None:
    await db.execute(update(Task).where(Task.id == task_id).values(**values))
