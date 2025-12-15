from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, FieldValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = structlog.get_logger()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    API_PREFIX: str = "/v1"
    AI_INTERNAL_TOKEN: str = "ai-internal-token"
    PLANNER_MAX_BATCH: int = 64
    DEFAULT_TIMEZONE: str = "UTC"


auth_header_name = "X-AI-Internal-Token"
settings = Settings()

app = FastAPI(title="LifeMerge AI Planner", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class PlannerTask(BaseModel):
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


class PlannerConflict(BaseModel):
    slot_id: uuid.UUID | None = None
    reason: str
    severity: Literal["info", "warning", "error"] = "warning"
    details: str | None = None
    related_task_id: uuid.UUID | None = None


class PlannerRun(BaseModel):
    plan_request_id: uuid.UUID
    week_start: date | None = None
    work_schedule: list[WorkScheduleEntry] = Field(default_factory=list)
    subscription_status: Literal["pro", "trial", "free"] = "pro"
    tasks: list[PlannerTask] = Field(default_factory=list)
    calendar_events: list[PlannerCalendarEvent] = Field(default_factory=list)
    preferences: PlannerPreferences | None = None
    previous_plan_version: int | None = None
    completed_task_ids: list[uuid.UUID] = Field(default_factory=list)
    rescheduled_task_ids: list[uuid.UUID] = Field(default_factory=list)
    applied_slot_ids: list[uuid.UUID] = Field(default_factory=list)


class BatchPlannerRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    requests: list[PlannerRun]

    @field_validator("requests")
    @classmethod
    def validate_batch_size(cls, requests: list[PlannerRun]):
        if len(requests) > settings.PLANNER_MAX_BATCH:
            raise ValueError(f"batch too large (>{settings.PLANNER_MAX_BATCH})")
        return requests


class PlannerSlotOut(BaseModel):
    slot_id: uuid.UUID
    task_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    start_at: datetime
    end_at: datetime


class PlannerPlanOut(BaseModel):
    plan_request_id: uuid.UUID
    status: str = "ready"
    source: str = "ai"
    slots: list[PlannerSlotOut]
    conflicts: list[PlannerConflict] = Field(default_factory=list)
    version: int = 1


class BatchPlannerResponse(BaseModel):
    plans: list[PlannerPlanOut]
    request_id: str


async def ensure_internal_access(token: str = Header(alias=auth_header_name)) -> None:
    if token != settings.AI_INTERNAL_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(f"{settings.API_PREFIX}/planner/batch-run", response_model=BatchPlannerResponse)
async def batch_run(
    payload: BatchPlannerRequest,
    request: Request,
    _: None = Depends(ensure_internal_access),
):
    plans: list[PlannerPlanOut] = []
    for item in payload.requests:
        slots, conflicts = _generate_slots(
            week_start=item.week_start,
            tasks=item.tasks,
            work_schedule=item.work_schedule,
            preferences=item.preferences,
            calendar_events=item.calendar_events,
            completed_task_ids=item.completed_task_ids,
            rescheduled_task_ids=item.rescheduled_task_ids,
        )
        version = (item.previous_plan_version or 0) + 1
        plan = PlannerPlanOut(
            plan_request_id=item.plan_request_id,
            status="ready",
            slots=slots,
            conflicts=conflicts,
            version=version,
        )
        plans.append(plan)

    log.info(
        "ai_batch_plan_generated",
        batch_size=len(plans),
        request_id=payload.request_id,
        client_request_id=request.headers.get("x-request-id"),
        conflicts=sum(len(plan.conflicts) for plan in plans),
        max_version=max((plan.version for plan in plans), default=1),
    )
    return BatchPlannerResponse(plans=plans, request_id=payload.request_id)


def _generate_slots(
    *,
    week_start: date | None,
    tasks: list[PlannerTask],
    work_schedule: list[WorkScheduleEntry],
    preferences: PlannerPreferences | None,
    calendar_events: list[PlannerCalendarEvent],
    completed_task_ids: list[uuid.UUID],
    rescheduled_task_ids: list[uuid.UUID],
) -> tuple[list[PlannerSlotOut], list[PlannerConflict]]:
    start_date = week_start or datetime.now(timezone.utc).date()
    completed_ids = set(completed_task_ids)
    rescheduled_ids = set(rescheduled_task_ids)
    active_tasks = [task for task in tasks if task.task_id not in completed_ids] if tasks else []

    windows = _build_available_windows(
        start_date=start_date,
        work_schedule=work_schedule,
        preferences=preferences,
        calendar_events=calendar_events,
    )
    slots: list[PlannerSlotOut] = []

    if not active_tasks:
        filler_tasks = [
            PlannerTask(
                task_id=uuid.uuid4(),
                title="Deep work",
                duration_minutes=90,
                status="todo",
            ),
            PlannerTask(
                task_id=uuid.uuid4(),
                title="Focus session",
                duration_minutes=60,
                status="todo",
            ),
            PlannerTask(
                task_id=uuid.uuid4(),
                title="Wrap-up",
                duration_minutes=45,
                status="todo",
            ),
        ]
        active_tasks = filler_tasks

    scheduled_slots, conflicts = _schedule_tasks(
        windows=windows,
        tasks=active_tasks,
        start_date=start_date,
    )
    slots.extend(scheduled_slots)

    conflicts.extend(
        _detect_conflicts(
            slots=slots,
            work_schedule=work_schedule,
            preferences=preferences,
            calendar_events=calendar_events,
            completed_task_ids=completed_ids,
            rescheduled_task_ids=rescheduled_ids,
        )
    )

    return slots, conflicts


def _schedule_tasks(
    *,
    windows: list[tuple[datetime, datetime]],
    tasks: list[PlannerTask],
    start_date: date,
) -> tuple[list[PlannerSlotOut], list[PlannerConflict]]:
    slots: list[PlannerSlotOut] = []
    conflicts: list[PlannerConflict] = []

    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            _clean_datetime(t.due_at) if t.due_at else datetime.combine(start_date, time.max, tzinfo=timezone.utc),
            -(t.priority or 0),
        ),
    )

    available_windows = list(windows)
    for task in sorted_tasks:
        duration = timedelta(minutes=task.duration_minutes)
        deadline = _clean_datetime(task.due_at) if task.due_at else datetime.combine(
            start_date + timedelta(days=7),
            time(hour=23, minute=59),
            tzinfo=timezone.utc,
        )

        placed = False
        for idx, (win_start, win_end) in enumerate(list(available_windows)):
            latest_end = min(win_end, deadline)
            if win_start >= latest_end:
                continue
            slot_start = win_start
            slot_end = slot_start + duration
            if slot_end > latest_end:
                continue

            slot = PlannerSlotOut(
                slot_id=uuid.uuid4(),
                task_id=task.task_id,
                title=task.title,
                description=task.status or "Suggested by AI",
                start_at=slot_start,
                end_at=slot_end,
            )
            slots.append(slot)
            placed = True

            remaining = []
            if slot_end < win_end:
                remaining.append((slot_end, win_end))
            available_windows.pop(idx)
            available_windows[idx:idx] = remaining
            break

        if not placed:
            conflicts.append(
                PlannerConflict(
                    slot_id=None,
                    related_task_id=task.task_id,
                    reason="no_available_window",
                    severity="error",
                    details="No free slot before the task deadline.",
                )
            )

    return slots, conflicts


def _build_available_windows(
    *,
    start_date: date,
    work_schedule: list[WorkScheduleEntry],
    preferences: PlannerPreferences | None,
    calendar_events: list[PlannerCalendarEvent],
) -> list[tuple[datetime, datetime]]:
    schedule = work_schedule or [
        WorkScheduleEntry(day_of_week=day, start_time=time(hour=9), end_time=time(hour=17)) for day in range(0, 5)
    ]
    events = [
        (
            _clean_datetime(event.start_at),
            _clean_datetime(event.end_at),
        )
        for event in calendar_events
    ]

    windows: list[tuple[datetime, datetime]] = []
    for day_offset in range(7):
        if preferences and day_offset in preferences.no_plan_days:
            continue
        day_schedule = [entry for entry in schedule if entry.day_of_week == day_offset]
        for entry in day_schedule:
            start_dt = datetime.combine(start_date + timedelta(days=day_offset), entry.start_time, tzinfo=timezone.utc)
            end_dt = datetime.combine(start_date + timedelta(days=day_offset), entry.end_time, tzinfo=timezone.utc)
            windows.append((start_dt, end_dt))

    if preferences and preferences.breaks:
        processed: list[tuple[datetime, datetime]] = []
        for start_dt, end_dt in windows:
            adjusted = [(start_dt, end_dt)]
            for br in preferences.breaks:
                break_start = datetime.combine(start_dt.date(), br.start_time, tzinfo=timezone.utc)
                break_end = datetime.combine(start_dt.date(), br.end_time, tzinfo=timezone.utc)
                adjusted = _subtract_interval(adjusted, break_start, break_end)
            processed.extend(adjusted)
        windows = processed

    for event_start, event_end in events:
        windows = _subtract_interval(windows, event_start, event_end)

    windows.sort(key=lambda pair: pair[0])
    return windows


def _subtract_interval(
    windows: list[tuple[datetime, datetime]], block_start: datetime, block_end: datetime
) -> list[tuple[datetime, datetime]]:
    updated: list[tuple[datetime, datetime]] = []
    for start_dt, end_dt in windows:
        if block_end <= start_dt or end_dt <= block_start:
            updated.append((start_dt, end_dt))
            continue
        if start_dt < block_start:
            updated.append((start_dt, block_start))
        if block_end < end_dt:
            updated.append((block_end, end_dt))
    return updated


def _clean_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _detect_conflicts(
    *,
    slots: list[PlannerSlotOut],
    work_schedule: list[WorkScheduleEntry],
    preferences: PlannerPreferences | None,
    calendar_events: list[PlannerCalendarEvent],
    completed_task_ids: set[uuid.UUID],
    rescheduled_task_ids: set[uuid.UUID],
) -> list[PlannerConflict]:
    conflicts: list[PlannerConflict] = []

    for slot in slots:
        weekday = slot.start_at.weekday()
        start_time = slot.start_at.time()
        end_time = slot.end_at.time()

        allowed = False
        for entry in work_schedule:
            if entry.day_of_week != weekday:
                continue
            start_window = entry.start_time.replace(tzinfo=None) if entry.start_time.tzinfo else entry.start_time
            end_window = entry.end_time.replace(tzinfo=None) if entry.end_time.tzinfo else entry.end_time
            if start_window <= start_time and end_time <= end_window:
                allowed = True
                break
        if work_schedule and not allowed:
            conflicts.append(
                PlannerConflict(
                    slot_id=slot.slot_id,
                    reason="outside_work_schedule",
                    severity="warning",
                    details="Slot falls outside configured working hours.",
                )
            )

        if preferences:
            if preferences.latest_start_hour is not None and slot.start_at.hour > preferences.latest_start_hour:
                conflicts.append(
                    PlannerConflict(
                        slot_id=slot.slot_id,
                        reason="after_hours",
                        severity="warning",
                        details="Starts later than user preference allows.",
                    )
                )
            if weekday in preferences.no_plan_days:
                conflicts.append(
                    PlannerConflict(
                        slot_id=slot.slot_id,
                        reason="no_plan_day",
                        severity="info",
                        details="User requested no planning on this day.",
                    )
                )
            for br in preferences.breaks:
                if br.start_time <= start_time < br.end_time or br.start_time < end_time <= br.end_time:
                    conflicts.append(
                        PlannerConflict(
                            slot_id=slot.slot_id,
                            reason="break_time",
                            severity="warning",
                            details="Overlaps with a planned break.",
                        )
                    )

        for event in calendar_events:
            if event.start_at < slot.end_at and slot.start_at < event.end_at:
                conflicts.append(
                    PlannerConflict(
                        slot_id=slot.slot_id,
                        reason="calendar_conflict",
                        severity="error",
                        details=f"Overlaps with calendar event {event.title}",
                    )
                )

        if slot.task_id in completed_task_ids:
            conflicts.append(
                PlannerConflict(
                    slot_id=slot.slot_id,
                    related_task_id=slot.task_id,
                    reason="task_already_completed",
                    severity="info",
                    details="Task already completed before planning.",
                )
            )
        if slot.task_id in rescheduled_task_ids:
            conflicts.append(
                PlannerConflict(
                    slot_id=slot.slot_id,
                    related_task_id=slot.task_id,
                    reason="task_rescheduled",
                    severity="warning",
                    details="Task has been rescheduled and may need re-planning.",
                )
            )

    return conflicts
