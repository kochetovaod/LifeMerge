from __future__ import annotations

import uuid

import pytest


@pytest.mark.asyncio
async def test_missing_request_id_400(client, tasks_path):
    # Missing X-Request-Id should fail at middleware for mutating calls
    r = await client.post(tasks_path, json={"title": "x", "request_id": "r"}, headers={"X-Timezone": "UTC"})
    assert r.status_code == 400
    assert r.json().get("error", {}).get("code") == "missing_request_id"


@pytest.mark.asyncio
async def test_invalid_timezone_400(client, auth_paths):
    r = await client.post(
        auth_paths["forgot"],
        json={"email": "a@test.local"},
        headers={"X-Request-Id": str(uuid.uuid4()), "X-Timezone": "Not/A_Timezone"},
    )
    assert r.status_code == 400
    assert r.json().get("error", {}).get("code") == "invalid_timezone"


@pytest.mark.asyncio
async def test_rate_limit_signup_429(client, auth_paths, make_headers, redis_flush):
    # limit=2 from env (conftest); third should 429
    email = f"rl_{uuid.uuid4().hex[:10]}@test.local"
    for i in range(2):
        r = await client.post(
            auth_paths["signup"],
            json={"email": email, "password": "StrongPassw0rd!", "full_name": "Test", "timezone": "UTC"},
            headers=make_headers(rid=str(uuid.uuid4())),
        )
        # first request may be 200, second may be 409 (user_exists) depending on behavior;
        # the point is to consume rate-limit slots.
        assert r.status_code in (200, 409)

    r3 = await client.post(
        auth_paths["signup"],
        json={"email": email, "password": "StrongPassw0rd!", "full_name": "Test", "timezone": "UTC"},
        headers=make_headers(rid=str(uuid.uuid4())),
    )
    assert r3.status_code == 429
    assert r3.json().get("error", {}).get("code") == "rate_limited"
