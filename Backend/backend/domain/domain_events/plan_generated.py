from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class PlanGenerated:
    plan_id: uuid.UUID
    user_id: uuid.UUID
    version: int
    occurred_at: datetime = datetime.now(timezone.utc)
