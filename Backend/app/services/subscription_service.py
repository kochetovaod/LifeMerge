from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.models.user import User
from app.schemas.subscription import PlanLimits, SubscriptionStatusOut

TRIAL_PERIOD = timedelta(days=settings.TRIAL_PERIOD_DAYS)


def _resolve_trial_dates(user: User) -> tuple[datetime | None, datetime | None]:
    start = user.trial_started_at or user.created_at
    if start and not user.trial_started_at:
        user.trial_started_at = start

    if user.trial_ends_at:
        end = user.trial_ends_at
    elif start:
        end = start + TRIAL_PERIOD
    else:
        end = None
    return start, end


def activate_trial(user: User) -> User:
    """Force-start a trial window for the given user."""

    now = datetime.now(timezone.utc)
    user.trial_started_at = now
    user.trial_ends_at = now + TRIAL_PERIOD
    user.is_pro = False
    return user


def subscription_status(user: User) -> SubscriptionStatusOut:
    now = datetime.now(timezone.utc)
    trial_start, trial_end = _resolve_trial_dates(user)

    trial_active = bool(trial_start and trial_end and trial_start <= now < trial_end)
    if user.is_pro:
        current_plan = "pro"
    elif trial_active:
        current_plan = "trial"
    else:
        current_plan = "free"

    limits = {
        "free": PlanLimits(
            ai_planner_access=False,
            analytics_access=False,
            max_ai_plans_per_week=0,
            max_goals=settings.FREE_MAX_GOALS,
            max_tasks=settings.FREE_MAX_TASKS,
            max_finance_accounts=settings.FREE_MAX_FINANCE_ACCOUNTS,
            notes="AI planner and advanced automations are not available on the Free plan.",
        ),
        "trial": PlanLimits(
            ai_planner_access=True,
            analytics_access=True,
            max_ai_plans_per_week=settings.AI_PLANNER_MAX_BATCH,
            max_goals=settings.FREE_MAX_GOALS,
            max_tasks=settings.FREE_MAX_TASKS,
            max_finance_accounts=settings.FREE_MAX_FINANCE_ACCOUNTS,
            notes="Trial users can access AI with soft limits inherited from the Free tier.",
        ),
        "pro": PlanLimits(
            ai_planner_access=True,
            analytics_access=True,
            max_ai_plans_per_week=None,
            notes="Full AI planner access with no weekly cap.",
        ),
    }

    return SubscriptionStatusOut(
        current_plan=current_plan,
        trial_started_at=trial_start,
        trial_ends_at=trial_end,
        trial_active=trial_active,
        limits=limits,
    )
