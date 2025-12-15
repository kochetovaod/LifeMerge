from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import log
from app.repositories import tasks_repo
from app.schemas.planner import PlannerSlot
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

    slots = _generate_slots(week_start=payload.get("week_start"))
    _GENERATED_PLANS[plan_request_id] = {
        "user_id": user_id,
        "status": "ready",
        "slots": slots,
        "created_at": datetime.now(timezone.utc),
    }

    log.info(
        "ai_planner_requested",
        request_id=request.state.request_id,
        user_id=str(user_id),
        plan_request_id=str(plan_request_id),
        subscription_status=payload.get("subscription_status"),
    )

    return {"plan_request_id": plan_request_id, "status": "ready"}


def _generate_slots(*, week_start: str | None) -> list[PlannerSlot]:
    if week_start:
        try:
            start_date = date.fromisoformat(week_start)
        except ValueError:
            start_date = datetime.now(timezone.utc).date()
    else:
        start_date = datetime.now(timezone.utc).date()

    base_dt = datetime.combine(start_date, time(hour=9), tzinfo=timezone.utc)
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

    return slots


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
        }

    if decision == "decline":
        plan["status"] = "declined"
        return {"status": plan["status"], "created_task_ids": [], "updated_task_ids": []}

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

    plan["status"] = "accepted"
    plan["created_task_ids"] = created
    plan["updated_task_ids"] = updated

    return {"status": plan["status"], "created_task_ids": created, "updated_task_ids": updated}
