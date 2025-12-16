from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Literal, Optional


@dataclass
class WorkScheduleEntry:
    day_of_week: int
    start_time: time
    end_time: time


@dataclass
class PlannerBreak:
    start_time: time
    end_time: time


@dataclass
class PlannerPreferences:
    latest_start_hour: Optional[int] = None
    breaks: list[PlannerBreak] = field(default_factory=list)
    no_plan_days: set[int] = field(default_factory=set)


@dataclass
class PlannerTask:
    task_id: uuid.UUID
    title: str
    duration_minutes: int
    due_at: Optional[datetime] = None
    priority: Optional[int] = None
    status: Optional[str] = None


@dataclass
class PlannerCalendarEvent:
    event_id: uuid.UUID
    title: str
    start_at: datetime
    end_at: datetime


@dataclass
class PlannerSlot:
    slot_id: uuid.UUID
    task_id: Optional[uuid.UUID]
    title: str
    description: Optional[str]
    start_at: datetime
    end_at: datetime


@dataclass
class PlannerConflict:
    slot_id: Optional[uuid.UUID]
    reason: str
    severity: str = "warning"
    details: Optional[str] = None
    related_task_id: Optional[uuid.UUID] = None


@dataclass
class PlannerRunCommand:
    """Команда для запуска планировщика"""
    request_id: str
    user_id: uuid.UUID
    week_start: Optional[date]
    work_schedule: list[WorkScheduleEntry]
    subscription_status: str
    tasks: list[PlannerTask]
    calendar_events: list[PlannerCalendarEvent]
    preferences: Optional[PlannerPreferences]
    previous_plan_version: Optional[int] = None
    completed_task_ids: list[uuid.UUID] = field(default_factory=list)
    rescheduled_task_ids: list[uuid.UUID] = field(default_factory=list)
    applied_slot_ids: list[uuid.UUID] = field(default_factory=list)


@dataclass
class PlannerRunResult:
    """Результат запуска планировщика"""
    plan_request_id: uuid.UUID
    status: str
    message: Optional[str] = None
    trial_offer: Optional[str] = None
    source: Optional[str] = None


@dataclass
class PlannerPlan:
    """Представление плана в приложении"""
    plan_request_id: uuid.UUID
    status: str
    version: int = 1
    source: str = "ai"
    slots: list[PlannerSlot] = field(default_factory=list)
    conflicts: list[PlannerConflict] = field(default_factory=list)


@dataclass
class PlannerDecisionCommand:
    """Команда для принятия решения по плану"""
    request_id: str
    plan_request_id: uuid.UUID
    user_id: uuid.UUID
    decision: Literal["accept", "decline"]
    accepted_slot_ids: Optional[list[uuid.UUID]] = None
    edits: list[dict] = field(default_factory=list)


@dataclass
class PlannerDecisionResult:
    """Результат принятия решения"""
    plan_request_id: uuid.UUID
    status: str
    created_task_ids: list[uuid.UUID]
    updated_task_ids: list[uuid.UUID]
    version: int = 1