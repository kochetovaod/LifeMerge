from __future__ import annotations

from zoneinfo import ZoneInfo

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserOut


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    full_name: str | None = Field(default=None, max_length=200)
    timezone: str = Field(default="UTC", max_length=64)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except Exception as exc:  # pragma: no cover - defensive validation
            raise ValueError("Invalid timezone") from exc
        return value


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    device_id: str = Field(min_length=1, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=1)
    device_id: str = Field(min_length=1, max_length=128)


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=256)


class LogoutIn(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)


class AuthOut(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
    request_id: str
