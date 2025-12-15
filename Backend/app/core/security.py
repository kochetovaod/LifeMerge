from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import hashlib
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, user_id: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.ACCESS_TOKEN_TTL_SECONDS)
    payload: dict[str, Any] = {
        "sub": subject,
        "uid": user_id,
        "iat": int(now.timestamp()),
        "exp": exp,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, user_id: str, device_id: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.REFRESH_TOKEN_TTL_SECONDS)
    payload: dict[str, Any] = {
        "sub": subject,
        "uid": user_id,
        "device_id": device_id,
        "iat": int(now.timestamp()),
        "exp": exp,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def token_hash(token: str) -> str:
    # store only hash of refresh token in DB
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
