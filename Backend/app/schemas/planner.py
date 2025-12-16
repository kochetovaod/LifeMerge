from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Any, Literal

from pydantic import BaseModel, Field, FieldValidationInfo, field_validator


class WorkScheduleEntry(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @field_validator("end_time")
    @classmethod
    def validate_range(cls, end_time: time, info: FieldValidationInfo):
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class PlannerBreak(BaseModel):
    start_time: time
    end_time: time

    @field_validator("end_time")
    @classmethod
    def validate_range(cls, end_time: time, info: FieldValidationInfo):
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class PlannerPreferences(BaseModel):
    latest_start_hour: int | None = Field(default=None, ge=0, le=23)
    breaks: list[PlannerBreak] = Field(default_factory=list)
    no_plan_days: set[int] = Field(default_factory=set)

    @field_validator("no_plan_days")
    @classmethod
    def validate_days(cls, value: set[int]):
        for day in value:
            if day < 0 or day > 6:
                raise ValueError("no_plan_days must contain values between 0 and 6")
        return value


class PlannerTaskIn(BaseModel):
    task_id: uuid.UUID
    title: str
    duration_minutes: int = Field(gt=0, le=24 * 60)
    due_at: datetime | None = None
    priority: int | None = None
    status: Literal["todo", "in_progress", "done", "moved", "skipped"] | None = None


class PlannerCalendarEvent(BaseModel):
    event_id: uuid.UUID
    title: str
    start_at: datetime
    end_at: datetime

    @field_validator("end_at")
    @classmethod
    def validate_range(cls, end_at: datetime, info: FieldValidationInfo):
        start_at = info.data.get("start_at")
        if start_at and end_at <= start_at:
            raise ValueError("end_at must be after start_at")
        return end_at


class PlannerRunIn(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    week_start: date | None = None
    work_schedule: list[WorkScheduleEntry] = Field(default_factory=list)
    subscription_status: Literal["pro", "trial", "free"]
    tasks: list[PlannerTaskIn] = Field(default_factory=list)
    calendar_events: list[PlannerCalendarEvent] = Field(default_factory=list)
    preferences: PlannerPreferences | None = None
    previous_plan_version: int | None = None
    completed_task_ids: list[uuid.UUID] = Field(default_factory=list)
    rescheduled_task_ids: list[uuid.UUID] = Field(default_factory=list)
    applied_slot_ids: list[uuid.UUID] = Field(default_factory=list)
    strategy: str | None = None
    strategy_options: dict[str, Any] | None = None


class PlannerReplanIn(PlannerRunIn):
    """Allows re-running the planner for an existing request."""


class PlannerRunOut(BaseModel):
    plan_request_id: uuid.UUID | None
    status: str
    request_id: str
    message: str | None = None
    trial_offer: str | None = None
    source: str | None = None


class PlannerSlot(BaseModel):
    slot_id: uuid.UUID
    task_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    start_at: datetime
    end_at: datetime

    @property
    def duration_minutes(self) -> int:
        return int((self.end_at - self.start_at).total_seconds() // 60)


class PlannerConflict(BaseModel):
    slot_id: uuid.UUID | None = None
    reason: str
    severity: Literal["info", "warning", "error"] = "warning"
    details: str | None = None
    related_task_id: uuid.UUID | None = None


class PlannerPlanOut(BaseModel):
    plan_request_id: uuid.UUID
    status: str
    version: int = 1
    source: str = "ai"
    slots: list[PlannerSlot]
    conflicts: list[PlannerConflict] = Field(default_factory=list)
    request_id: str


class PlannerSlotEdit(BaseModel):
    slot_id: uuid.UUID
    title: str | None = None
    description: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None


class PlannerDecisionIn(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    decision: Literal["accept", "decline"]
    accepted_slot_ids: list[uuid.UUID] | None = None
    edits: list[PlannerSlotEdit] = Field(default_factory=list)


class PlannerDecisionOut(BaseModel):
    plan_request_id: uuid.UUID
    status: str
    created_task_ids: list[uuid.UUID]
    updated_task_ids: list[uuid.UUID]
    request_id: str
    version: int = 1
