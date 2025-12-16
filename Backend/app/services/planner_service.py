from __future__ import annotations

import uuid
from datetime import datetime, timezone
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
from app.services.planning_strategies import PlanningStrategyConfig, PlanningStrategyFactory
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
    strategy_name: str | None = None,
    strategy_options: dict[str, Any] | None = None,
) -> tuple[list[PlannerSlot], list[PlannerConflict]]:
    config = PlanningStrategyConfig(
        week_start=week_start,
        tasks=tasks,
        work_schedule=work_schedule,
        preferences=preferences,
        calendar_events=calendar_events,
        completed_task_ids=completed_task_ids,
        rescheduled_task_ids=rescheduled_task_ids,
        strategy_name=strategy_name,
        strategy_options=strategy_options,
    )

    strategy = PlanningStrategyFactory.get_strategy(config)
    slots, conflicts = strategy.generate_slots(config)

    log.info(
        "planner_strategy_metrics",
        strategy=strategy.get_name(),
        scheduled=len(slots),
        conflicts=len(conflicts),
        metadata=strategy.get_metadata(),
    )

    return slots, conflicts


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
            strategy_name=payload.get("strategy"),
            strategy_options=payload.get("strategy_options"),
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
            strategy_name=payload.get("strategy"),
            strategy_options=payload.get("strategy_options"),
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
            strategy_name=payload.get("strategy"),
            strategy_options=payload.get("strategy_options"),
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
