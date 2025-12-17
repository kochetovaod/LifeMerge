from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SubtaskOut(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    title: str
    done: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted: bool = False

    class Config:
        from_attributes = True


class SubtaskCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    request_id: str


class SubtaskUpdateIn(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    done: bool | None = None
    updated_at: datetime | None = None
    request_id: str


class SubtaskListOut(BaseModel):
    items: list[SubtaskOut]
    next_cursor: str | None = None
    request_id: str
