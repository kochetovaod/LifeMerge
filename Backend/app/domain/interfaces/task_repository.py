from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Protocol, Sequence


class ITaskRepository(Protocol):
    async def find_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Any | None:
        """Return a task by id for a given user, or None if not found."""

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
    ) -> tuple[Sequence[Any], str | None]:
        """Return a list of tasks for a user and the next cursor, if any."""

    async def save(self, task: Any) -> Any:
        """Persist a task instance and return it."""

    async def update_values(self, task_id: uuid.UUID, values: dict) -> None:
        """Apply partial updates to a task identified by id."""

    async def soft_delete(self, task_id: uuid.UUID, values: dict) -> None:
        """Soft delete a task using the provided values."""

    async def refresh(self, task: Any) -> None:
        """Refresh a task instance from the data store."""
