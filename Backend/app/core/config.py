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


settings = Settings()
