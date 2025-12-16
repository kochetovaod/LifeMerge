from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Literal


def _ensure_time(value: time | str) -> time:
    if isinstance(value, time):
        return value
    return time.fromisoformat(value)


def _ensure_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _ensure_uuid(value: uuid.UUID | str | None) -> uuid.UUID | None:
    if value is None or isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


@dataclass
class WorkScheduleEntry:
    day_of_week: int
    start_time: time
    end_time: time

    def __post_init__(self) -> None:
        self.start_time = _ensure_time(self.start_time)
        self.end_time = _ensure_time(self.end_time)
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if self.day_of_week < 0 or self.day_of_week > 6:
            raise ValueError("day_of_week must be between 0 and 6")

    @classmethod
    def from_dict(cls, data: dict) -> "WorkScheduleEntry":
        return cls(
            day_of_week=int(data.get("day_of_week")),
            start_time=_ensure_time(data.get("start_time")),
            end_time=_ensure_time(data.get("end_time")),
        )


@dataclass
class PlannerBreak:
    start_time: time
    end_time: time

    def __post_init__(self) -> None:
        self.start_time = _ensure_time(self.start_time)
        self.end_time = _ensure_time(self.end_time)
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")

    @classmethod
    def from_dict(cls, data: dict) -> "PlannerBreak":
        return cls(start_time=_ensure_time(data.get("start_time")), end_time=_ensure_time(data.get("end_time")))


@dataclass
class PlannerPreferences:
    latest_start_hour: int | None = None
    breaks: list[PlannerBreak] = field(default_factory=list)
    no_plan_days: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.latest_start_hour is not None and (self.latest_start_hour < 0 or self.latest_start_hour > 23):
            raise ValueError("latest_start_hour must be between 0 and 23")
        self.breaks = [br if isinstance(br, PlannerBreak) else PlannerBreak.from_dict(br) for br in self.breaks]
        self.no_plan_days = {int(day) for day in self.no_plan_days}
        for day in self.no_plan_days:
            if day < 0 or day > 6:
                raise ValueError("no_plan_days must contain values between 0 and 6")

    @classmethod
    def from_dict(cls, data: dict | None) -> "PlannerPreferences" | None:
        if data is None:
            return None
        return cls(
            latest_start_hour=data.get("latest_start_hour"),
            breaks=data.get("breaks") or [],
            no_plan_days=set(data.get("no_plan_days") or []),
        )


@dataclass
class PlannerSlot:
    slot_id: uuid.UUID
    task_id: uuid.UUID | None
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime

    def __post_init__(self) -> None:
        self.slot_id = _ensure_uuid(self.slot_id) or uuid.uuid4()
        self.task_id = _ensure_uuid(self.task_id)
        self.start_at = _ensure_datetime(self.start_at)
        self.end_at = _ensure_datetime(self.end_at)
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")

    @property
    def duration_minutes(self) -> int:
        return int((self.end_at - self.start_at).total_seconds() // 60)

    @classmethod
    def from_dict(cls, data: dict) -> "PlannerSlot":
        return cls(
            slot_id=_ensure_uuid(data.get("slot_id")) or uuid.uuid4(),
            task_id=_ensure_uuid(data.get("task_id")),
            title=data.get("title") or "",
            description=data.get("description"),
            start_at=_ensure_datetime(data.get("start_at")),
            end_at=_ensure_datetime(data.get("end_at")),
        )


@dataclass
class PlannerConflict:
    slot_id: uuid.UUID | None
    reason: str
    severity: Literal["info", "warning", "error"] = "warning"
    details: str | None = None
    related_task_id: uuid.UUID | None = None

    def __post_init__(self) -> None:
        self.slot_id = _ensure_uuid(self.slot_id)
        self.related_task_id = _ensure_uuid(self.related_task_id)

    @classmethod
    def from_dict(cls, data: dict) -> "PlannerConflict":
        return cls(
            slot_id=_ensure_uuid(data.get("slot_id")),
            reason=data.get("reason") or "",
            severity=data.get("severity", "warning"),
            details=data.get("details"),
            related_task_id=_ensure_uuid(data.get("related_task_id")),
        )
