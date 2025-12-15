from __future__ import annotations

import uuid
from datetime import date, time
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
    subscription_status: Literal["pro", "trial"]


class PlannerRunOut(BaseModel):
    plan_request_id: uuid.UUID
    status: str
    request_id: str
