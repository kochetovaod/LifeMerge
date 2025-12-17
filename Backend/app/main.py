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
from app.db.schema_check import ensure_schema_up_to_date
from app.middleware.idempotency_snapshot import IdempotencySnapshotMiddleware
from app.infra.redis_client import get_redis

configure_logging()

# Проверка безопасности секретов при старте
def validate_security_config() -> None:
    """Проверяем конфигурацию безопасности при запуске приложения."""
    insecure_defaults = settings.INSECURE_DEFAULT_VALUES
    
    # В dev-окружении только логируем предупреждения
    if settings.APP_ENV == "dev":
        if settings.JWT_SECRET_KEY in insecure_defaults:
            log.warning(
                "INSECURE_CONFIGURATION",
                field="JWT_SECRET_KEY",
                value=settings.JWT_SECRET_KEY,
                message="Using default JWT secret key in dev environment. This is INSECURE for production!"
            )
        
        if settings.FCM_SERVER_KEY in insecure_defaults:
            log.warning(
                "INSECURE_CONFIGURATION",
                field="FCM_SERVER_KEY",
                value=settings.FCM_SERVER_KEY,
                message="Using default FCM key in dev environment. This is INSECURE for production!"
            )
        
        if settings.AI_SERVICE_AUTH_TOKEN in insecure_defaults:
            log.warning(
                "INSECURE_CONFIGURATION",
                field="AI_SERVICE_AUTH_TOKEN",
                value=settings.AI_SERVICE_AUTH_TOKEN,
                message="Using default AI service token in dev environment. This is INSECURE for production!"
            )
    
    # В stage/prod окружениях валидация уже выполнена в Settings через field_validator
    # Но дополнительно логируем факт использования безопасных значений
    else:
        log.info(
            "SECURITY_CONFIG_VALIDATED",
            env=settings.APP_ENV,
            jwt_secret_set=settings.JWT_SECRET_KEY not in insecure_defaults,
            fcm_key_set=settings.FCM_SERVER_KEY not in insecure_defaults,
            ai_token_set=settings.AI_SERVICE_AUTH_TOKEN not in insecure_defaults,
        )
    
    # Логируем CORS конфигурацию
    log.info(
        "CORS_CONFIGURATION",
        env=settings.APP_ENV,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        origins_count=len(settings.CORS_ALLOW_ORIGINS),
        using_wildcard="*" in settings.CORS_ALLOW_ORIGINS,
    )

app = FastAPI(
    title="LifeMerge Backend",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# Выполняем проверку безопасности
validate_security_config()

# Настройка CORS middleware
cors_kwargs = {
    "allow_credentials": settings.CORS_ALLOW_CREDENTIALS,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": ["X-Request-Id", "X-Timezone"],
}

# Добавляем allow_origins только если есть origins для разрешения
if settings.CORS_ALLOW_ORIGINS:
    cors_kwargs["allow_origins"] = settings.CORS_ALLOW_ORIGINS
else:
    # Если origins пустые, но нужны credentials - это конфигурационная ошибка
    # (кроме dev окружения, где есть дефолты)
    if settings.CORS_ALLOW_CREDENTIALS and settings.APP_ENV != "dev":
        raise ValueError(
            "CORS_ALLOW_ORIGINS must be configured when CORS_ALLOW_CREDENTIALS=True "
            f"in {settings.APP_ENV} environment."
        )
    # В dev режиме или без credentials можем оставить origins пустыми
    # FastAPI CORSMiddleware будет использовать null origin

app.add_middleware(CORSMiddleware, **cors_kwargs)
# Adds request_id + timezone context, returns request_id in all responses
app.add_middleware(RequestContextMiddleware)
app.add_middleware(IdempotencySnapshotMiddleware)


app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.on_event("startup")
async def on_startup() -> None:
    env = (settings.ENV or "local").lower()

    if env in ("local", "dev"):
        # dev convenience: create tables automatically
        await init_db(engine)
        return

    if env in ("stage", "prod") and not settings.REDIS_URL:
        raise RuntimeError("REDIS_URL must be set in stage/prod for rate limiting")

    if env in ("stage", "prod"):
        # strict: alembic must be applied; schema must match head
        await ensure_schema_up_to_date(engine, alembic_ini_path="alembic.ini")
        return

    # unknown env -> fail closed (safer for release)
    raise RuntimeError(f"Unknown ENV={settings.ENV}. Expected local/dev/stage/prod.")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    try:
        r = get_redis()
        await r.aclose()
    except Exception:
        pass
        
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