from __future__ import annotations

from typing import Any

from app.core.logging import log


def publish_event(*, name: str, request_id: str, user_id: str | None = None, payload: dict[str, Any] | None = None) -> None:
    # MVP: structured log. Later: outbox/queue -> worker -> Firebase/Amplitude
    log.info(
        "analytics_event",
        event_name=name,
        request_id=request_id,
        user_id=user_id,
        payload=payload or {},
    )
