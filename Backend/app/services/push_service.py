from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import log
from app.models.notification import DigestSchedule
from app.models.push_device import PushDeviceToken
from app.services.observability import record_push_metric


@dataclass(frozen=True)
class NotificationPayload:
    user_id: str
    device: PushDeviceToken
    title: str
    body: str
    data: dict[str, Any]
    collapse_key: str | None
    request_id: str | None


@dataclass(frozen=True)
class SendResult:
    success: bool
    platform: str
    status: str
    status_code: int | None = None
    error: str | None = None


class NotificationPlatform(ABC):
    @abstractmethod
    async def send(self, payload: NotificationPayload) -> SendResult:  # pragma: no cover - interface contract
        raise NotImplementedError

    @abstractmethod
    def validate_token(self, token: str) -> bool:  # pragma: no cover - interface contract
        raise NotImplementedError

    @abstractmethod
    def get_platform_name(self) -> str:  # pragma: no cover - interface contract
        raise NotImplementedError


class FCMPlatform(NotificationPlatform):
    def __init__(self, fcm_url: str) -> None:
        self._fcm_url = fcm_url

    def get_platform_name(self) -> str:
        return "fcm"

    def validate_token(self, token: str) -> bool:
        return bool(token and len(token) > 10)

    async def send(self, payload: NotificationPayload) -> SendResult:
        headers = {
            "Authorization": f"key={settings.FCM_SERVER_KEY}",
            "Content-Type": "application/json",
            "X-Request-Id": payload.request_id or "",
        }
        body = {
            "to": payload.device.device_token,
            "priority": "high",
            "collapse_key": payload.collapse_key,
            "notification": {"title": payload.title, "body": payload.body},
            "data": payload.data,
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self._fcm_url, headers=headers, json=body)
            status = "delivered" if resp.status_code < 300 else "failed"
            return SendResult(
                success=resp.status_code < 300,
                platform=self.get_platform_name(),
                status=status,
                status_code=resp.status_code,
                error=None if resp.status_code < 300 else resp.text,
            )
        except httpx.HTTPError as exc:  # pragma: no cover - network errors
            return SendResult(
                success=False,
                platform=self.get_platform_name(),
                status="failed",
                status_code=None,
                error=str(exc),
            )


class APNSPlatform(NotificationPlatform):
    def get_platform_name(self) -> str:
        return "apns"

    def validate_token(self, token: str) -> bool:
        return bool(token)

    async def send(self, payload: NotificationPayload) -> SendResult:
        log.info(
            "push_sent_apns",
            request_id=payload.request_id,
            user_id=payload.user_id,
            collapse_key=payload.collapse_key,
            payload={"title": payload.title, "body": payload.body, "data": payload.data},
        )
        return SendResult(success=True, platform=self.get_platform_name(), status="queued")


class WebPushPlatform(NotificationPlatform):
    def get_platform_name(self) -> str:
        return "webpush"

    def validate_token(self, token: str) -> bool:
        return bool(token)

    async def send(self, payload: NotificationPayload) -> SendResult:
        log.info(
            "push_sent_webpush",
            request_id=payload.request_id,
            user_id=payload.user_id,
            collapse_key=payload.collapse_key,
            payload={"title": payload.title, "body": payload.body, "data": payload.data},
        )
        return SendResult(success=True, platform=self.get_platform_name(), status="queued")


class EmailPlatform(NotificationPlatform):
    def get_platform_name(self) -> str:
        return "email"

    def validate_token(self, token: str) -> bool:
        return True

    async def send(self, payload: NotificationPayload) -> SendResult:
        log.info(
            "notification_email_fallback",
            request_id=payload.request_id,
            user_id=payload.user_id,
            subject=payload.title,
            body_preview=payload.body[:120],
        )
        return SendResult(success=True, platform=self.get_platform_name(), status="delivered")


class NotificationRouter:
    def __init__(
        self,
        *,
        platforms: Iterable[NotificationPlatform],
        platform_aliases: dict[str, str] | None = None,
        fallback_chain: dict[str, list[str]] | None = None,
    ) -> None:
        self._platforms: dict[str, NotificationPlatform] = {
            platform.get_platform_name(): platform for platform in platforms
        }
        self._platform_aliases = {k.lower(): v for k, v in (platform_aliases or {}).items()}
        self._fallback_chain = {k: v for k, v in (fallback_chain or {}).items()}

    def _resolve_platform(self, platform_hint: str) -> NotificationPlatform | None:
        normalized = platform_hint.lower()
        key = self._platform_aliases.get(normalized, normalized)
        return self._platforms.get(key)

    def _build_chain(self, platform_hint: str) -> list[NotificationPlatform]:
        chain: list[NotificationPlatform] = []
        primary = self._resolve_platform(platform_hint)
        if primary:
            chain.append(primary)
            for fallback_name in self._fallback_chain.get(primary.get_platform_name(), []):
                fallback = self._platforms.get(fallback_name)
                if fallback:
                    chain.append(fallback)
        return chain

    async def route(self, payload: NotificationPayload) -> None:
        for platform in self._build_chain(payload.device.platform):
            if not platform.validate_token(payload.device.device_token):
                record_push_metric(
                    user_id=payload.user_id,
                    platform=platform.get_platform_name(),
                    status="invalid_token",
                    request_id=payload.request_id,
                )
                continue

            result = await platform.send(payload)
            record_push_metric(
                user_id=payload.user_id,
                platform=platform.get_platform_name(),
                status=result.status,
                request_id=payload.request_id,
            )

            if result.success:
                return

        log.warning(
            "push_delivery_exhausted",
            request_id=payload.request_id,
            user_id=payload.user_id,
            platform=payload.device.platform,
        )


class PushService:
    def __init__(self) -> None:
        self._router = NotificationRouter(
            platforms=[
                FCMPlatform("https://fcm.googleapis.com/fcm/send"),
                APNSPlatform(),
                WebPushPlatform(),
                EmailPlatform(),
            ],
            platform_aliases={"ios": "apns", "android": "fcm", "web": "webpush"},
            fallback_chain={"fcm": ["email"], "webpush": ["email"]},
        )

    async def send_notification(
        self,
        db: AsyncSession,
        *,
        user_id,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        collapse_key: str | None = None,
        request_id: str | None = None,
    ) -> None:
        tokens = await self._active_devices(db, user_id)
        if not tokens:
            log.info("push_skipped_no_devices", user_id=str(user_id), request_id=request_id)
            return

        tasks = [
            self._router.route(
                NotificationPayload(
                    user_id=str(user_id),
                    device=device,
                    title=title,
                    body=body,
                    data=data or {},
                    collapse_key=collapse_key,
                    request_id=request_id,
                )
            )
            for device in tokens
        ]
        await asyncio.gather(*tasks)

    async def send_digest(
        self,
        db: AsyncSession,
        *,
        digest: DigestSchedule,
        title: str,
        body: str,
        payload: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        await self.send_notification(
            db,
            user_id=digest.user_id,
            title=title,
            body=body,
            data={"type": "digest", **(payload or {})},
            collapse_key=f"digest-{digest.cadence}",
            request_id=request_id,
        )

    async def _active_devices(self, db: AsyncSession, user_id) -> list[PushDeviceToken]:
        res = await db.execute(
            select(PushDeviceToken).where(PushDeviceToken.user_id == user_id, PushDeviceToken.enabled.is_(True))
        )
        return list(res.scalars())


push_service = PushService()
