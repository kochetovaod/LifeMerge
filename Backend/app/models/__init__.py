from __future__ import annotations

# Import all models so Alembic sees them via Base.metadata
from app.models.user import User  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.idempotency import IdempotencyKey  # noqa: F401

from app.models.goal import Goal  # noqa: F401
from app.models.calendar_event import CalendarEvent  # noqa: F401
from app.models.inbox_item import InboxItem  # noqa: F401
from app.models.finance import FinanceAccount, FinanceTransaction, Budget  # noqa: F401
from app.models.notification import NotificationTrigger, DigestSchedule  # noqa: F401
from app.models.subscription_state import SubscriptionState  # noqa: F401
from app.models.sync_operation import SyncOperation  # noqa: F401
