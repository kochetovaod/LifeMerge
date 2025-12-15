from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base
from app.models.user import User  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.idempotency import IdempotencyKey  # noqa: F401


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
