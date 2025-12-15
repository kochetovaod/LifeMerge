from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.batch_sync import router as batch_sync_router
from app.api.v1.ai_rules import router as ai_rules_router
from app.api.v1.planner import router as planner_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.subscription import router as subscription_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(batch_sync_router, tags=["sync"])
api_router.include_router(ai_rules_router, tags=["ai"])
api_router.include_router(planner_router, tags=["planner"])
api_router.include_router(tasks_router, tags=["tasks"])
api_router.include_router(subscription_router, tags=["subscription"])
