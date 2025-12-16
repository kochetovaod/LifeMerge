from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SubscriptionChanged:
    user_id: uuid.UUID
    is_pro: bool
    occurred_at: datetime = datetime.now(timezone.utc)
