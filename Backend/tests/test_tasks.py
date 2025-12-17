from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_tasks_create_idempotent(client, auth_paths, tasks_path, make_headers, user_email, user_password, device_id):
    # login
    h = make_headers(rid=str(uuid.uuid4()))
    r = await client.post(
        auth_paths["login"],
        json={"email": user_email, "password": user_password, "device_id": device_id},
        headers=h,
    )
    assert r.status_code == 200
    access = r.json()["data"]["access_token"]

    # create task with idempotency key
    idem = str(uuid.uuid4())
    rid = str(uuid.uuid4())
    h2 = await auth_header(access, make_headers(rid=rid, idem=idem))
    body = {"title": "T1", "description": "D", "request_id": rid}

    r1 = await client.post(tasks_path, json=body, headers=h2)
    assert r1.status_code == 200
    t1 = r1.json()["data"]
    assert "id" in t1

    # repeat same request: must return same payload (same id)
    r2 = await client.post(tasks_path, json=body, headers=h2)
    assert r2.status_code == 200
    t2 = r2.json()["data"]
    assert t2["id"] == t1["id"]


@pytest.mark.asyncio
async def test_tasks_update_conflict_409(client, auth_paths, tasks_path, make_headers, user_email, user_password, device_id):
    # login
    h = make_headers(rid=str(uuid.uuid4()))
    r = await client.post(auth_paths["login"], json={"email": user_email, "password": user_password, "device_id": device_id}, headers=h)
    assert r.status_code == 200
    access = r.json()["data"]["access_token"]

    # create task
    rid_create = str(uuid.uuid4())
    h2 = await auth_header(access, make_headers(rid=rid_create, idem=str(uuid.uuid4())))
    r_create = await client.post(tasks_path, json={"title": "T-conflict", "request_id": rid_create}, headers=h2)
    assert r_create.status_code == 200
    task = r_create.json()["data"]
    task_id = task["id"]

    # patch with wrong updated_at
    rid_patch = str(uuid.uuid4())
    h3 = await auth_header(access, make_headers(rid=rid_patch, idem=str(uuid.uuid4())))
    wrong_updated = datetime(2000, 1, 1, tzinfo=timezone.utc).isoformat()
    r_patch = await client.patch(
        f"{tasks_path}/{task_id}",
        json={"title": "new", "updated_at": wrong_updated, "request_id": rid_patch},
        headers=h3,
    )
    assert r_patch.status_code == 409
    body = r_patch.json()
    assert body.get("error", {}).get("code") == "conflict"
    assert "current" in (body.get("error", {}).get("details") or {})


@pytest.mark.asyncio
async def test_tasks_delete_soft_and_list_hides_deleted(client, auth_paths, tasks_path, make_headers, user_email, user_password, device_id):
    # login
    h = make_headers(rid=str(uuid.uuid4()))
    r = await client.post(auth_paths["login"], json={"email": user_email, "password": user_password, "device_id": device_id}, headers=h)
    assert r.status_code == 200
    access = r.json()["data"]["access_token"]

    # create task
    rid_create = str(uuid.uuid4())
    h2 = await auth_header(access, make_headers(rid=rid_create, idem=str(uuid.uuid4())))
    r_create = await client.post(tasks_path, json={"title": "T-del", "request_id": rid_create}, headers=h2)
    assert r_create.status_code == 200
    task_id = r_create.json()["data"]["id"]

    # delete
    rid_del = str(uuid.uuid4())
    h3 = await auth_header(access, make_headers(rid=rid_del, idem=str(uuid.uuid4())))
    r_del = await client.request("DELETE", f"{tasks_path}/{task_id}", json={"request_id": rid_del}, headers=h3)
    assert r_del.status_code == 200

    # list should not include deleted
    h4 = await auth_header(access, make_headers(rid=str(uuid.uuid4())))
    r_list = await client.get(tasks_path, headers=h4)
    assert r_list.status_code == 200
    items = r_list.json()["data"]["items"]
    assert all(it["id"] != task_id for it in items)
