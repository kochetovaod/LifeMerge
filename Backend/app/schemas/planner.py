from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Literal

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


class PlannerRunIn(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    week_start: date | None = None
    work_schedule: list[WorkScheduleEntry] = Field(default_factory=list)
    subscription_status: Literal["pro", "trial", "free"]


class PlannerRunOut(BaseModel):
    plan_request_id: uuid.UUID
    status: str
    request_id: str


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


class PlannerPlanOut(BaseModel):
    plan_request_id: uuid.UUID
    status: str
    slots: list[PlannerSlot]
    request_id: str


class PlannerDecisionIn(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    decision: Literal["accept", "decline"]
    accepted_slot_ids: list[uuid.UUID] | None = None


class PlannerDecisionOut(BaseModel):
    plan_request_id: uuid.UUID
    status: str
    created_task_ids: list[uuid.UUID]
    updated_task_ids: list[uuid.UUID]
    request_id: str
