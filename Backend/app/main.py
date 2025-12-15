from __future__ import annotations

import uuid

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, log
from app.db.init_db import init_db
from app.db.session import engine
from app.middleware.request_context import RequestContextMiddleware

configure_logging()

app = FastAPI(
    title="LifeMerge Backend (Skeleton)",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adds request_id + timezone context, returns request_id in all responses
app.add_middleware(RequestContextMiddleware)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def on_startup() -> None:
    # Skeleton convenience: create tables automatically.
    # In production, use Alembic migrations.
    await init_db(engine)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Ensure we always return a request_id for tracing, even on unexpected errors
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    log.exception("unhandled_exception", request_id=request_id, path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "Internal server error",
            },
            "request_id": request_id,
        },
        headers={"X-Request-Id": request_id},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Ensure API error format matches `{error:..., request_id}` across services.
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    payload = exc.detail if isinstance(exc.detail, dict) else {
        "error": {"code": "http_error", "message": str(exc.detail)},
        "request_id": request_id,
    }
    # hard-enforce request_id
    payload.setdefault("request_id", request_id)
    return JSONResponse(status_code=exc.status_code, content=payload, headers={"X-Request-Id": request_id})
