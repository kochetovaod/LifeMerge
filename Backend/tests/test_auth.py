from __future__ import annotations

import uuid

import pytest


@pytest.mark.asyncio
async def test_signup_login_refresh_happy_path(client, auth_paths, make_headers, user_email, user_password, device_id, redis_flush):
    # signup
    h = make_headers(rid=str(uuid.uuid4()))
    r = await client.post(
        auth_paths["signup"],
        json={"email": user_email, "password": user_password, "full_name": "Test", "timezone": h["X-Timezone"]},
        headers=h,
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data

    # login
    h2 = make_headers(rid=str(uuid.uuid4()))
    r2 = await client.post(
        auth_paths["login"],
        json={"email": user_email, "password": user_password, "device_id": device_id},
        headers=h2,
    )
    assert r2.status_code == 200
    data2 = r2.json()["data"]
    assert "access_token" in data2
    assert "refresh_token" in data2

    # refresh
    h3 = make_headers(rid=str(uuid.uuid4()))
    r3 = await client.post(
        auth_paths["refresh"],
        json={"refresh_token": data2["refresh_token"], "device_id": device_id},
        headers=h3,
    )
    assert r3.status_code == 200
    data3 = r3.json()["data"]
    assert "access_token" in data3
    assert "refresh_token" in data3


@pytest.mark.asyncio
async def test_login_invalid_password(client, auth_paths, make_headers, user_email, user_password, device_id):
    h = make_headers(rid=str(uuid.uuid4()))
    r = await client.post(
        auth_paths["login"],
        json={"email": user_email, "password": "wrong", "device_id": device_id},
        headers=h,
    )
    assert r.status_code in (401, 400)
    body = r.json()
    assert body.get("error", {}).get("code") in ("invalid_credentials", "unauthorized")


@pytest.mark.asyncio
async def test_refresh_reuse_revokes_old_token(client, auth_paths, make_headers, user_email, user_password, device_id):
    # login to get refresh
    h = make_headers(rid=str(uuid.uuid4()))
    r = await client.post(
        auth_paths["login"],
        json={"email": user_email, "password": user_password, "device_id": device_id},
        headers=h,
    )
    assert r.status_code == 200
    refresh1 = r.json()["data"]["refresh_token"]

    # refresh -> rotates and revokes refresh1
    h2 = make_headers(rid=str(uuid.uuid4()))
    r2 = await client.post(auth_paths["refresh"], json={"refresh_token": refresh1, "device_id": device_id}, headers=h2)
    assert r2.status_code == 200

    # reuse refresh1 must fail
    h3 = make_headers(rid=str(uuid.uuid4()))
    r3 = await client.post(auth_paths["refresh"], json={"refresh_token": refresh1, "device_id": device_id}, headers=h3)
    assert r3.status_code == 401
    assert r3.json().get("error", {}).get("code") in ("invalid_refresh", "unauthorized")
