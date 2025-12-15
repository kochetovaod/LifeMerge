from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

ALLOWED_STATUSES = {"todo", "in_progress", "done", "deferred"}


class TaskOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    status: str
    priority: int | None = None
    estimated_minutes: int | None = None
    energy_level: int | None = None
    goal_id: uuid.UUID | None = None
    due_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted: bool = False

    class Config:
        from_attributes = True


class TaskCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    goal_id: uuid.UUID | None = None
    due_at: datetime | None = None
    priority: int | None = None
    estimated_minutes: int | None = None
    energy_level: int | None = None
    request_id: str = Field(min_length=1, max_length=128)

    @field_validator("priority", "estimated_minutes", "energy_level")
    @classmethod
    def non_negative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("Value must be non-negative")
        return value


class TaskUpdateIn(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    description: str | None = None
    goal_id: uuid.UUID | None = None
    due_at: datetime | None = None
    priority: int | None = None
    estimated_minutes: int | None = None
    energy_level: int | None = None
    status: str | None = None
    updated_at: datetime | None = None
    request_id: str = Field(min_length=1, max_length=128)

    @field_validator("priority", "estimated_minutes", "energy_level")
    @classmethod
    def non_negative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("Value must be non-negative")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_STATUSES:
            raise ValueError("Unsupported status")
        return value


class TaskDeleteIn(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)


class TaskListOut(BaseModel):
    items: list[TaskOut]
    next_cursor: str | None = None
    request_id: str
