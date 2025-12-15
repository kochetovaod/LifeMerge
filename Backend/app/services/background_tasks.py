from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification import DigestSchedule
from app.models.sync_operation import SyncOperation
from app.services.batch_sync_service import process_batch_operations
from app.services.observability import log_sync_error, record_sync_metric
from app.services.push_service import push_service
from app.schemas.sync import BatchSyncOperation


async def process_sync_queue(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    retry_cutoff = now - timedelta(minutes=settings.SYNC_RETRY_MINUTES)

    res = await db.execute(
        select(SyncOperation)
        .where(
            and_(
                SyncOperation.status.in_(["pending", "error"]),
                SyncOperation.scheduled_at <= now,
                SyncOperation.locked.is_(False),
                SyncOperation.updated_at <= retry_cutoff,
            )
        )
        .limit(settings.SYNC_QUEUE_BATCH_SIZE)
    )
    ops = list(res.scalars())
    if not ops:
        record_sync_metric(queue_depth=0, processed=0, status="idle")
        return

    processed = 0
    for op in ops:
        op.locked = True
        op.updated_at = now
        await db.flush()
        try:
            payload = BatchSyncOperation(
                entity=op.payload.get("entity", op.entity),
                action=op.payload.get("action", op.action),
                id=op.payload.get("id"),
                updated_at=op.payload.get("updated_at", now),
                data=op.payload.get("data"),
            )
            await process_batch_operations(db, user_id=op.user_id, operations=[payload])
            op.status = "done"
            op.last_error = None
        except Exception as exc:  # noqa: BLE001
            op.status = "error"
            op.last_error = str(exc)
            log_sync_error(user_id=str(op.user_id), entity=op.entity, action=op.action, reason=str(exc))
        finally:
            op.locked = False
            op.attempts += 1
            op.updated_at = datetime.now(timezone.utc)
            processed += 1
    await db.commit()
    record_sync_metric(queue_depth=max(len(ops) - processed, 0), processed=processed, status="processed")


async def dispatch_digests(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    res = await db.execute(
        select(DigestSchedule).where(
            and_(
                DigestSchedule.channel == "push",
                DigestSchedule.next_run_at <= now,
            )
        )
    )
    schedules = list(res.scalars())
    for schedule in schedules:
        await push_service.send_digest(
            db,
            digest=schedule,
            title="LifeMerge digest",
            body=f"Your {schedule.cadence} summary is ready",
            payload={"cadence": schedule.cadence},
        )
        schedule.last_sent_at = now
        schedule.next_run_at = _next_digest_run(schedule, now)
        schedule.updated_at = now
    await db.commit()


def _next_digest_run(schedule: DigestSchedule, now: datetime) -> datetime:
    if schedule.cadence == "weekly":
        delta = timedelta(days=7)
    else:
        delta = timedelta(days=1)
    base = now.replace(hour=settings.DIGEST_SEND_HOUR_UTC, minute=0, second=0, microsecond=0)
    return base + delta
