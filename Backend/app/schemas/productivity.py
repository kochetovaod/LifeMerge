from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GoalCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    target_date: date | None = None


class GoalUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    target_date: date | None = None


class GoalOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    target_date: date | None = None
    progress: float = Field(ge=0, le=1)
    tasks_total: int
    tasks_completed: int


class GoalProgressOut(BaseModel):
    id: uuid.UUID
    percent_complete: float = Field(ge=0, le=100)
    tasks_total: int
    tasks_completed: int
    updated_at: datetime


class TaskLink(BaseModel):
    id: uuid.UUID
    title: str
    status: Literal["todo", "in_progress", "done", "moved", "skipped"]


class CalendarEventIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    start_at: datetime
    end_at: datetime
    recurrence: str | None = Field(
        default=None, description="Natural language rule e.g. daily, weekly on Monday"
    )
    parallel_with: list[uuid.UUID] = Field(default_factory=list)

    @field_validator("end_at")
    @classmethod
    def validate_range(cls, end_at: datetime, values):
        start_at: datetime | None = values.data.get("start_at")
        if start_at and end_at <= start_at:
            raise ValueError("end_at must be after start_at")
        return end_at


class CalendarEventUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    start_at: datetime | None = None
    end_at: datetime | None = None
    recurrence: str | None = None
    parallel_with: list[uuid.UUID] | None = None


class CalendarEventOut(BaseModel):
    id: uuid.UUID
    title: str
    start_at: datetime
    end_at: datetime
    recurrence: str | None = None
    parallel_with: list[uuid.UUID] = Field(default_factory=list)


class InboxCreateIn(BaseModel):
    note: str = Field(min_length=1, max_length=500)


class InboxConvertIn(BaseModel):
    target: Literal["task", "event", "goal"]
    title: str


class InboxItemOut(BaseModel):
    id: uuid.UUID
    note: str
    created_at: datetime
    converted_to: str | None = None


class FinanceTransactionIn(BaseModel):
    type: Literal["income", "expense"]
    amount: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    category: str
    occurred_at: datetime
    recurring: bool = False


class FinanceTransactionUpdateIn(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    category: str | None = None
    occurred_at: datetime | None = None
    recurring: bool | None = None


class FinanceTransactionOut(BaseModel):
    id: uuid.UUID
    type: Literal["income", "expense"]
    amount: float
    currency: str
    category: str
    occurred_at: datetime
    recurring: bool = False


class FinanceSummaryOut(BaseModel):
    month: str
    income_total: float
    expense_total: float
    net: float
    budgets: dict[str, float]


class BudgetIn(BaseModel):
    month: str = Field(description="YYYY-MM")
    amount: float = Field(gt=0)


class BudgetOut(BaseModel):
    month: str
    amount: float
    limited: bool


class NotificationTriggerIn(BaseModel):
    entity: Literal["task", "event", "finance"]
    entity_id: uuid.UUID
    lead_minutes: int = Field(ge=0, le=1440)
    remind_at: datetime


class NotificationTriggerOut(BaseModel):
    id: uuid.UUID
    entity: str
    entity_id: uuid.UUID
    lead_minutes: int
    remind_at: datetime
    channel: Literal["push", "email"]


class DigestPreviewOut(BaseModel):
    cadence: Literal["daily", "weekly"]
    items: list[str]


class SyncStatusOut(BaseModel):
    queue_depth: int
    last_synced_at: datetime | None
    pending_entities: list[str]
    status: Literal["idle", "syncing", "error"]

