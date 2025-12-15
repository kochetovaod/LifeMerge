from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.sync import BatchSyncOperation, BatchSyncResult
from app.schemas.tasks import ALLOWED_STATUSES, TaskOut


async def process_batch_operations(
    db: AsyncSession, *, user_id: uuid.UUID, operations: list[BatchSyncOperation]
) -> list[BatchSyncResult]:
    results: list[BatchSyncResult] = []

    for op in operations:
        if op.entity == "task":
            result = await _process_task_operation(db, user_id=user_id, op=op)
        else:
            result = BatchSyncResult(
                entity=op.entity,
                action=op.action,
                id=op.id,
                status="unsupported",
                reason="Unsupported entity type",
            )
        results.append(result)

    return results


async def _process_task_operation(db: AsyncSession, *, user_id: uuid.UUID, op: BatchSyncOperation) -> BatchSyncResult:
    normalized_updated_at = _normalize_to_utc(op.updated_at)

    task: Task | None = None
    if op.id:
        res = await db.execute(select(Task).where(Task.id == op.id, Task.user_id == user_id))
        task = res.scalar_one_or_none()

    if op.action == "delete":
        return await _apply_task_delete(db, task=task, op=op, updated_at=normalized_updated_at)

    if op.action == "upsert":
        return await _apply_task_upsert(db, user_id=user_id, task=task, op=op, updated_at=normalized_updated_at)

    return BatchSyncResult(
        entity=op.entity,
        action=op.action,
        id=op.id,
        status="error",
        reason="Unsupported action",
    )


async def _apply_task_upsert(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    task: Task | None,
    op: BatchSyncOperation,
    updated_at: datetime,
) -> BatchSyncResult:
    if op.data is None:
        return BatchSyncResult(
            entity=op.entity,
            action=op.action,
            id=op.id,
            status="error",
            reason="Missing data for upsert",
        )

    status = op.data.get("status", task.status if task else "todo")
    if status and status not in ALLOWED_STATUSES:
        return BatchSyncResult(
            entity=op.entity,
            action=op.action,
            id=op.id,
            status="error",
            reason="Unsupported status value",
        )

    if task and _normalize_to_utc(task.updated_at) >= updated_at:
        return BatchSyncResult(
            entity=op.entity,
            action=op.action,
            id=task.id,
            status="skipped",
            reason="Conflict: existing version is newer",
            current=TaskOut.model_validate(task).model_dump(),
        )

    if task is None:
        title = op.data.get("title")
        if not title:
            return BatchSyncResult(
                entity=op.entity,
                action=op.action,
                id=op.id,
                status="error",
                reason="Title is required for creating tasks",
            )

        task = Task(
            id=op.id or uuid.uuid4(),
            user_id=user_id,
            title=title,
            description=op.data.get("description"),
            goal_id=op.data.get("goal_id"),
            due_at=_normalize_optional_dt(op.data.get("due_at")),
            priority=op.data.get("priority"),
            estimated_minutes=op.data.get("estimated_minutes"),
            energy_level=op.data.get("energy_level"),
            status=status or "todo",
            created_at=_normalize_to_utc(op.data.get("created_at") or updated_at),
            updated_at=updated_at,
            deleted=bool(op.data.get("deleted", False)),
        )
        db.add(task)
        await db.flush()
    else:
        for field in [
            "title",
            "description",
            "goal_id",
            "due_at",
            "priority",
            "estimated_minutes",
            "energy_level",
            "status",
            "deleted",
        ]:
            if field in op.data:
                value: Any = op.data.get(field)
                if field == "status" and value and value not in ALLOWED_STATUSES:
                    return BatchSyncResult(
                        entity=op.entity,
                        action=op.action,
                        id=task.id,
                        status="error",
                        reason="Unsupported status value",
                    )
                if field == "due_at":
                    value = _normalize_optional_dt(value)
                setattr(task, field, value)
        task.updated_at = updated_at

    await db.flush()
    return BatchSyncResult(
        entity=op.entity,
        action=op.action,
        id=task.id,
        status="applied",
        current=TaskOut.model_validate(task).model_dump(),
    )


async def _apply_task_delete(
    db: AsyncSession,
    *,
    task: Task | None,
    op: BatchSyncOperation,
    updated_at: datetime,
) -> BatchSyncResult:
    if op.id is None:
        return BatchSyncResult(
            entity=op.entity,
            action=op.action,
            id=None,
            status="error",
            reason="Task id is required for delete",
        )

    if task is None:
        return BatchSyncResult(
            entity=op.entity,
            action=op.action,
            id=op.id,
            status="skipped",
            reason="Task not found",
        )

    if _normalize_to_utc(task.updated_at) >= updated_at:
        return BatchSyncResult(
            entity=op.entity,
            action=op.action,
            id=task.id,
            status="skipped",
            reason="Conflict: existing version is newer",
            current=TaskOut.model_validate(task).model_dump(),
        )

    task.deleted = True
    task.updated_at = updated_at
    await db.flush()

    return BatchSyncResult(
        entity=op.entity,
        action=op.action,
        id=task.id,
        status="applied",
        current=TaskOut.model_validate(task).model_dump(),
    )


def _normalize_to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalize_optional_dt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _normalize_to_utc(value)
