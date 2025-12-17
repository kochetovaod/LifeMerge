from __future__ import annotations

import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

# IMPORTANT:
# Set env BEFORE importing app (settings are read at import time)
os.environ.setdefault("ENV", "local")

# test DB / Redis (docker-compose.test.yml)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://lifemerge:lifemerge@localhost:55432/lifemerge_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:56379/0")

# Make rate limits tiny for tests
os.environ.setdefault("AUTH_RL_WINDOW_SECONDS", "60")
os.environ.setdefault("AUTH_RL_SIGNUP_LIMIT", "2")
os.environ.setdefault("AUTH_RL_LOGIN_LIMIT", "3")
os.environ.setdefault("AUTH_RL_FORGOT_LIMIT", "2")

# alembic (stage/prod check is disabled in local)
# still used by some code paths (keep default)
os.environ.setdefault("PYTHONUNBUFFERED", "1")


@pytest.fixture(scope="session")
def any_tz() -> str:
    return "UTC"


def _headers(*, tz: str, rid: str | None = None, idem: str | None = None) -> dict[str, str]:
    h = {"X-Timezone": tz}
    if rid is not None:
        h["X-Request-Id"] = rid
    if idem is not None:
        h["X-Idempotency-Key"] = idem
    return h


@pytest.fixture(scope="session")
def make_headers(any_tz):
    def _mk(rid: str | None = None, idem: str | None = None, tz: str | None = None) -> dict[str, str]:
        return _headers(tz=tz or any_tz, rid=rid, idem=idem)
    return _mk


@pytest.fixture(scope="session")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
def user_email() -> str:
    return f"u_{uuid.uuid4().hex[:10]}@test.local"


@pytest.fixture(scope="session")
def user_password() -> str:
    return "StrongPassw0rd!"


@pytest.fixture(scope="session")
def device_id() -> str:
    return "ios-device-1"


@pytest.fixture()
async def redis_flush():
    try:
        from app.infra.redis_client import get_redis
        r = get_redis()
        await r.flushdb()
    except Exception:
        # tests that don't hit rate-limit should still run
        pass
    yield
    try:
        from app.infra.redis_client import get_redis
        r = get_redis()
        await r.flushdb()
    except Exception:
        pass


@pytest.fixture(scope="session")
def auth_paths():
    return {
        "signup": "/v1/auth/signup",
        "login": "/v1/auth/login",
        "refresh": "/v1/auth/refresh",
        "forgot": "/v1/auth/forgot",
    }


@pytest.fixture(scope="session")
def tasks_path():
    return "/v1/tasks"


async def signup(
    client: AsyncClient,
    *,
    path: str,
    email: str,
    password: str,
    headers: dict[str, str],
):
    body = {"email": email, "password": password, "full_name": "Test", "timezone": headers["X-Timezone"]}
    return await client.post(path, json=body, headers=headers)


async def login(
    client: AsyncClient,
    *,
    path: str,
    email: str,
    password: str,
    device_id: str,
    headers: dict[str, str],
):
    body = {"email": email, "password": password, "device_id": device_id}
    return await client.post(path, json=body, headers=headers)


async def auth_header(access_token: str, headers: dict[str, str]) -> dict[str, str]:
    h = dict(headers)
    h["Authorization"] = f"Bearer {access_token}"
    return h
