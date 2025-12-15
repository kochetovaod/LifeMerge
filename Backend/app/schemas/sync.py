from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BatchSyncOperation(BaseModel):
    entity: Literal["task", "event", "finance"]
    action: Literal["upsert", "delete"]
    id: uuid.UUID | None = None
    data: dict | None = None
    updated_at: datetime


class BatchSyncResult(BaseModel):
    entity: str
    action: str
    id: uuid.UUID | None = None
    status: Literal["applied", "skipped", "unsupported", "error"]
    reason: str | None = None
    current: dict | None = None


class BatchSyncRequest(BaseModel):
    operations: list[BatchSyncOperation]
    request_id: str = Field(min_length=1, max_length=128)


class BatchSyncResponse(BaseModel):
    results: list[BatchSyncResult]
    request_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "entity": "task",
                        "action": "upsert",
                        "id": "c5ab350b-7254-4bc0-9865-808f036f8e8f",
                        "status": "applied",
                        "reason": None,
                        "current": {
                            "title": "Example",
                            "status": "todo",
                            "updated_at": "2024-01-01T00:00:00Z",
                        },
                    }
                ],
                "request_id": "req-123",
            }
        }
