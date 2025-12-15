from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.idempotency import enforce_idempotency
from app.core.logging import log
from app.core.response import err, ok
from app.db.session import get_db
from app.models.task import Task
from app.schemas.tasks import ALLOWED_STATUSES, TaskCreateIn, TaskDeleteIn, TaskListOut, TaskOut, TaskUpdateIn
from app.services.events import publish_event
from app.services.tasks_service import create_task, list_tasks, soft_delete_task, update_task

router = APIRouter(prefix="/tasks")


@router.get("", response_model=TaskListOut)
async def get_tasks(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(default=None),
    goal_id: uuid.UUID | None = Query(default=None),
    due_from: datetime | None = Query(default=None),
    due_to: datetime | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    if status and status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=err(request, "validation_error", "Unsupported status filter"))

    items, next_cursor = await list_tasks(
        db,
        user_id=current_user.id,
        status=status,
        goal_id=goal_id,
        due_from=due_from,
        due_to=due_to,
        cursor=cursor,
        limit=limit,
    )

    payload = {
        "items": [TaskOut.model_validate(t) for t in items],
        "next_cursor": next_cursor,
    }

    log.info(
        "tasks_list",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        count=len(items),
        next_cursor=next_cursor,
    )

    return ok(request, payload)


@router.post("", response_model=TaskOut)
async def post_task(
    request: Request,
    body: TaskCreateIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    await enforce_idempotency(request, current_user, db, request_id=body.request_id, idempotency_key=x_idempotency_key)

    task = await create_task(db, current_user.id, body.model_dump())
    await db.commit()
    await db.refresh(task)

    publish_event(
        name="Task_Created",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        payload={"task_id": str(task.id)},
    )

    log.info(
        "task_created",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        task_id=str(task.id),
    )

    return ok(request, TaskOut.model_validate(task).model_dump())


@router.patch("/{task_id}", response_model=TaskOut)
async def patch_task(
    request: Request,
    task_id: uuid.UUID,
    body: TaskUpdateIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    await enforce_idempotency(request, current_user, db, request_id=body.request_id, idempotency_key=x_idempotency_key)

    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id, Task.deleted == False))  # noqa: E712
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Task not found"))

    try:
        updated = await update_task(db, task, body.model_dump(exclude_unset=True), expected_updated_at=body.updated_at)
    except ValueError as exc:
        if str(exc) == "conflict":
            raise HTTPException(
                status_code=409,
                detail=err(
                    request,
                    "conflict",
                    "Task version conflict",
                    details={"current": TaskOut.model_validate(task).model_dump()},
                ),
            )
        raise HTTPException(status_code=400, detail=err(request, "validation_error", "Invalid task data"))

    await db.commit()
    await db.refresh(updated)
    log.info(
        "task_updated",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        task_id=str(updated.id),
    )
    return ok(request, TaskOut.model_validate(updated).model_dump())


@router.delete("/{task_id}")
async def delete_task(
    request: Request,
    task_id: uuid.UUID,
    body: TaskDeleteIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    await enforce_idempotency(request, current_user, db, request_id=body.request_id, idempotency_key=x_idempotency_key)

    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id, Task.deleted == False))  # noqa: E712
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Task not found"))

    await soft_delete_task(db, task)
    await db.commit()
    log.info(
        "task_deleted",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        task_id=str(task.id),
    )
    return ok(request, {"status": "ok"})
