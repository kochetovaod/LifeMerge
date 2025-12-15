from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # env: dev|stage|prod
    APP_ENV: str = "dev"
    API_V1_PREFIX: str = "/v1"

    # DB
    DATABASE_URL: str = "postgresql+asyncpg://lifemerge:lifemerge@db:5432/lifemerge"

    # JWT
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_STAGE_AND_PROD"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_SECONDS: int = 900  # 15m
    REFRESH_TOKEN_TTL_SECONDS: int = 60 * 60 * 24 * 30  # 30d

    # Security
    PASSWORD_BCRYPT_ROUNDS: int = 12

    # HTTP
    CORS_ALLOW_ORIGINS: list[str] = ["*"]
    DEFAULT_TIMEZONE: str = "UTC"

    # Push notifications
    FCM_SERVER_KEY: str = "CHANGE_ME_IN_STAGE_AND_PROD"
    APNS_KEY_ID: str | None = None
    APNS_TEAM_ID: str | None = None
    APNS_KEY_PATH: str | None = None
    PUSH_DEFAULT_TOPIC: str = "lifemerge"
    DIGEST_DEFAULT_CADENCE: str = "daily"
    DIGEST_SEND_HOUR_UTC: int = 7

    # Background processing
    SYNC_QUEUE_BATCH_SIZE: int = 50
    SYNC_RETRY_MINUTES: int = 5

    # AI planner service
    AI_SERVICE_URL: str = "http://ai-service:9000"
    AI_SERVICE_AUTH_TOKEN: str = "ai-internal-token"
    AI_SERVICE_TIMEOUT_SECONDS: int = 30

    # Batch planner tuning
    AI_PLANNER_MAX_BATCH: int = 50

    # Subscriptions
    TRIAL_PERIOD_DAYS: int = 14
    FREE_MAX_GOALS: int = 5
    FREE_MAX_TASKS: int = 100
    FREE_MAX_FINANCE_ACCOUNTS: int = 1
    AI_ALLOWED_PLANS: list[str] = ["pro", "trial"]
    ANALYTICS_ALLOWED_PLANS: list[str] = ["pro"]


settings = Settings()
