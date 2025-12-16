from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from backend.domain.domain_events.task_created import TaskCreated
from backend.domain.entities.task import Task
from backend.domain.interfaces.message_bus import MessageBus
from backend.domain.interfaces.repositories.task_repository import TaskRepository


@dataclass
class CreateTaskRequest:
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    priority: Optional[int] = None
    estimated_minutes: Optional[int] = None
    energy_level: Optional[int] = None
    goal_id: Optional[uuid.UUID] = None


class CreateTask:
    def __init__(self, task_repo: TaskRepository, message_bus: MessageBus):
        self._task_repo = task_repo
        self._bus = message_bus

    async def execute(self, request: CreateTaskRequest) -> Task:
        task = Task.create(
            user_id=request.user_id,
            title=request.title,
            description=request.description,
            priority=request.priority,
            estimated_minutes=request.estimated_minutes,
            energy_level=request.energy_level,
            goal_id=request.goal_id,
        )
        task = await self._task_repo.add(task)
        await self._bus.publish(TaskCreated(task_id=task.id, user_id=task.user_id))
        return task
