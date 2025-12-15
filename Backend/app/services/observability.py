from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.logging import log


def log_ai_request(*, request_id: str, user_id: str, payload: dict[str, Any], status: str, latency_ms: int | None = None):
    log.info(
        "ai_request",
        request_id=request_id,
        user_id=user_id,
        status=status,
        latency_ms=latency_ms,
        payload=payload,
        logged_at=datetime.now(timezone.utc).isoformat(),
    )


def log_sync_error(*, user_id: str, entity: str, action: str, reason: str, request_id: str | None = None):
    log.error(
        "sync_error",
        request_id=request_id,
        user_id=user_id,
        entity=entity,
        action=action,
        reason=reason,
        logged_at=datetime.now(timezone.utc).isoformat(),
    )


def record_push_metric(*, user_id: str, platform: str, status: str, request_id: str | None = None):
    log.info(
        "push_delivery",
        request_id=request_id,
        user_id=user_id,
        platform=platform,
        status=status,
        logged_at=datetime.now(timezone.utc).isoformat(),
    )


def record_sync_metric(*, queue_depth: int, processed: int, status: str):
    log.info(
        "sync_queue_metric",
        queue_depth=queue_depth,
        processed=processed,
        status=status,
        logged_at=datetime.now(timezone.utc).isoformat(),
    )
