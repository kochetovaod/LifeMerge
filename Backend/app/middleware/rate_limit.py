from __future__ import annotations

import time
from typing import Callable

from fastapi import Depends, HTTPException, Request

from app.core.config import settings
from app.core.response import err
from app.infra.redis_client import get_redis


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _rl_key(prefix: str, request: Request) -> str:
    # Optional: include endpoint-specific salt and ip
    return f"rl:{prefix}:{_client_ip(request)}"


def redis_rate_limit(*, key_prefix: str, limit: int, window_seconds: int) -> Callable:
    async def _dep(request: Request):
        redis = get_redis()
        key = _rl_key(key_prefix, request)

        # INCR + EXPIRE (atomic enough for MVP; for strict atomicity use LUA, but this is standard pattern)
        cnt = await redis.incr(key)
        if cnt == 1:
            await redis.expire(key, window_seconds)

        if cnt > limit:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=429,
                detail=err(
                    request,
                    "rate_limited",
                    "Too many requests",
                    details={"retry_after_seconds": max(0, int(ttl if ttl is not None else window_seconds))},
                ),
            )

    return Depends(_dep)


signup_rate_limit = redis_rate_limit(
    key_prefix="auth:signup",
    limit=settings.AUTH_RL_SIGNUP_LIMIT,
    window_seconds=settings.AUTH_RL_WINDOW_SECONDS,
)

login_rate_limit = redis_rate_limit(
    key_prefix="auth:login",
    limit=settings.AUTH_RL_LOGIN_LIMIT,
    window_seconds=settings.AUTH_RL_WINDOW_SECONDS,
)

forgot_rate_limit = redis_rate_limit(
    key_prefix="auth:forgot",
    limit=settings.AUTH_RL_FORGOT_LIMIT,
    window_seconds=settings.AUTH_RL_WINDOW_SECONDS,
)
