from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.logging import log
from app.core.response import err, ok
from app.db.session import get_db
from app.schemas.ai_rules import AiRulesOut, AiRulesUpsertIn, AiRulesBase
from app.services.ai_rules_service import get_rules, upsert_rules

router = APIRouter(prefix="/ai/rules")


def _serialize_rules(rules_model) -> AiRulesBase:
    return AiRulesBase.model_validate(
        {
            "quiet_hours": (rules_model.quiet_hours if rules_model else []) or [],
            "breaks": (rules_model.breaks if rules_model else []) or [],
            "blocked_days": (rules_model.blocked_days if rules_model else []) or [],
        }
    )


@router.get("", response_model=AiRulesOut)
async def get_ai_rules(request: Request, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rules = await get_rules(db, user_id=current_user.id)
    payload = _serialize_rules(rules).model_dump()

    log.info(
        "ai_rules_fetch",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        has_rules=rules is not None,
    )

    return ok(request, {**payload, "request_id": request.state.request_id})


@router.put("", response_model=AiRulesOut)
async def upsert_ai_rules(
    request: Request,
    body: AiRulesUpsertIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload = body.model_dump(exclude={"request_id"}, mode="json")
    try:
        rules = await upsert_rules(
            db,
            user_id=current_user.id,
            quiet_hours=payload["quiet_hours"],
            breaks=payload["breaks"],
            blocked_days=payload["blocked_days"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=err(request, "validation_error", str(exc)))

    await db.commit()
    await db.refresh(rules)

    log.info(
        "ai_rules_upserted",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        quiet_hours=len(payload["quiet_hours"]),
        breaks=len(payload["breaks"]),
        blocked_days=len(payload["blocked_days"]),
    )

    rules_payload = _serialize_rules(rules).model_dump()
    return ok(request, {**rules_payload, "request_id": request.state.request_id})
