from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from backend.domain.value_objects.email import Email


@dataclass
class User:
    """Aggregate root for platform users."""

    id: uuid.UUID
    email: Email
    full_name: Optional[str] = None
    timezone: str = "UTC"
    is_pro: bool = False
    trial_started_at: datetime | None = field(default_factory=lambda: datetime.now(timezone.utc))
    trial_ends_at: datetime | None = None

    def start_trial(self, days: int) -> None:
        now = datetime.now(timezone.utc)
        self.trial_started_at = now
        self.trial_ends_at = now + timedelta(days=days)

    def upgrade_to_pro(self) -> None:
        self.is_pro = True
        self.trial_ends_at = None

    def rename(self, full_name: str) -> None:
        self.full_name = full_name
