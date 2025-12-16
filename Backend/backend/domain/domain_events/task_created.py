from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class TaskCreated:
    task_id: uuid.UUID
    user_id: uuid.UUID
    occurred_at: datetime = datetime.now(timezone.utc)
