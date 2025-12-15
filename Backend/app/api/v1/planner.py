from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.ai_access import ensure_ai_access
from app.api.deps import get_current_user
from app.api.idempotency import enforce_idempotency
from app.core.logging import log
from app.core.response import err, ok
from app.db.session import get_db
from app.schemas.planner import (
    PlannerDecisionIn,
    PlannerDecisionOut,
    PlannerPlanOut,
    PlannerRunIn,
    PlannerRunOut,
)
from app.services.planner_service import apply_plan_decision, enqueue_planner_run, get_plan_by_request_id

router = APIRouter(prefix="/planner")


@router.post("/run", response_model=PlannerRunOut)
async def run_ai_planner(
    request: Request,
    body: PlannerRunIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    try:
        ensure_ai_access(request, subscription_status=body.subscription_status)
    except HTTPException as exc:
        if exc.status_code == 403:
            trial_offer = None
            detail = exc.detail or {}
            if isinstance(detail, dict):
                error = detail.get("error") or {}
                details = error.get("details") or {}
                trial_offer = details.get("trial_offer") or "Start a trial to enable the AI planner."
            payload = {
                "plan_request_id": None,
                "status": "upgrade_required",
                "request_id": request.state.request_id,
                "message": "AI planner is only available on Trial or Pro.",
                "trial_offer": trial_offer,
            }
            log.info(
                "planner_run_denied_free_plan",
                request_id=request.state.request_id,
                user_id=str(current_user.id),
                subscription_status=body.subscription_status,
            )
            return ok(request, payload)
        raise

    await enforce_idempotency(request, current_user, db, request_id=body.request_id, idempotency_key=x_idempotency_key)

    planner_payload = {
        "week_start": body.week_start.isoformat() if body.week_start else None,
        "work_schedule": [entry.model_dump(mode="json") for entry in body.work_schedule],
        "subscription_status": body.subscription_status,
        "tasks": [task.model_dump(mode="json") for task in body.tasks],
        "calendar_events": [event.model_dump(mode="json") for event in body.calendar_events],
        "preferences": body.preferences.model_dump(mode="json") if body.preferences else None,
        "previous_plan_version": body.previous_plan_version or 0,
        "completed_task_ids": [str(item) for item in body.completed_task_ids],
        "rescheduled_task_ids": [str(item) for item in body.rescheduled_task_ids],
        "applied_slot_ids": [str(item) for item in body.applied_slot_ids],
    }
    result = await enqueue_planner_run(request=request, user_id=current_user.id, payload=planner_payload)

    log.info(
        "planner_run_requested",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        subscription_status=body.subscription_status,
        work_schedule_entries=len(body.work_schedule),
        tasks=len(body.tasks),
        calendar_events=len(body.calendar_events),
    )

    return ok(request, result)


@router.get("/{plan_request_id}", response_model=PlannerPlanOut)
async def get_ai_plan(
    request: Request,
    plan_request_id: uuid.UUID,
    current_user=Depends(get_current_user),
):
    plan = get_plan_by_request_id(plan_request_id=plan_request_id, user_id=current_user.id)
    if not plan:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Plan not found"))

    payload = {
        "plan_request_id": plan_request_id,
        "status": plan["status"],
        "slots": plan["slots"],
        "conflicts": plan.get("conflicts", []),
        "version": plan.get("version", 1),
        "request_id": request.state.request_id,
    }

    log.info(
        "planner_plan_retrieved",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        plan_request_id=str(plan_request_id),
        slots=len(plan.get("slots", [])),
        conflicts=len(plan.get("conflicts", [])),
        version=plan.get("version", 1),
    )
    return ok(request, payload)


@router.post("/{plan_request_id}/decision", response_model=PlannerDecisionOut)
async def decide_ai_plan(
    request: Request,
    plan_request_id: uuid.UUID,
    body: PlannerDecisionIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    await enforce_idempotency(request, current_user, db, request_id=body.request_id, idempotency_key=x_idempotency_key)

    try:
        accepted_slots = set(body.accepted_slot_ids) if body.accepted_slot_ids else None
        decision_result = await apply_plan_decision(
            db,
            plan_request_id=plan_request_id,
            user_id=current_user.id,
            decision=body.decision,
            accepted_slots=accepted_slots,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Plan not found"))

    await db.commit()

    log.info(
        "planner_plan_decision",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        plan_request_id=str(plan_request_id),
        decision=body.decision,
        accepted_slots=len(body.accepted_slot_ids or []),
        version=decision_result.get("version", 1),
    )

    payload = {
        "plan_request_id": plan_request_id,
        "status": decision_result["status"],
        "created_task_ids": decision_result.get("created_task_ids", []),
        "updated_task_ids": decision_result.get("updated_task_ids", []),
        "request_id": body.request_id,
        "version": decision_result.get("version", 1),
    }

    return ok(request, payload)
