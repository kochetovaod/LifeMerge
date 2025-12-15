from __future__ import annotations

from datetime import time

from pydantic import BaseModel, Field, FieldValidationInfo, field_validator


class QuietHoursRule(BaseModel):
    start_time: time
    end_time: time

    @field_validator("end_time")
    @classmethod
    def validate_range(cls, end_time: time, info: FieldValidationInfo) -> time:
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class BreakRule(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @field_validator("end_time")
    @classmethod
    def validate_range(cls, end_time: time, info: FieldValidationInfo) -> time:
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class AiRulesBase(BaseModel):
    quiet_hours: list[QuietHoursRule] = Field(default_factory=list)
    breaks: list[BreakRule] = Field(default_factory=list)
    blocked_days: list[int] = Field(default_factory=list)

    @field_validator("blocked_days")
    @classmethod
    def validate_blocked_days(cls, value: list[int]) -> list[int]:
        for day in value:
            if day < 0 or day > 6:
                raise ValueError("blocked_days must contain values between 0 and 6")
        return sorted(set(value))


class AiRulesUpsertIn(AiRulesBase):
    request_id: str = Field(min_length=1, max_length=128)


class AiRulesOut(AiRulesBase):
    request_id: str

    class Config:
        from_attributes = True
