from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, FieldValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = structlog.get_logger()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    API_PREFIX: str = "/v1"
    AI_INTERNAL_TOKEN: str = "ai-internal-token"
    PLANNER_MAX_BATCH: int = 64
    DEFAULT_TIMEZONE: str = "UTC"


auth_header_name = "X-AI-Internal-Token"
settings = Settings()

app = FastAPI(title="LifeMerge AI Planner", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WorkScheduleEntry(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @field_validator("end_time")
    @classmethod
    def validate_range(cls, end_time: time, info: FieldValidationInfo):
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class PlannerRun(BaseModel):
    plan_request_id: uuid.UUID
    week_start: date | None = None
    work_schedule: list[WorkScheduleEntry] = Field(default_factory=list)
    subscription_status: Literal["pro", "trial", "free"] = "pro"


class BatchPlannerRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    requests: list[PlannerRun]

    @field_validator("requests")
    @classmethod
    def validate_batch_size(cls, requests: list[PlannerRun]):
        if len(requests) > settings.PLANNER_MAX_BATCH:
            raise ValueError(f"batch too large (>{settings.PLANNER_MAX_BATCH})")
        return requests


class PlannerSlotOut(BaseModel):
    slot_id: uuid.UUID
    task_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    start_at: datetime
    end_at: datetime


class PlannerPlanOut(BaseModel):
    plan_request_id: uuid.UUID
    status: str = "ready"
    slots: list[PlannerSlotOut]


class BatchPlannerResponse(BaseModel):
    plans: list[PlannerPlanOut]
    request_id: str


async def ensure_internal_access(token: str = Header(alias=auth_header_name)) -> None:
    if token != settings.AI_INTERNAL_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(f"{settings.API_PREFIX}/planner/batch-run", response_model=BatchPlannerResponse)
async def batch_run(
    payload: BatchPlannerRequest,
    request: Request,
    _: None = Depends(ensure_internal_access),
):
    plans: list[PlannerPlanOut] = []
    for item in payload.requests:
        slots = _generate_slots(week_start=item.week_start)
        plan = PlannerPlanOut(plan_request_id=item.plan_request_id, status="ready", slots=slots)
        plans.append(plan)

    log.info(
        "ai_batch_plan_generated",
        batch_size=len(plans),
        request_id=payload.request_id,
        client_request_id=request.headers.get("x-request-id"),
    )
    return BatchPlannerResponse(plans=plans, request_id=payload.request_id)


def _generate_slots(*, week_start: date | None) -> list[PlannerSlotOut]:
    start_date = week_start or datetime.now(timezone.utc).date()
    base_dt = datetime.combine(start_date, time(hour=9), tzinfo=timezone.utc)

    slots: list[PlannerSlotOut] = []
    durations = [timedelta(minutes=90), timedelta(minutes=60), timedelta(minutes=45)]
    titles = ["Deep work", "Focus session", "Wrap-up"]

    for idx, delta in enumerate(durations):
        start_at = base_dt + timedelta(hours=idx * 3)
        end_at = start_at + delta
        slot = PlannerSlotOut(
            slot_id=uuid.uuid4(),
            title=titles[idx],
            description=f"Suggested block {idx + 1}",
            start_at=start_at,
            end_at=end_at,
        )
        slots.append(slot)

    return slots
