from __future__ import annotations

from typing import Iterable

from fastapi import HTTPException, Request

from app.core.response import err

ALLOWED_AI_SUBSCRIPTIONS: set[str] = {"trial", "pro"}


def ensure_ai_access(request: Request, *, subscription_status: str) -> None:
    """Ensure the caller has access to AI endpoints.

    Free tier users are rejected with a 403 and a descriptive message that
    outlines the current limitations. Trial and Pro users are allowed.
    """

    if subscription_status.lower() not in ALLOWED_AI_SUBSCRIPTIONS:
        allowed: Iterable[str] = sorted(ALLOWED_AI_SUBSCRIPTIONS)
        raise HTTPException(
            status_code=403,
            detail=err(
                request,
                "ai_access_denied",
                "AI features are available for Trial or Pro members only.",
                details={
                    "allowed_statuses": list(allowed),
                    "restrictions": "Free plan does not include AI planner access. Upgrade or start a trial to continue.",
                },
            ),
        )
