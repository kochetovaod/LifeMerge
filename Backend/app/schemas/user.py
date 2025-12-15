from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    timezone: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted: bool = False

    class Config:
        from_attributes = True
