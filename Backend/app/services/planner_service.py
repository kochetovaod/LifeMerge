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
from app.schemas.planner import PlannerConflict, PlannerPreferences, PlannerSlot
from app.services.events import publish_event
from app.services.tasks_service import create_task, update_task

_GENERATED_PLANS: dict[uuid.UUID, dict[str, Any]] = {}


async def enqueue_planner_run(
    *, request: Request, user_id: uuid.UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    plan_request_id = uuid.uuid4()

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
    _GENERATED_PLANS[plan_request_id] = {
        "user_id": user_id,
        "status": plan["status"],
        "slots": slots,
        "conflicts": conflicts,
        "version": version,
        "created_at": datetime.now(timezone.utc),
        "history": [
            {
                "version": version,
                "status": plan["status"],
                "slots": slots,
                "conflicts": conflicts,
                "logged_at": datetime.now(timezone.utc),
            }
        ],
    }

    log.info(
        "ai_planner_requested",
        request_id=request.state.request_id,
        user_id=str(user_id),
        plan_request_id=str(plan_request_id),
        subscription_status=payload.get("subscription_status"),
        version=version,
        conflicts=len(conflicts),
    )

    return {"plan_request_id": plan_request_id, "status": "ready"}


def _generate_slots(
    *,
    week_start: str | None,
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

    start_time = time(hour=9)
    if work_schedule:
        start_key = lambda entry: entry.get("start_time").isoformat() if isinstance(entry.get("start_time"), time) else str(entry.get("start_time"))  # noqa: E731
        first_entry = sorted(work_schedule, key=start_key)[0]
        raw_start = first_entry.get("start_time")
        if isinstance(raw_start, time):
            start_time = raw_start
        elif isinstance(raw_start, str):
            try:
                start_time = time.fromisoformat(raw_start)
            except ValueError:
                start_time = time(hour=9)

    base_dt = datetime.combine(start_date, start_time, tzinfo=timezone.utc)
    slots: list[PlannerSlot] = []
    durations = [timedelta(minutes=90), timedelta(minutes=60), timedelta(minutes=45)]
    titles = ["Deep work", "Focus session", "Wrap-up"]

    for idx, delta in enumerate(durations):
        start_at = base_dt + timedelta(hours=idx * 3)
        end_at = start_at + delta
        slot = PlannerSlot(
            slot_id=uuid.uuid4(),
            task_id=None,
            title=titles[idx],
            description=f"Suggested block {idx + 1}",
            start_at=start_at,
            end_at=end_at,
        )
        slots.append(slot)

    conflicts = _detect_conflicts(
        slots=slots,
        work_schedule=work_schedule or [],
        preferences=preferences,
        calendar_events=calendar_events or [],
        completed_task_ids=completed_task_ids or [],
        rescheduled_task_ids=rescheduled_task_ids or [],
    )

    return slots, conflicts


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
        async with httpx.AsyncClient(timeout=settings.AI_SERVICE_TIMEOUT_SECONDS) as client:
            response = await client.post(endpoint, json=body, headers=headers)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:  # noqa: BLE001
        log.error(
            "ai_planner_request_failed",
            request_id=request.state.request_id,
            plan_request_id=str(plan_request_id),
            endpoint=endpoint,
            error=str(exc),
        )
        # Fall back to local generation to avoid user-facing failures
        fallback_slots, fallback_conflicts = _generate_slots(
            week_start=payload.get("week_start"),
            work_schedule=payload.get("work_schedule", []),
            preferences=payload.get("preferences"),
            calendar_events=payload.get("calendar_events", []),
            completed_task_ids=payload.get("completed_task_ids", []),
            rescheduled_task_ids=payload.get("rescheduled_task_ids", []),
        )
        return {"status": "ready", "slots": fallback_slots, "conflicts": fallback_conflicts, "version": previous_version + 1}

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
            work_schedule=payload.get("work_schedule", []),
            preferences=payload.get("preferences"),
            calendar_events=payload.get("calendar_events", []),
            completed_task_ids=payload.get("completed_task_ids", []),
            rescheduled_task_ids=payload.get("rescheduled_task_ids", []),
        )
        return {"status": "ready", "slots": fallback_slots, "conflicts": fallback_conflicts, "version": previous_version + 1}

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
