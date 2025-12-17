from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.logging import log
from app.core.response import ok
from app.db.session import get_db
from app.schemas.sync import BatchSyncRequest, BatchSyncResponse
from app.services.batch_sync_service import process_batch_operations

router = APIRouter(prefix="/sync")


@router.post("/batch", response_model=BatchSyncResponse)
async def batch_sync(
    request: Request,
    body: BatchSyncRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # IdempotencySnapshotMiddleware handles:
    # - key lookup by X-Idempotency-Key (or X-Request-Id fallback if enabled there)
    # - returning stored response for retries
    results = await process_batch_operations(db, user_id=current_user.id, operations=body.operations)
    await db.commit()

    log.info(
        "batch_sync_completed",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        operations=len(body.operations),
        applied=len([r for r in results if r.status == "applied"]),
        skipped=len([r for r in results if r.status == "skipped"]),
    )

    return ok(request, {"results": [r.model_dump() for r in results]})
