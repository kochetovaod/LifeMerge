from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories import tasks_repo
from app.schemas.tasks import ALLOWED_STATUSES


async def list_tasks(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: str | None = None,
    goal_id: uuid.UUID | None = None,
    due_from: datetime | None = None,
    due_to: datetime | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> tuple[list[Task], str | None]:
    return await tasks_repo.list(
        db,
        user_id=user_id,
        status=status,
        goal_id=goal_id,
        due_from=due_from,
        due_to=due_to,
        cursor=cursor,
        limit=limit,
    )


async def create_task(db: AsyncSession, user_id: uuid.UUID, data: dict) -> Task:
    now = datetime.now(timezone.utc)
    task = Task(
        user_id=user_id,
        title=data["title"],
        description=data.get("description"),
        goal_id=data.get("goal_id"),
        due_at=data.get("due_at"),
        priority=data.get("priority"),
        estimated_minutes=data.get("estimated_minutes"),
        energy_level=data.get("energy_level"),
        status="todo",
        created_at=now,
        updated_at=now,
        deleted=False,
    )
    return await tasks_repo.create(db, task)


async def update_task(db: AsyncSession, task: Task, patch: dict, expected_updated_at: datetime | None) -> Task:
    if expected_updated_at:
        # normalize tz
        a = task.updated_at.replace(tzinfo=timezone.utc)
        b = expected_updated_at.replace(tzinfo=timezone.utc)
        if a != b:
            raise ValueError("conflict")

    values = {k: v for k, v in patch.items() if v is not None and k not in {"request_id", "updated_at"}}
    status = values.get("status")
    if status and status not in ALLOWED_STATUSES:
        raise ValueError("invalid_status")
    values["updated_at"] = datetime.now(timezone.utc)

    await tasks_repo.patch(db, task_id=task.id, values=values)
    await db.refresh(task)
    return task


async def soft_delete_task(db: AsyncSession, task: Task) -> Task:
    values = {"deleted": True, "updated_at": datetime.now(timezone.utc)}
    await tasks_repo.soft_delete(db, task_id=task.id, values=values)
    await db.refresh(task)
    return task
