from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user
from app.core.response import ok
from app.models.user import User
from app.schemas.subscription import SubscriptionStatusOut
from app.services.subscription_service import subscription_status

router = APIRouter(prefix="/subscription")


@router.get("/status", response_model=SubscriptionStatusOut)
async def get_subscription_status(
    request: Request, current_user: User = Depends(get_current_user)
):
    status = subscription_status(current_user)
    return ok(request, status.model_dump())
