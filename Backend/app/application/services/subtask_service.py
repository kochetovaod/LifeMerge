from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subtask import Subtask
from app.repositories import subtasks_repo


async def list_subtasks(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    task_id: uuid.UUID,
    cursor: str | None,
    limit: int,
) -> tuple[list[Subtask], str | None]:
    return await subtasks_repo.list_by_task(db, user_id=user_id, task_id=task_id, cursor=cursor, limit=limit)


async def create_subtask(db: AsyncSession, *, user_id: uuid.UUID, task_id: uuid.UUID, title: str) -> Subtask:
    now = datetime.now(timezone.utc)
    st = Subtask(
        user_id=user_id,
        task_id=task_id,
        title=title,
        done=False,
        created_at=now,
        updated_at=now,
        deleted=False,
    )
    return await subtasks_repo.create(db, st)


async def update_subtask(
    db: AsyncSession,
    *,
    subtask: Subtask,
    patch: dict,
    expected_updated_at: datetime | None,
) -> Subtask:
    if expected_updated_at:
        a = subtask.updated_at.replace(tzinfo=timezone.utc)
        b = expected_updated_at.replace(tzinfo=timezone.utc)
        if a != b:
            raise ValueError("conflict")

    values = {k: v for k, v in patch.items() if v is not None and k not in {"request_id", "updated_at"}}
    values["updated_at"] = datetime.now(timezone.utc)

    await subtasks_repo.patch(db, subtask_id=subtask.id, values=values)
    await db.refresh(subtask)
    return subtask


async def soft_delete_subtask(db: AsyncSession, *, subtask: Subtask) -> Subtask:
    values = {"deleted": True, "updated_at": datetime.now(timezone.utc)}
    await subtasks_repo.soft_delete(db, subtask_id=subtask.id, values=values)
    await db.refresh(subtask)
    return subtask
