from __future__ import annotations

import json
from typing import ClassVar

from pydantic import FieldValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # env: dev|stage|prod
    APP_ENV: str = "dev"
    API_V1_PREFIX: str = "/v1"

    # DB
    DATABASE_URL: str = "postgresql+asyncpg://lifemerge:lifemerge@db:5432/lifemerge"

    # JWT
    JWT_SECRET_KEY: str = Field(default="CHANGE_ME_IN_STAGE_AND_PROD")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_SECONDS: int = 900  # 15m
    REFRESH_TOKEN_TTL_SECONDS: int = 60 * 60 * 24 * 30  # 30d

    # Security
    PASSWORD_BCRYPT_ROUNDS: int = 12

    # HTTP & CORS Configuration
    # Important: When CORS_ALLOW_CREDENTIALS=True, CORS_ALLOW_ORIGINS must not contain "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_ORIGINS: list[str] = Field(default_factory=list)
    DEFAULT_TIMEZONE: str = "UTC"

    # Push notifications
    FCM_SERVER_KEY: str = Field(default="CHANGE_ME_IN_STAGE_AND_PROD")
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
    AI_SERVICE_AUTH_TOKEN: str = Field(default="CHANGE_ME_IN_STAGE_AND_PROD")
    AI_SERVICE_TIMEOUT_SECONDS: int = 30

    # Batch planner tuning
    AI_PLANNER_MAX_BATCH: int = 50
    PLANNER_DEFAULT_STRATEGY: str = "simple_greedy"

    # Subscriptions
    TRIAL_PERIOD_DAYS: int = 14
    FREE_MAX_GOALS: int = 5
    FREE_MAX_TASKS: int = 100
    FREE_MAX_FINANCE_ACCOUNTS: int = 1
    AI_ALLOWED_PLANS: list[str] = ["pro", "trial"]
    ANALYTICS_ALLOWED_PLANS: list[str] = ["pro"]

    # Значения по умолчанию, которые считаются небезопасными
    INSECURE_DEFAULT_VALUES: ClassVar[set[str]] = {
        "CHANGE_ME_IN_STAGE_AND_PROD",
        "CHANGE_ME",
        "SECRET_KEY",
        "YOUR_KEY_HERE",
    }

    @field_validator("JWT_SECRET_KEY", "FCM_SERVER_KEY", "AI_SERVICE_AUTH_TOKEN")
    @classmethod
    def validate_secrets(cls, value: str, info: FieldValidationInfo) -> str:
        """Валидация секретов: в production окружениях запрещены дефолтные значения."""
        env = info.data.get("APP_ENV", "dev")
        
        # В dev-окружении только предупреждаем в логах
        if env == "dev":
            return value
        
        # В stage/prod проверяем, что значение не является небезопасным дефолтом
        if value in cls.INSECURE_DEFAULT_VALUES:
            raise ValueError(
                f"{info.field_name} must be set to a secure value in {env} environment. "
                f"Current value '{value}' is not allowed."
            )
        
        # Дополнительная проверка на слишком короткие или простые значения
        if len(value) < 16:
            raise ValueError(
                f"{info.field_name} must be at least 16 characters long in {env} environment."
            )
        
        return value

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        """Parse CORS origins from string (JSON array) or list."""
        if value is None:
            return []
        
        if isinstance(value, list):
            return value
        
        try:
            # Try to parse as JSON array
            return json.loads(value)
        except json.JSONDecodeError:
            # If not JSON, split by comma
            return [origin.strip() for origin in value.split(",") if origin.strip()]

    @field_validator("CORS_ALLOW_ORIGINS")
    @classmethod
    def validate_cors_config(cls, value: list[str], info: FieldValidationInfo) -> list[str]:
        """Валидация CORS конфигурации: проверяем совместимость credentials и origins."""
        env = info.data.get("APP_ENV", "dev")
        allow_credentials = info.data.get("CORS_ALLOW_CREDENTIALS", True)
        
        # Если включены credentials, проверяем что origins не содержит "*"
        if allow_credentials and "*" in value:
            if env == "dev":
                # В dev режиме выдаем предупреждение и заменяем "*" на null origin
                # (это позволяет работать с localhost без явной конфигурации)
                log.warning(
                    "INSECURE_CORS_CONFIG",
                    message="CORS_ALLOW_CREDENTIALS=True with CORS_ALLOW_ORIGINS=['*'] is not allowed by browsers. "
                            "In dev environment, using null origin for flexibility.",
                    env=env
                )
                # В dev разрешаем специфичные для разработки origins
                dev_defaults = ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"]
                return dev_defaults
            else:
                # В stage/prod это ошибка конфигурации
                raise ValueError(
                    f"CORS_ALLOW_ORIGINS cannot contain '*' when CORS_ALLOW_CREDENTIALS=True in {env} environment. "
                    f"Please specify explicit origins."
                )
        
        # В production окружениях проверяем, что origins не пустые
        if env in ["stage", "prod"] and not value:
            raise ValueError(
                f"CORS_ALLOW_ORIGINS must be explicitly configured in {env} environment when CORS_ALLOW_CREDENTIALS=True."
            )
        
        return value

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        """Валидация значения APP_ENV."""
        allowed = {"dev", "stage", "prod"}
        if value not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}, got '{value}'")
        return value


settings = Settings()