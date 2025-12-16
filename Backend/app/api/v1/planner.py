from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.response import ok
from app.db.session import get_db
from app.schemas.planner import (
    PlannerDecisionIn,
    PlannerDecisionOut,
    PlannerPlanOut,
    PlannerReplanIn,
    PlannerRunIn,
    PlannerRunOut,
)
from app.services.planner_orchestration import (
    PlannerAccessService,
    PlannerEventPublisher,
    PlannerOrchestrator,
    PlannerPayloadValidator,
)

router = APIRouter(prefix="/planner")


def get_planner_orchestrator() -> PlannerOrchestrator:
    event_publisher = PlannerEventPublisher()
    payload_validator = PlannerPayloadValidator()
    access_service = PlannerAccessService(event_publisher)
    return PlannerOrchestrator(access_service, event_publisher, payload_validator)


@router.post("/run", response_model=PlannerRunOut)
async def run_ai_planner(
    request: Request,
    body: PlannerRunIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
    orchestrator: PlannerOrchestrator = Depends(get_planner_orchestrator),
):
    result = await orchestrator.run_planner(
        request,
        body,
        current_user=current_user,
        db=db,
        idempotency_key=x_idempotency_key,
    )
    return ok(request, result)


@router.get("/{plan_request_id}", response_model=PlannerPlanOut)
async def get_ai_plan(
    request: Request,
    plan_request_id: uuid.UUID,
    current_user=Depends(get_current_user),
    orchestrator: PlannerOrchestrator = Depends(get_planner_orchestrator),
):
    payload = orchestrator.get_plan(request, plan_request_id=plan_request_id, current_user=current_user)
    return ok(request, payload)


@router.post("/{plan_request_id}/replan", response_model=PlannerPlanOut)
async def replan_ai_plan(
    request: Request,
    plan_request_id: uuid.UUID,
    body: PlannerReplanIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
    orchestrator: PlannerOrchestrator = Depends(get_planner_orchestrator),
):
    payload = await orchestrator.replan(
        request,
        plan_request_id=plan_request_id,
        body=body,
        current_user=current_user,
        db=db,
        idempotency_key=x_idempotency_key,
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
    orchestrator: PlannerOrchestrator = Depends(get_planner_orchestrator),
):
    payload = await orchestrator.decide_plan(
        request,
        plan_request_id=plan_request_id,
        body=body,
        current_user=current_user,
        db=db,
        idempotency_key=x_idempotency_key,
    )
    return ok(request, payload)
