from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PlanLimits(BaseModel):
    ai_planner_access: bool
    max_ai_plans_per_week: int | None = None
    analytics_access: bool = False
    max_goals: int | None = None
    max_tasks: int | None = None
    max_finance_accounts: int | None = None
    notes: str | None = None


class SubscriptionStatusOut(BaseModel):
    current_plan: Literal["free", "trial", "pro"]
    trial_started_at: datetime | None
    trial_ends_at: datetime | None
    trial_active: bool
    limits: dict[str, PlanLimits]
