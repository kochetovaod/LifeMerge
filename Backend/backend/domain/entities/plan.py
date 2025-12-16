from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, List

from backend.domain.entities.task import Task


@dataclass
class Plan:
    """Aggregate root capturing a generated plan for a user."""

    id: uuid.UUID
    user_id: uuid.UUID
    tasks: List[Task] = field(default_factory=list)
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def new(cls, *, user_id: uuid.UUID, tasks: Iterable[Task] | None = None, version: int = 1) -> "Plan":
        return cls(id=uuid.uuid4(), user_id=user_id, tasks=list(tasks or []), version=version)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def replace_tasks(self, tasks: Iterable[Task]) -> None:
        self.tasks = list(tasks)
