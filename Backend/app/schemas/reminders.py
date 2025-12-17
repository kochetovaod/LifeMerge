from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReminderCreateIn(BaseModel):
    remind_at: datetime
    request_id: str


class ReminderOut(BaseModel):
    id: uuid.UUID
    entity: str
    entity_id: uuid.UUID
    trigger_at: datetime
    enabled: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted: bool = False

    class Config:
        from_attributes = True


class ReminderListOut(BaseModel):
    items: list[ReminderOut]
    next_cursor: str | None = None
    request_id: str
