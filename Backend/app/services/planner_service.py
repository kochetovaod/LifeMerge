from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

import httpx
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import log
from app.repositories import tasks_repo
from app.schemas.planner import (
    PlannerConflict,
    PlannerPreferences,
    PlannerSlot,
    PlannerSlotEdit,
    PlannerTaskIn,
)
from app.services.events import publish_event
from app.services.observability import log_ai_request
from app.services.tasks_service import create_task, update_task

_GENERATED_PLANS: dict[uuid.UUID, dict[str, Any]] = {}


async def enqueue_planner_run(
    *, request: Request, user_id: uuid.UUID, payload: dict[str, Any], plan_request_id: uuid.UUID | None = None
) -> dict[str, Any]:
    plan_request_id = plan_request_id or uuid.uuid4()
    existing_plan = _GENERATED_PLANS.get(plan_request_id)

    publish_event(
        name="AI_Planner_Requested",
        request_id=request.state.request_id,
        user_id=str(user_id),
        payload={"plan_request_id": str(plan_request_id), **payload},
    )

    plan = await _request_plan_from_ai(request=request, plan_request_id=plan_request_id, payload=payload)
    slots = plan["slots"]
    conflicts: list[PlannerConflict] = plan.get("conflicts", [])
    version: int = plan.get("version", 1)
    source = plan.get("source", "ai")
    new_plan = {
        "user_id": user_id,
        "status": plan["status"],
        "slots": slots,
        "conflicts": conflicts,
        "version": version,
        "created_at": existing_plan.get("created_at") if existing_plan else datetime.now(timezone.utc),
        "applied_slot_ids": payload.get("applied_slot_ids", []),
        "history": list(existing_plan.get("history", [])) if existing_plan else [],
        "source": source,
    }
    _append_history(new_plan, status=plan["status"])
    _GENERATED_PLANS[plan_request_id] = new_plan

    log.info(
        "ai_planner_requested",
        request_id=request.state.request_id,
        user_id=str(user_id),
        plan_request_id=str(plan_request_id),
        subscription_status=payload.get("subscription_status"),
        version=version,
        conflicts=len(conflicts),
    )

    return {"plan_request_id": plan_request_id, "status": "ready", "source": source}


def _generate_slots(
    *,
    week_start: str | None,
    tasks: list[dict[str, Any]] | None = None,
    work_schedule: list[dict[str, Any]] | None = None,
    preferences: PlannerPreferences | None = None,
    calendar_events: list[dict[str, Any]] | None = None,
    completed_task_ids: list[str] | None = None,
    rescheduled_task_ids: list[str] | None = None,
) -> tuple[list[PlannerSlot], list[PlannerConflict]]:
    if preferences and isinstance(preferences, dict):
        try:
            preferences = PlannerPreferences.model_validate(preferences)
        except Exception:  # noqa: BLE001
            preferences = None
    if week_start:
        try:
            start_date = date.fromisoformat(week_start)
        except ValueError:
            start_date = datetime.now(timezone.utc).date()
    else:
        start_date = datetime.now(timezone.utc).date()

    completed_ids = set(completed_task_ids or [])
    rescheduled_ids = set(rescheduled_task_ids or [])
    parsed_tasks: list[PlannerTaskIn] = []
    for raw in tasks or []:
        try:
            parsed_tasks.append(PlannerTaskIn.model_validate(raw))
        except Exception:  # noqa: BLE001
            continue
    active_tasks = [task for task in parsed_tasks if str(task.task_id) not in completed_ids]

    windows = _build_available_windows(
        start_date=start_date,
        work_schedule=work_schedule or [],
        preferences=preferences,
        calendar_events=calendar_events or [],
    )
    slots: list[PlannerSlot] = []

    if not active_tasks:
        filler_tasks = [
            PlannerTaskIn(
                task_id=uuid.uuid4(),
                title="Deep work",
                duration_minutes=90,
                status="todo",
            ),
            PlannerTaskIn(
                task_id=uuid.uuid4(),
                title="Focus session",
                duration_minutes=60,
                status="todo",
            ),
            PlannerTaskIn(
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
            work_schedule=work_schedule or [],
            preferences=preferences,
            calendar_events=calendar_events or [],
            completed_task_ids=list(completed_ids),
            rescheduled_task_ids=list(rescheduled_ids),
        )
    )

    return slots, conflicts


def _schedule_tasks(
    *, windows: list[tuple[datetime, datetime]], tasks: list[PlannerTaskIn], start_date: date
) -> tuple[list[PlannerSlot], list[PlannerConflict]]:
    slots: list[PlannerSlot] = []
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

            slots.append(
                PlannerSlot(
                    slot_id=uuid.uuid4(),
                    task_id=task.task_id,
                    title=task.title,
                    description=task.status or "Suggested by AI",
                    start_at=slot_start,
                    end_at=slot_end,
                )
            )
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
    work_schedule: list[dict[str, Any]],
    preferences: PlannerPreferences | None,
    calendar_events: list[dict[str, Any]],
) -> list[tuple[datetime, datetime]]:
    schedule = work_schedule or [
        {"day_of_week": day, "start_time": time(hour=9), "end_time": time(hour=17)} for day in range(0, 5)
    ]
    events = []
    for event in calendar_events:
        start = event.get("start_at")
        end = event.get("end_at")
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            end = datetime.fromisoformat(end)
        if start and end:
            events.append((_clean_datetime(start), _clean_datetime(end)))

    windows: list[tuple[datetime, datetime]] = []
    for day_offset in range(7):
        if preferences and day_offset in preferences.no_plan_days:
            continue
        day_schedule = [entry for entry in schedule if entry.get("day_of_week") == day_offset]
        for entry in day_schedule:
            start_time = entry.get("start_time")
            end_time = entry.get("end_time")
            if isinstance(start_time, str):
                start_time = time.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = time.fromisoformat(end_time)
            if not start_time or not end_time:
                continue
            start_dt = datetime.combine(start_date + timedelta(days=day_offset), start_time, tzinfo=timezone.utc)
            end_dt = datetime.combine(start_date + timedelta(days=day_offset), end_time, tzinfo=timezone.utc)
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


def _apply_slot_edits(slots: list[PlannerSlot], edits: list[PlannerSlotEdit]) -> list[PlannerSlot]:
    edits_map = {item.slot_id: item for item in edits}
    updated: list[PlannerSlot] = []

    for slot in slots:
        edit = edits_map.get(slot.slot_id)
        if not edit:
            updated.append(slot)
            continue

        start_at = edit.start_at or slot.start_at
        end_at = edit.end_at or slot.end_at
        if end_at <= start_at:
            log.warning(
                "planner_edit_invalid_range",
                slot_id=str(slot.slot_id),
                request_start=start_at.isoformat(),
                request_end=end_at.isoformat(),
            )
            updated.append(slot)
            continue

        updated.append(
            PlannerSlot(
                slot_id=slot.slot_id,
                task_id=slot.task_id,
                title=edit.title or slot.title,
                description=edit.description or slot.description,
                start_at=start_at,
                end_at=end_at,
            )
        )

    return updated


def get_plan_by_request_id(*, plan_request_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any] | None:
    plan = _GENERATED_PLANS.get(plan_request_id)
    if not plan or plan["user_id"] != user_id:
        return None
    return plan


async def apply_plan_decision(
    db: AsyncSession,
    *,
    plan_request_id: uuid.UUID,
    user_id: uuid.UUID,
    decision: str,
    accepted_slots: set[uuid.UUID] | None,
    edits: list[PlannerSlotEdit] | None = None,
) -> dict[str, Any]:
    plan = get_plan_by_request_id(plan_request_id=plan_request_id, user_id=user_id)
    if not plan:
        raise ValueError("plan_not_found")

    if plan["status"] in {"accepted", "declined"}:
        return {
            "status": plan["status"],
            "created_task_ids": plan.get("created_task_ids", []),
            "updated_task_ids": plan.get("updated_task_ids", []),
            "version": plan.get("version", 1),
        }

    if decision == "decline":
        plan["status"] = "declined"
        plan["applied_slot_ids"] = []
        _append_history(plan, status="declined")
        return {"status": plan["status"], "created_task_ids": [], "updated_task_ids": [], "version": plan.get("version", 1)}

    created: list[uuid.UUID] = []
    updated: list[uuid.UUID] = []
    slots: list[PlannerSlot] = plan["slots"]
    if edits:
        slots = _apply_slot_edits(slots, edits)
        plan["slots"] = slots

    to_accept = accepted_slots if accepted_slots else {slot.slot_id for slot in slots}

    for slot in slots:
        if slot.slot_id not in to_accept:
            continue

        duration_minutes = int((slot.end_at - slot.start_at).total_seconds() // 60)
        if slot.task_id:
            task = await tasks_repo.get_by_id(db, task_id=slot.task_id, user_id=user_id)
            if not task:
                continue
            patch = {
                "title": slot.title,
                "description": slot.description,
                "due_at": slot.start_at,
                "estimated_minutes": duration_minutes,
                "status": "todo",
            }
            updated_task = await update_task(db, task, patch, expected_updated_at=None)
            updated.append(updated_task.id)
        else:
            task_data = {
                "title": slot.title,
                "description": slot.description,
                "due_at": slot.start_at,
                "estimated_minutes": duration_minutes,
            }
            new_task = await create_task(db, user_id, task_data)
            created.append(new_task.id)

    accepted_all = len(to_accept) == len(slots)
    plan["status"] = "accepted" if accepted_all else "partially_accepted"
    plan["created_task_ids"] = created
    plan["updated_task_ids"] = updated
    plan["applied_slot_ids"] = list(to_accept)
    _append_history(plan, status=plan["status"], created_task_ids=created, updated_task_ids=updated)

    return {
        "status": plan["status"],
        "created_task_ids": created,
        "updated_task_ids": updated,
        "version": plan.get("version", 1),
    }


async def _request_plan_from_ai(
    *, request: Request, plan_request_id: uuid.UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    endpoint = f"{settings.AI_SERVICE_URL.rstrip('/')}/v1/planner/batch-run"
    headers = {"X-AI-Internal-Token": settings.AI_SERVICE_AUTH_TOKEN}
    previous_version = int(payload.get("previous_plan_version") or 0)
    body = {
        "request_id": request.state.request_id,
        "requests": [
            {
                "plan_request_id": str(plan_request_id),
                "week_start": payload.get("week_start"),
                "work_schedule": payload.get("work_schedule", []),
                "subscription_status": payload.get("subscription_status", "pro"),
                "tasks": payload.get("tasks", []),
                "calendar_events": payload.get("calendar_events", []),
                "preferences": payload.get("preferences"),
                "previous_plan_version": previous_version,
                "completed_task_ids": payload.get("completed_task_ids", []),
                "rescheduled_task_ids": payload.get("rescheduled_task_ids", []),
                "applied_slot_ids": payload.get("applied_slot_ids", []),
            }
        ],
    }

    try:
        start_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        async with httpx.AsyncClient(timeout=settings.AI_SERVICE_TIMEOUT_SECONDS) as client:
            response = await client.post(endpoint, json=body, headers=headers)
        response.raise_for_status()
        latency_ms = int(datetime.now(timezone.utc).timestamp() * 1000) - start_ms
        log_ai_request(
            request_id=request.state.request_id,
            user_id=str(payload.get("user_id")),
            payload={"plan_request_id": str(plan_request_id), "previous_version": previous_version},
            status="success",
            latency_ms=latency_ms,
        )
        result = response.json()
    except Exception as exc:  # noqa: BLE001
        log.error(
            "ai_planner_request_failed",
            request_id=request.state.request_id,
            plan_request_id=str(plan_request_id),
            endpoint=endpoint,
            error=str(exc),
        )
        log_ai_request(
            request_id=request.state.request_id,
            user_id=str(payload.get("user_id")),
            payload={"plan_request_id": str(plan_request_id), "previous_version": previous_version},
            status="failed",
        )
        # Fall back to local generation to avoid user-facing failures
        fallback_slots, fallback_conflicts = _generate_slots(
            week_start=payload.get("week_start"),
            tasks=payload.get("tasks", []),
            work_schedule=payload.get("work_schedule", []),
            preferences=payload.get("preferences"),
            calendar_events=payload.get("calendar_events", []),
            completed_task_ids=payload.get("completed_task_ids", []),
            rescheduled_task_ids=payload.get("rescheduled_task_ids", []),
        )
        return {
            "status": "ready",
            "slots": fallback_slots,
            "conflicts": fallback_conflicts,
            "version": previous_version + 1,
            "source": "ai",
        }

    plans = result.get("plans") or []
    plan_data = next((p for p in plans if str(p.get("plan_request_id")) == str(plan_request_id)), None)
    if not plan_data:
        log.error(
            "ai_planner_missing_plan",
            request_id=request.state.request_id,
            plan_request_id=str(plan_request_id),
            error="plan_not_returned",
        )
        fallback_slots, fallback_conflicts = _generate_slots(
            week_start=payload.get("week_start"),
            tasks=payload.get("tasks", []),
            work_schedule=payload.get("work_schedule", []),
            preferences=payload.get("preferences"),
            calendar_events=payload.get("calendar_events", []),
            completed_task_ids=payload.get("completed_task_ids", []),
            rescheduled_task_ids=payload.get("rescheduled_task_ids", []),
        )
        return {
            "status": "ready",
            "slots": fallback_slots,
            "conflicts": fallback_conflicts,
            "version": previous_version + 1,
            "source": "ai",
        }

    slots: list[PlannerSlot] = []
    conflicts: list[PlannerConflict] = []
    for slot_data in plan_data.get("slots", []):
        try:
            slot = PlannerSlot.model_validate(slot_data)
            slots.append(slot)
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "ai_planner_slot_invalid",
                request_id=request.state.request_id,
                plan_request_id=str(plan_request_id),
                slot_payload=slot_data,
                error=str(exc),
            )

    for conflict_data in plan_data.get("conflicts", []):
        try:
            conflicts.append(PlannerConflict.model_validate(conflict_data))
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "ai_planner_conflict_invalid",
                request_id=request.state.request_id,
                plan_request_id=str(plan_request_id),
                conflict_payload=conflict_data,
                error=str(exc),
            )

    if not slots:
        slots, conflicts = _generate_slots(
            week_start=payload.get("week_start"),
            tasks=payload.get("tasks", []),
            work_schedule=payload.get("work_schedule", []),
            preferences=payload.get("preferences"),
            calendar_events=payload.get("calendar_events", []),
            completed_task_ids=payload.get("completed_task_ids", []),
            rescheduled_task_ids=payload.get("rescheduled_task_ids", []),
        )

    return {
        "status": plan_data.get("status", "ready"),
        "slots": slots,
        "conflicts": conflicts,
        "version": plan_data.get("version") or previous_version + 1,
        "source": plan_data.get("source", "ai"),
    }


def _append_history(plan: dict[str, Any], *, status: str, created_task_ids: list[uuid.UUID] | None = None, updated_task_ids: list[uuid.UUID] | None = None) -> None:
    history = plan.setdefault("history", [])
    history.append(
        {
            "version": plan.get("version", 1),
            "status": status,
            "slots": plan.get("slots", []),
            "conflicts": plan.get("conflicts", []),
            "created_task_ids": created_task_ids or [],
            "updated_task_ids": updated_task_ids or [],
            "logged_at": datetime.now(timezone.utc),
        }
    )


def _detect_conflicts(
    *,
    slots: list[PlannerSlot],
    work_schedule: list[dict[str, Any]],
    preferences: PlannerPreferences | None,
    calendar_events: list[dict[str, Any]],
    completed_task_ids: list[str],
    rescheduled_task_ids: list[str],
) -> list[PlannerConflict]:
    conflicts: list[PlannerConflict] = []
    for slot in slots:
        weekday = slot.start_at.weekday()
        start_time = slot.start_at.time()
        end_time = slot.end_at.time()

        # Work schedule boundaries
        allowed = False
        for entry in work_schedule:
            if entry.get("day_of_week") != weekday:
                continue
            start_window = time.fromisoformat(entry.get("start_time") if isinstance(entry.get("start_time"), str) else entry.get("start_time").isoformat())
            end_window = time.fromisoformat(entry.get("end_time") if isinstance(entry.get("end_time"), str) else entry.get("end_time").isoformat())
            if start_window.tzinfo:
                start_window = start_window.replace(tzinfo=None)
            if end_window.tzinfo:
                end_window = end_window.replace(tzinfo=None)
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
                start_break = br.start_time
                end_break = br.end_time
                if start_break <= start_time < end_break or start_break < end_time <= end_break:
                    conflicts.append(
                        PlannerConflict(
                            slot_id=slot.slot_id,
                            reason="break_time",
                            severity="warning",
                            details="Overlaps with a planned break.",
                        )
                    )

        for event in calendar_events:
            event_start = event.get("start_at")
            event_end = event.get("end_at")
            if isinstance(event_start, str):
                event_start = datetime.fromisoformat(event_start)
            if isinstance(event_end, str):
                event_end = datetime.fromisoformat(event_end)
            if event_start < slot.end_at and slot.start_at < event_end:
                conflicts.append(
                    PlannerConflict(
                        slot_id=slot.slot_id,
                        reason="calendar_conflict",
                        severity="error",
                        details=f"Overlaps with calendar event {event.get('title')}",
                    )
                )

        if slot.task_id and str(slot.task_id) in completed_task_ids:
            conflicts.append(
                PlannerConflict(
                    slot_id=slot.slot_id,
                    reason="task_already_completed",
                    severity="info",
                    related_task_id=slot.task_id,
                    details="Task was marked as completed before planning.",
                )
            )
        if slot.task_id and str(slot.task_id) in rescheduled_task_ids:
            conflicts.append(
                PlannerConflict(
                    slot_id=slot.slot_id,
                    reason="task_rescheduled",
                    severity="warning",
                    related_task_id=slot.task_id,
                    details="Task has been rescheduled and may need re-planning.",
                )
            )

    return conflicts
