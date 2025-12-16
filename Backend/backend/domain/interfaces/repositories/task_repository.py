from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Iterable, Optional

from backend.domain.entities.task import Task


class TaskRepository(ABC):
    @abstractmethod
    async def add(self, task: Task) -> Task:
        raise NotImplementedError

    @abstractmethod
    async def get(self, task_id: uuid.UUID, *, user_id: uuid.UUID) -> Optional[Task]:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(self, user_id: uuid.UUID) -> Iterable[Task]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, task: Task) -> None:
        raise NotImplementedError
