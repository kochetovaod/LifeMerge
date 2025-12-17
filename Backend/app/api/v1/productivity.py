from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.response import err, ok
from app.db.session import get_db
from app.models.calendar_event import CalendarEvent
from app.models.finance import Budget, FinanceTransaction
from app.models.goal import Goal
from app.models.inbox_item import InboxItem
from app.models.notification import NotificationTrigger
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


# ----------------------
# Goals
# ----------------------
@router.get("/goals", response_model=list[GoalOut])
async def list_goals(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    updated_from: datetime | None = None,
):
    q = select(Goal).where(Goal.user_id == current_user.id)
    if hasattr(Goal, "deleted"):
        q = q.where(Goal.deleted == False)  # noqa: E712
    if updated_from is not None and hasattr(Goal, "updated_at"):
        q = q.where(Goal.updated_at >= updated_from)
    res = await db.execute(q.order_by(Goal.created_at.desc() if hasattr(Goal, "created_at") else Goal.id))
    goals = list(res.scalars())

    items: list[GoalOut] = []
    for g in goals:
        items.append(
            GoalOut(
                id=g.id,
                title=g.title,
                description=getattr(g, "description", None),
                target_date=getattr(g, "target_date", None),
                progress=float(getattr(g, "progress", 0.0) or 0.0),
                tasks_total=int(getattr(g, "tasks_total", 0) or 0),
                tasks_completed=int(getattr(g, "tasks_completed", 0) or 0),
            )
        )
    return ok(request, [i.model_dump() for i in items])


@router.post("/goals", response_model=GoalOut)
async def create_goal(
    request: Request,
    body: GoalCreateIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    g = Goal(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        target_date=body.target_date,
        progress=0.0,
        tasks_total=0,
        tasks_completed=0,
        created_at=_now() if hasattr(Goal, "created_at") else None,
        updated_at=_now() if hasattr(Goal, "updated_at") else None,
        deleted=False if hasattr(Goal, "deleted") else None,
    )
    db.add(g)
    await db.commit()
    await db.refresh(g)

    out = GoalOut(
        id=g.id,
        title=g.title,
        description=getattr(g, "description", None),
        target_date=getattr(g, "target_date", None),
        progress=float(getattr(g, "progress", 0.0) or 0.0),
        tasks_total=int(getattr(g, "tasks_total", 0) or 0),
        tasks_completed=int(getattr(g, "tasks_completed", 0) or 0),
    )
    return ok(request, out.model_dump())


@router.patch("/goals/{goal_id}", response_model=GoalOut)
async def update_goal(
    request: Request,
    goal_id: uuid.UUID,
    body: GoalUpdateIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id))
    g = res.scalar_one_or_none()
    if not g or (hasattr(g, "deleted") and g.deleted):
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Goal not found"))

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(g, field, value)
    if hasattr(g, "updated_at"):
        g.updated_at = _now()

    await db.commit()
    await db.refresh(g)

    out = GoalOut(
        id=g.id,
        title=g.title,
        description=getattr(g, "description", None),
        target_date=getattr(g, "target_date", None),
        progress=float(getattr(g, "progress", 0.0) or 0.0),
        tasks_total=int(getattr(g, "tasks_total", 0) or 0),
        tasks_completed=int(getattr(g, "tasks_completed", 0) or 0),
    )
    return ok(request, out.model_dump())


@router.get("/goals/{goal_id}/progress", response_model=GoalProgressOut)
async def goal_progress(
    request: Request,
    goal_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id))
    g = res.scalar_one_or_none()
    if not g or (hasattr(g, "deleted") and g.deleted):
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Goal not found"))

    total = int(getattr(g, "tasks_total", 0) or 0)
    completed = int(getattr(g, "tasks_completed", 0) or 0)
    denom = max(total, 1)
    percent = min(100.0, (completed / denom) * 100.0)

    payload = GoalProgressOut(
        id=g.id,
        percent_complete=percent,
        tasks_total=total,
        tasks_completed=completed,
        updated_at=getattr(g, "updated_at", _now()),
    )
    return ok(request, payload.model_dump())


# ----------------------
# Calendar
# ----------------------
@router.get("/calendar/events", response_model=list[CalendarEventOut])
async def list_events(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    updated_from: datetime | None = None,
):
    q = select(CalendarEvent).where(CalendarEvent.user_id == current_user.id)
    if hasattr(CalendarEvent, "deleted"):
        q = q.where(CalendarEvent.deleted == False)  # noqa: E712
    if updated_from is not None and hasattr(CalendarEvent, "updated_at"):
        q = q.where(CalendarEvent.updated_at >= updated_from)
    res = await db.execute(q.order_by(CalendarEvent.start_at.desc() if hasattr(CalendarEvent, "start_at") else CalendarEvent.id))
    events = list(res.scalars())

    out: list[CalendarEventOut] = []
    for e in events:
        out.append(
            CalendarEventOut(
                id=e.id,
                title=e.title,
                start_at=e.start_at,
                end_at=e.end_at,
                recurrence=getattr(e, "recurrence", None),
                parallel_with=getattr(e, "parallel_with", []) or [],
            )
        )
    return ok(request, [i.model_dump() for i in out])


@router.post("/calendar/events", response_model=CalendarEventOut)
async def create_event(
    request: Request,
    body: CalendarEventIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.end_at <= body.start_at:
        raise HTTPException(status_code=400, detail=err(request, "validation_error", "end_at must be after start_at"))

    e = CalendarEvent(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title=body.title,
        start_at=body.start_at,
        end_at=body.end_at,
        recurrence=body.recurrence,
        parallel_with=body.parallel_with,
        created_at=_now() if hasattr(CalendarEvent, "created_at") else None,
        updated_at=_now() if hasattr(CalendarEvent, "updated_at") else None,
        deleted=False if hasattr(CalendarEvent, "deleted") else None,
    )
    db.add(e)
    await db.commit()
    await db.refresh(e)

    out = CalendarEventOut(
        id=e.id,
        title=e.title,
        start_at=e.start_at,
        end_at=e.end_at,
        recurrence=getattr(e, "recurrence", None),
        parallel_with=getattr(e, "parallel_with", []) or [],
    )
    return ok(request, out.model_dump())


@router.patch("/calendar/events/{event_id}", response_model=CalendarEventOut)
async def update_event(
    request: Request,
    event_id: uuid.UUID,
    body: CalendarEventUpdateIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id))
    e = res.scalar_one_or_none()
    if not e or (hasattr(e, "deleted") and e.deleted):
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Event not found"))

    updates = body.model_dump(exclude_unset=True)
    start_at = updates.get("start_at", getattr(e, "start_at", None))
    end_at = updates.get("end_at", getattr(e, "end_at", None))
    if start_at and end_at and end_at <= start_at:
        raise HTTPException(status_code=400, detail=err(request, "validation_error", "end_at must be after start_at"))

    for field, value in updates.items():
        setattr(e, field, value)
    if hasattr(e, "updated_at"):
        e.updated_at = _now()

    await db.commit()
    await db.refresh(e)

    out = CalendarEventOut(
        id=e.id,
        title=e.title,
        start_at=e.start_at,
        end_at=e.end_at,
        recurrence=getattr(e, "recurrence", None),
        parallel_with=getattr(e, "parallel_with", []) or [],
    )
    return ok(request, out.model_dump())


# ----------------------
# Inbox
# ----------------------
@router.post("/inbox", response_model=InboxItemOut)
async def add_inbox_note(
    request: Request,
    body: InboxCreateIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = InboxItem(
        id=uuid.uuid4(),
        user_id=current_user.id,
        note=body.note,
        created_at=_now(),
        converted_to=None,
        deleted=False if hasattr(InboxItem, "deleted") else None,
        updated_at=_now() if hasattr(InboxItem, "updated_at") else None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    out = InboxItemOut(id=item.id, note=item.note, created_at=item.created_at, converted_to=getattr(item, "converted_to", None))
    return ok(request, out.model_dump())


@router.post("/inbox/{item_id}/convert", response_model=InboxItemOut)
async def convert_inbox_note(
    request: Request,
    item_id: uuid.UUID,
    body: InboxConvertIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(InboxItem).where(InboxItem.id == item_id, InboxItem.user_id == current_user.id))
    item = res.scalar_one_or_none()
    if not item or (hasattr(item, "deleted") and item.deleted):
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Inbox item not found"))

    item.converted_to = body.target
    if hasattr(item, "updated_at"):
        item.updated_at = _now()

    await db.commit()
    await db.refresh(item)

    out = InboxItemOut(id=item.id, note=item.note, created_at=item.created_at, converted_to=item.converted_to)
    return ok(request, out.model_dump())


# ----------------------
# Finance
# ----------------------
@router.get("/finance/transactions", response_model=list[FinanceTransactionOut])
async def list_transactions(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    updated_from: datetime | None = None,
):
    q = select(FinanceTransaction).where(FinanceTransaction.user_id == current_user.id)
    if hasattr(FinanceTransaction, "deleted"):
        q = q.where(FinanceTransaction.deleted == False)  # noqa: E712
    if updated_from is not None and hasattr(FinanceTransaction, "updated_at"):
        q = q.where(FinanceTransaction.updated_at >= updated_from)
    res = await db.execute(q.order_by(FinanceTransaction.occurred_at.desc() if hasattr(FinanceTransaction, "occurred_at") else FinanceTransaction.id))
    txs = list(res.scalars())

    out: list[FinanceTransactionOut] = []
    for t in txs:
        out.append(
            FinanceTransactionOut(
                id=t.id,
                type=t.type,
                amount=float(t.amount),
                currency=t.currency,
                category=t.category,
                occurred_at=t.occurred_at,
                recurring=bool(getattr(t, "recurring", False)),
            )
        )
    return ok(request, [i.model_dump() for i in out])


@router.post("/finance/transactions", response_model=FinanceTransactionOut)
async def create_transaction(
    request: Request,
    body: FinanceTransactionIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    t = FinanceTransaction(
        id=uuid.uuid4(),
        user_id=current_user.id,
        type=body.type,
        amount=body.amount,
        currency=body.currency,
        category=body.category,
        occurred_at=body.occurred_at,
        recurring=body.recurring,
        created_at=_now() if hasattr(FinanceTransaction, "created_at") else None,
        updated_at=_now() if hasattr(FinanceTransaction, "updated_at") else None,
        deleted=False if hasattr(FinanceTransaction, "deleted") else None,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)

    out = FinanceTransactionOut(
        id=t.id,
        type=t.type,
        amount=float(t.amount),
        currency=t.currency,
        category=t.category,
        occurred_at=t.occurred_at,
        recurring=bool(getattr(t, "recurring", False)),
    )
    return ok(request, out.model_dump())


@router.patch("/finance/transactions/{tx_id}", response_model=FinanceTransactionOut)
async def update_transaction(
    request: Request,
    tx_id: uuid.UUID,
    body: FinanceTransactionUpdateIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(FinanceTransaction).where(FinanceTransaction.id == tx_id, FinanceTransaction.user_id == current_user.id))
    t = res.scalar_one_or_none()
    if not t or (hasattr(t, "deleted") and t.deleted):
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Transaction not found"))

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(t, field, value)
    if hasattr(t, "updated_at"):
        t.updated_at = _now()

    await db.commit()
    await db.refresh(t)

    out = FinanceTransactionOut(
        id=t.id,
        type=t.type,
        amount=float(t.amount),
        currency=t.currency,
        category=t.category,
        occurred_at=t.occurred_at,
        recurring=bool(getattr(t, "recurring", False)),
    )
    return ok(request, out.model_dump())


@router.delete("/finance/transactions/{tx_id}")
async def delete_transaction(
    request: Request,
    tx_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(FinanceTransaction).where(FinanceTransaction.id == tx_id, FinanceTransaction.user_id == current_user.id))
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail=err(request, "not_found", "Transaction not found"))

    if hasattr(t, "deleted"):
        t.deleted = True
        if hasattr(t, "updated_at"):
            t.updated_at = _now()
        await db.commit()
        return ok(request, {"status": "deleted"})

    # fallback hard delete if model has no deleted flag
    await db.execute(delete(FinanceTransaction).where(FinanceTransaction.id == tx_id))
    await db.commit()
    return ok(request, {"status": "deleted"})


@router.get("/finance/summary", response_model=FinanceSummaryOut)
async def finance_summary(
    request: Request,
    month: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(FinanceTransaction).where(FinanceTransaction.user_id == current_user.id)
    if hasattr(FinanceTransaction, "deleted"):
        q = q.where(FinanceTransaction.deleted == False)  # noqa: E712
    res = await db.execute(q)
    txs = list(res.scalars())

    income = sum(float(t.amount) for t in txs if t.type == "income")
    expenses = sum(float(t.amount) for t in txs if t.type == "expense")

    bq = select(Budget).where(Budget.user_id == current_user.id)
    res2 = await db.execute(bq)
    budgets_rows = list(res2.scalars())
    budgets: dict[str, float] = {}
    for b in budgets_rows:
        budgets[getattr(b, "month")] = float(getattr(b, "amount"))

    payload = FinanceSummaryOut(
        month=month,
        income_total=income,
        expense_total=expenses,
        net=income - expenses,
        budgets=budgets,
    )
    return ok(request, payload.model_dump())


@router.post("/finance/budgets", response_model=BudgetOut)
async def set_budget(
    request: Request,
    body: BudgetIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    status = _get_plan(current_user)
    limited = False
    amount = body.amount
    if status.current_plan == "free" and body.amount > FREE_BUDGET_LIMIT:
        limited = True
        amount = FREE_BUDGET_LIMIT

    res = await db.execute(select(Budget).where(Budget.user_id == current_user.id, Budget.month == body.month))
    b = res.scalar_one_or_none()
    if b is None:
        b = Budget(
            id=uuid.uuid4() if hasattr(Budget, "id") else None,
            user_id=current_user.id,
            month=body.month,
            amount=amount,
            created_at=_now() if hasattr(Budget, "created_at") else None,
            updated_at=_now() if hasattr(Budget, "updated_at") else None,
            deleted=False if hasattr(Budget, "deleted") else None,
        )
        db.add(b)
    else:
        b.amount = amount
        if hasattr(b, "updated_at"):
            b.updated_at = _now()

    await db.commit()
    return ok(request, BudgetOut(month=body.month, amount=amount, limited=limited).model_dump())


# ----------------------
# Notifications
# ----------------------
@router.post("/notifications/triggers", response_model=NotificationTriggerOut)
async def create_notification_trigger(
    request: Request,
    body: NotificationTriggerIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    trig = NotificationTrigger(
        id=uuid.uuid4(),
        user_id=current_user.id,
        entity=body.entity,
        entity_id=body.entity_id,
        lead_minutes=body.lead_minutes,
        remind_at=body.remind_at,
        channel="push",
        created_at=_now() if hasattr(NotificationTrigger, "created_at") else None,
        updated_at=_now() if hasattr(NotificationTrigger, "updated_at") else None,
        deleted=False if hasattr(NotificationTrigger, "deleted") else None,
    )
    db.add(trig)
    await db.commit()
    await db.refresh(trig)

    out = NotificationTriggerOut(
        id=trig.id,
        entity=trig.entity,
        entity_id=trig.entity_id,
        lead_minutes=trig.lead_minutes,
        remind_at=trig.remind_at,
        channel=trig.channel,
    )
    return ok(request, out.model_dump())


@router.get("/notifications/digest", response_model=DigestPreviewOut)
async def digest_preview(request: Request, cadence: str = "daily", current_user=Depends(get_current_user)):
    items = [
        "Upcoming tasks and events summarized",
        "Finance reminders and recurring payments",
        "Goal progress snapshot",
    ]
    payload = DigestPreviewOut(cadence=cadence, items=items)
    return ok(request, payload.model_dump())


# ----------------------
# Sync status (MVP)
# ----------------------
@router.get("/sync/status", response_model=SyncStatusOut)
async def sync_status(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pending_entities: list[str] = []

    # Простой сигнал “есть что синкать” по данным (MVP).
    # Если появится таблица sync_queue/outbox — переключим на неё без изменения контракта.
    inbox_count = (await db.execute(select(func.count()).select_from(InboxItem).where(InboxItem.user_id == current_user.id))).scalar_one()
    events_count = (await db.execute(select(func.count()).select_from(CalendarEvent).where(CalendarEvent.user_id == current_user.id))).scalar_one()

    if inbox_count:
        pending_entities.append("inbox")
    if events_count:
        pending_entities.append("calendar")

    status = SyncStatusOut(
        queue_depth=len(pending_entities),
        last_synced_at=_now(),
        pending_entities=pending_entities,
        status="syncing" if pending_entities else "idle",
    )
    return ok(request, status.model_dump())
