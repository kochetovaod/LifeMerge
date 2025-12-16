from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task as TaskModel
from backend.domain.entities.task import Task
from backend.domain.interfaces.repositories.task_repository import TaskRepository
from backend.infrastructure.persistence import mappers


class SqlAlchemyTaskRepository(TaskRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, task: Task) -> Task:
        model = mappers.task_to_model(task)
        self._session.add(model)
        await self._session.flush()
        return mappers.model_to_task(model)

    async def get(self, task_id: uuid.UUID, *, user_id: uuid.UUID) -> Task | None:
        res = await self._session.execute(
            select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user_id, TaskModel.deleted == False)  # noqa: E712
        )
        row = res.scalar_one_or_none()
        return mappers.model_to_task(row) if row else None

    async def list_for_user(self, user_id: uuid.UUID) -> Iterable[Task]:
        res = await self._session.execute(
            select(TaskModel).where(TaskModel.user_id == user_id, TaskModel.deleted == False).order_by(TaskModel.updated_at.desc())  # noqa: E712
        )
        return [mappers.model_to_task(row) for row in res.scalars().all()]

    async def save(self, task: Task) -> None:
        existing = await self.get(task.id, user_id=task.user_id)
        if not existing:
            await self.add(task)
            return
        await self._session.merge(mappers.task_to_model(task))
