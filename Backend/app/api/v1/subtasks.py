from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.idempotency import enforce_idempotency
from app.core.response import err, ok
from app.db.session import get_db
from app.models.subtask import Subtask
from app.models.task import Task
from app.schemas.subtasks import SubtaskCreateIn, SubtaskListOut, SubtaskOut, SubtaskUpdateIn
from app.application.services.subtask_service import create_subtask, list_subtasks, update_subtask

router = APIRouter(prefix="/subtasks")


@router.get("", response_model=SubtaskListOut)
async def get_subtasks(
    request: Request,
    task_id: uuid.UUID = Query(...),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # verify parent task exists and belongs to user
    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id, Task.deleted == False))  # noqa: E712
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Task not found"))

    items, next_cursor = await list_subtasks(db, user_id=current_user.id, task_id=task_id, cursor=cursor, limit=limit)
    return ok(request, {"items": [SubtaskOut.model_validate(x) for x in items], "next_cursor": next_cursor})


@router.post("/tasks/{task_id}", response_model=SubtaskOut)
async def create_for_task(
    request: Request,
    task_id: uuid.UUID,
    body: SubtaskCreateIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    await enforce_idempotency(request, current_user, db, request_id=body.request_id, idempotency_key=x_idempotency_key)

    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id, Task.deleted == False))  # noqa: E712
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Task not found"))

    st = await create_subtask(db, user_id=current_user.id, task_id=task_id, title=body.title)
    await db.commit()
    await db.refresh(st)
    return ok(request, SubtaskOut.model_validate(st).model_dump())


@router.patch("/{subtask_id}", response_model=SubtaskOut)
async def patch_subtask(
    request: Request,
    subtask_id: uuid.UUID,
    body: SubtaskUpdateIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    await enforce_idempotency(request, current_user, db, request_id=body.request_id, idempotency_key=x_idempotency_key)

    res = await db.execute(select(Subtask).where(Subtask.id == subtask_id, Subtask.user_id == current_user.id, Subtask.deleted == False))  # noqa: E712
    st = res.scalar_one_or_none()
    if not st:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Subtask not found"))

    try:
        updated = await update_subtask(db, subtask=st, patch=body.model_dump(exclude_unset=True), expected_updated_at=body.updated_at)
    except ValueError:
        raise HTTPException(
            status_code=409,
            detail=err(
                request,
                "conflict",
                "Subtask version conflict",
                details={"current": SubtaskOut.model_validate(st).model_dump()},
            ),
        )

    await db.commit()
    await db.refresh(updated)
    return ok(request, SubtaskOut.model_validate(updated).model_dump())
