from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base
from app.models.user import User  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.idempotency import IdempotencyKey  # noqa: F401
from app.models.goal import Goal  # noqa: F401
from app.models.calendar_event import CalendarEvent  # noqa: F401
from app.models.inbox_item import InboxItem  # noqa: F401
from app.models.finance import Budget, FinanceAccount, FinanceTransaction  # noqa: F401
from app.models.push_device import PushDeviceToken  # noqa: F401
from app.models.notification import DigestSchedule, NotificationTrigger  # noqa: F401
from app.models.sync_operation import SyncOperation  # noqa: F401
from app.models.ai_plan import AiPlanRun  # noqa: F401
from app.models.subscription_state import SubscriptionState  # noqa: F401
from app.infrastructure.models.planner_models import SQLPlannerPlan, SQLPlannerSlot, SQLPlannerConflict

async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
