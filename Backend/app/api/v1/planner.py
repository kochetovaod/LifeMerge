from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.idempotency import enforce_idempotency
from app.core.logging import log
from app.core.response import ok
from app.db.session import get_db
from app.schemas.planner import PlannerRunIn, PlannerRunOut
from app.services.planner_service import enqueue_planner_run

router = APIRouter(prefix="/planner")


@router.post("/run", response_model=PlannerRunOut)
async def run_ai_planner(
    request: Request,
    body: PlannerRunIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    await enforce_idempotency(request, current_user, db, request_id=body.request_id, idempotency_key=x_idempotency_key)

    planner_payload = {
        "week_start": body.week_start.isoformat() if body.week_start else None,
        "work_schedule": [entry.model_dump() for entry in body.work_schedule],
        "subscription_status": body.subscription_status,
    }
    result = await enqueue_planner_run(request=request, user_id=current_user.id, payload=planner_payload)

    log.info(
        "planner_run_requested",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        subscription_status=body.subscription_status,
        work_schedule_entries=len(body.work_schedule),
    )

    return ok(request, result)
