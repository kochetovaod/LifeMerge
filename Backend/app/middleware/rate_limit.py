from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException, Request

from app.core.response import err

# MVP in-memory limiter (per-process). For prod / multi-replica -> Redis.
@dataclass
class _Bucket:
    reset_at: float
    count: int


_STORE: dict[str, _Bucket] = {}


def _client_ip(request: Request) -> str:
    # if behind proxy, you may want X-Forwarded-For parsing in ingress
    return request.client.host if request.client else "unknown"


def rate_limit(*, key_prefix: str, limit: int, window_seconds: int) -> Callable:
    async def _dep(request: Request):
        now = time.time()
        ip = _client_ip(request)
        key = f"{key_prefix}:{ip}"

        b = _STORE.get(key)
        if b is None or now >= b.reset_at:
            _STORE[key] = _Bucket(reset_at=now + window_seconds, count=1)
            return

        b.count += 1
        if b.count > limit:
            raise HTTPException(
                status_code=429,
                detail=err(
                    request,
                    "rate_limited",
                    "Too many requests",
                    details={"retry_after_seconds": max(0, int(b.reset_at - now))},
                ),
            )

    return Depends(_dep)


# project defaults
signup_rate_limit = rate_limit(key_prefix="auth:signup", limit=10, window_seconds=60)
forgot_rate_limit = rate_limit(key_prefix="auth:forgot", limit=10, window_seconds=60)
