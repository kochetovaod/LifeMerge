from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.task_repository import ITaskRepository
from app.models.task import Task
from app.repositories import tasks_repo


class SQLTaskRepository(ITaskRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        return await tasks_repo.get_by_id(self._session, task_id=task_id, user_id=user_id)

    async def find_by_user(
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
        return await tasks_repo.list(
            self._session,
            user_id=user_id,
            status=status,
            goal_id=goal_id,
            due_from=due_from,
            due_to=due_to,
            cursor=cursor,
            limit=limit,
        )

    async def save(self, task: Task) -> Task:
        return await tasks_repo.create(self._session, task)

    async def update_values(self, task_id: uuid.UUID, values: dict) -> None:
        await tasks_repo.patch(self._session, task_id=task_id, values=values)

    async def soft_delete(self, task_id: uuid.UUID, values: dict) -> None:
        await tasks_repo.soft_delete(self._session, task_id=task_id, values=values)

    async def refresh(self, task: Task) -> None:
        await self._session.refresh(task)
