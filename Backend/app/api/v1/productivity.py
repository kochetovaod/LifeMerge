from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user
from app.core.response import err, ok
from app.schemas.productivity import (
    BudgetIn,
    BudgetOut,
    CalendarEventIn,
    CalendarEventOut,
    CalendarEventUpdateIn,
    DigestPreviewOut,
    FinanceSummaryOut,
    FinanceTransactionIn,
    FinanceTransactionOut,
    FinanceTransactionUpdateIn,
    GoalCreateIn,
    GoalOut,
    GoalProgressOut,
    GoalUpdateIn,
    InboxConvertIn,
    InboxCreateIn,
    InboxItemOut,
    NotificationTriggerIn,
    NotificationTriggerOut,
    SyncStatusOut,
)
from app.schemas.subscription import SubscriptionStatusOut
from app.services.subscription_service import activate_trial, subscription_status

router = APIRouter(prefix="/productivity")


# In-memory stores for the skeleton endpoints
_goals: dict[uuid.UUID, dict] = defaultdict(dict)
_events: dict[uuid.UUID, dict] = defaultdict(dict)
_inbox: dict[uuid.UUID, dict] = defaultdict(dict)
_finance: dict[uuid.UUID, dict] = defaultdict(dict)
_budgets: dict[uuid.UUID, dict[str, float]] = defaultdict(dict)
_notifications: dict[uuid.UUID, dict] = defaultdict(dict)

FREE_BUDGET_LIMIT = 1000.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_plan(user) -> SubscriptionStatusOut:
    return subscription_status(user)


@router.post("/subscription/activate-trial")
async def activate_trial_plan(request: Request, current_user=Depends(get_current_user)):
    status = subscription_status(current_user)
    if status.current_plan == "pro":
        raise HTTPException(status_code=400, detail=err(request, "already_pro", "User already has Pro"))

    updated = activate_trial(current_user)
    payload = subscription_status(updated).model_dump()
    return ok(request, payload)


@router.get("/goals", response_model=list[GoalOut])
async def list_goals(request: Request, current_user=Depends(get_current_user)):
    goals = list(_goals[current_user.id].values())
    return ok(request, [GoalOut(**g) for g in goals])


@router.post("/goals", response_model=GoalOut)
async def create_goal(request: Request, body: GoalCreateIn, current_user=Depends(get_current_user)):
    goal_id = uuid.uuid4()
    record = {
        "id": goal_id,
        "title": body.title,
        "description": body.description,
        "target_date": body.target_date,
        "progress": 0.0,
        "tasks_total": 0,
        "tasks_completed": 0,
    }
    _goals[current_user.id][goal_id] = record
    return ok(request, GoalOut(**record).model_dump())


@router.patch("/goals/{goal_id}", response_model=GoalOut)
async def update_goal(
    request: Request, goal_id: uuid.UUID, body: GoalUpdateIn, current_user=Depends(get_current_user)
):
    goal = _goals[current_user.id].get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Goal not found"))

    for field, value in body.model_dump(exclude_unset=True).items():
        goal[field] = value
    return ok(request, GoalOut(**goal).model_dump())


@router.get("/goals/{goal_id}/progress", response_model=GoalProgressOut)
async def goal_progress(request: Request, goal_id: uuid.UUID, current_user=Depends(get_current_user)):
    goal = _goals[current_user.id].get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Goal not found"))

    total = max(goal.get("tasks_total", 0), 1)
    completed = goal.get("tasks_completed", 0)
    percent = min(100.0, (completed / total) * 100)
    payload = GoalProgressOut(
        id=goal_id,
        percent_complete=percent,
        tasks_total=total,
        tasks_completed=completed,
        updated_at=_now(),
    )
    return ok(request, payload.model_dump())


@router.get("/calendar/events", response_model=list[CalendarEventOut])
async def list_events(request: Request, current_user=Depends(get_current_user)):
    events = list(_events[current_user.id].values())
    return ok(request, [CalendarEventOut(**e) for e in events])


@router.post("/calendar/events", response_model=CalendarEventOut)
async def create_event(request: Request, body: CalendarEventIn, current_user=Depends(get_current_user)):
    event_id = uuid.uuid4()
    record = {
        "id": event_id,
        "title": body.title,
        "start_at": body.start_at,
        "end_at": body.end_at,
        "recurrence": body.recurrence,
        "parallel_with": body.parallel_with,
    }
    _events[current_user.id][event_id] = record
    return ok(request, CalendarEventOut(**record).model_dump())


@router.patch("/calendar/events/{event_id}", response_model=CalendarEventOut)
async def update_event(
    request: Request, event_id: uuid.UUID, body: CalendarEventUpdateIn, current_user=Depends(get_current_user)
):
    event = _events[current_user.id].get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Event not found"))

    updates = body.model_dump(exclude_unset=True)
    if updates.get("end_at") and updates.get("start_at"):
        if updates["end_at"] <= updates["start_at"]:
            raise HTTPException(status_code=400, detail=err(request, "validation_error", "end_at must be after start_at"))

    for field, value in updates.items():
        event[field] = value
    return ok(request, CalendarEventOut(**event).model_dump())


@router.post("/inbox", response_model=InboxItemOut)
async def add_inbox_note(request: Request, body: InboxCreateIn, current_user=Depends(get_current_user)):
    item_id = uuid.uuid4()
    record = {
        "id": item_id,
        "note": body.note,
        "created_at": _now(),
        "converted_to": None,
    }
    _inbox[current_user.id][item_id] = record
    return ok(request, InboxItemOut(**record).model_dump())


@router.post("/inbox/{item_id}/convert", response_model=InboxItemOut)
async def convert_inbox_note(
    request: Request, item_id: uuid.UUID, body: InboxConvertIn, current_user=Depends(get_current_user)
):
    item = _inbox[current_user.id].get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Inbox item not found"))

    item["converted_to"] = body.target
    return ok(request, InboxItemOut(**item).model_dump())


@router.get("/finance/transactions", response_model=list[FinanceTransactionOut])
async def list_transactions(request: Request, current_user=Depends(get_current_user)):
    txs = list(_finance[current_user.id].values())
    return ok(request, [FinanceTransactionOut(**t) for t in txs])


@router.post("/finance/transactions", response_model=FinanceTransactionOut)
async def create_transaction(
    request: Request, body: FinanceTransactionIn, current_user=Depends(get_current_user)
):
    tx_id = uuid.uuid4()
    record = {
        "id": tx_id,
        **body.model_dump(),
    }
    _finance[current_user.id][tx_id] = record
    return ok(request, FinanceTransactionOut(**record).model_dump())


@router.patch("/finance/transactions/{tx_id}", response_model=FinanceTransactionOut)
async def update_transaction(
    request: Request, tx_id: uuid.UUID, body: FinanceTransactionUpdateIn, current_user=Depends(get_current_user)
):
    tx = _finance[current_user.id].get(tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Transaction not found"))

    for field, value in body.model_dump(exclude_unset=True).items():
        tx[field] = value
    return ok(request, FinanceTransactionOut(**tx).model_dump())


@router.delete("/finance/transactions/{tx_id}")
async def delete_transaction(request: Request, tx_id: uuid.UUID, current_user=Depends(get_current_user)):
    tx = _finance[current_user.id].pop(tx_id, None)
    if not tx:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Transaction not found"))
    return ok(request, {"status": "deleted"})


@router.get("/finance/summary", response_model=FinanceSummaryOut)
async def finance_summary(request: Request, month: str, current_user=Depends(get_current_user)):
    txs = _finance[current_user.id].values()
    income = sum(t["amount"] for t in txs if t["type"] == "income")
    expenses = sum(t["amount"] for t in txs if t["type"] == "expense")
    budgets = _budgets[current_user.id]
    payload = FinanceSummaryOut(
        month=month,
        income_total=income,
        expense_total=expenses,
        net=income - expenses,
        budgets=budgets,
    )
    return ok(request, payload.model_dump())


@router.post("/finance/budgets", response_model=BudgetOut)
async def set_budget(request: Request, body: BudgetIn, current_user=Depends(get_current_user)):
    status = _get_plan(current_user)
    limited = False
    amount = body.amount
    if status.current_plan == "free" and body.amount > FREE_BUDGET_LIMIT:
        limited = True
        amount = FREE_BUDGET_LIMIT

    _budgets[current_user.id][body.month] = amount
    return ok(request, BudgetOut(month=body.month, amount=amount, limited=limited).model_dump())


@router.post("/notifications/triggers", response_model=NotificationTriggerOut)
async def create_notification_trigger(
    request: Request, body: NotificationTriggerIn, current_user=Depends(get_current_user)
):
    trig_id = uuid.uuid4()
    record = NotificationTriggerOut(
        id=trig_id,
        entity=body.entity,
        entity_id=body.entity_id,
        lead_minutes=body.lead_minutes,
        remind_at=body.remind_at,
        channel="push",
    )
    _notifications[current_user.id][trig_id] = record.model_dump()
    return ok(request, record.model_dump())


@router.get("/notifications/digest", response_model=DigestPreviewOut)
async def digest_preview(request: Request, cadence: str = "daily", current_user=Depends(get_current_user)):
    items = [
        "Upcoming tasks and events summarized",
        "Finance reminders and recurring payments",
        "Goal progress snapshot",
    ]
    payload = DigestPreviewOut(cadence=cadence, items=items)
    return ok(request, payload.model_dump())


@router.get("/sync/status", response_model=SyncStatusOut)
async def sync_status(request: Request, current_user=Depends(get_current_user)):
    pending: list[str] = []
    if _inbox[current_user.id]:
        pending.append("inbox")
    if _events[current_user.id]:
        pending.append("calendar")
    status = SyncStatusOut(
        queue_depth=len(pending),
        last_synced_at=_now(),
        pending_entities=pending,
        status="syncing" if pending else "idle",
    )
    return ok(request, status.model_dump())

