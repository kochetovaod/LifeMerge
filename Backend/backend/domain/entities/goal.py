from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Goal:
    """Aggregate root representing a user goal."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    progress: float = 0.0
    tasks_total: int = 0
    tasks_completed: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted: bool = False

    @classmethod
    def new(cls, *, user_id: uuid.UUID, title: str, description: str | None = None) -> "Goal":
        return cls(id=uuid.uuid4(), user_id=user_id, title=title, description=description)

    def track_completion(self, completed: bool) -> None:
        self.tasks_total += 1
        if completed:
            self.tasks_completed += 1
        self.progress = 0.0 if self.tasks_total == 0 else self.tasks_completed / self.tasks_total
        self.updated_at = datetime.now(timezone.utc)
