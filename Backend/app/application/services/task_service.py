from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.domain.interfaces.task_repository import ITaskRepository
from app.models.task import Task
from app.schemas.tasks import ALLOWED_STATUSES


class TaskService:
    def __init__(self, repo: ITaskRepository) -> None:
        self._repo = repo

    async def get_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        return await self._repo.find_by_id(task_id, user_id)

    async def list_tasks(
        self,
        user_id: uuid.UUID,
        *,
        status: str | None = None,
        goal_id: uuid.UUID | None = None,
        due_from: datetime | None = None,
        due_to: datetime | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Task], str | None]:
        tasks, next_cursor = await self._repo.find_by_user(
            user_id,
            status=status,
            goal_id=goal_id,
            due_from=due_from,
            due_to=due_to,
            cursor=cursor,
            limit=limit,
        )
        return list(tasks), next_cursor

    async def create_task(self, user_id: uuid.UUID, data: dict) -> Task:
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
        saved = await self._repo.save(task)
        await self._repo.refresh(saved)
        return saved

    async def update_task(
        self, task: Task, patch: dict, expected_updated_at: datetime | None
    ) -> Task:
        if expected_updated_at:
            a = task.updated_at.replace(tzinfo=timezone.utc)
            b = expected_updated_at.replace(tzinfo=timezone.utc)
            if a != b:
                raise ValueError("conflict")

        values = {k: v for k, v in patch.items() if v is not None and k not in {"request_id", "updated_at"}}
        status = values.get("status")
        if status and status not in ALLOWED_STATUSES:
            raise ValueError("invalid_status")
        values["updated_at"] = datetime.now(timezone.utc)

        await self._repo.update_values(task_id=task.id, values=values)
        await self._repo.refresh(task)
        return task

    async def soft_delete_task(db: AsyncSession, task: Task) -> Task:
        values = {"deleted": True, "updated_at": datetime.now(timezone.utc)}
        await tasks_repo.soft_delete(db, task_id=task.id, values=values)
        await db.refresh(task)
        return task