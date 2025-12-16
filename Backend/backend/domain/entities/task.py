from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from backend.domain.value_objects.time_slot import TimeSlot


@dataclass
class Task:
    """Aggregate root for user tasks."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str = "todo"
    priority: Optional[int] = None
    estimated_minutes: Optional[int] = None
    energy_level: Optional[int] = None
    goal_id: Optional[uuid.UUID] = None
    due_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted: bool = False

    @classmethod
    def create(
        cls,
        *,
        user_id: uuid.UUID,
        title: str,
        description: str | None = None,
        priority: int | None = None,
        estimated_minutes: int | None = None,
        energy_level: int | None = None,
        goal_id: uuid.UUID | None = None,
        due_at: datetime | None = None,
    ) -> "Task":
        return cls(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            estimated_minutes=estimated_minutes,
            energy_level=energy_level,
            goal_id=goal_id,
            due_at=due_at,
        )

    def assign_goal(self, goal_id: uuid.UUID | None) -> None:
        self.goal_id = goal_id
        self.touch()

    def schedule(self, slot: TimeSlot) -> None:
        self.due_at = slot.start
        self.touch()

    def mark_done(self) -> None:
        self.status = "done"
        self.touch()

    def archive(self) -> None:
        self.deleted = True
        self.touch()

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
