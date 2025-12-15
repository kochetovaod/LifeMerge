from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request

from app.core.logging import log
from app.services.events import publish_event


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

    log.info(
        "ai_planner_requested",
        request_id=request.state.request_id,
        user_id=str(user_id),
        plan_request_id=str(plan_request_id),
        subscription_status=payload.get("subscription_status"),
    )

    return {"plan_request_id": plan_request_id, "status": "queued"}
