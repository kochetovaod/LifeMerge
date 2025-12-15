from __future__ import annotations

import asyncio
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import log
from app.models.notification import DigestSchedule
from app.models.push_device import PushDeviceToken
from app.services.observability import record_push_metric


class PushService:
    def __init__(self) -> None:
        self._fcm_url = "https://fcm.googleapis.com/fcm/send"

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
            self._send_to_device(device, title, body, data=data or {}, collapse_key=collapse_key, request_id=request_id)
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

    async def _send_to_device(
        self,
        device: PushDeviceToken,
        title: str,
        body: str,
        *,
        data: dict[str, Any],
        collapse_key: str | None,
        request_id: str | None,
    ) -> None:
        if device.platform.lower() == "ios":
            await self._send_apns(device, title, body, data=data, collapse_key=collapse_key, request_id=request_id)
        else:
            await self._send_fcm(device, title, body, data=data, collapse_key=collapse_key, request_id=request_id)

    async def _send_fcm(
        self,
        device: PushDeviceToken,
        title: str,
        body: str,
        *,
        data: dict[str, Any],
        collapse_key: str | None,
        request_id: str | None,
    ) -> None:
        headers = {
            "Authorization": f"key={settings.FCM_SERVER_KEY}",
            "Content-Type": "application/json",
            "X-Request-Id": request_id or "",
        }
        payload = {
            "to": device.device_token,
            "priority": "high",
            "collapse_key": collapse_key,
            "notification": {"title": title, "body": body},
            "data": data,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self._fcm_url, headers=headers, json=payload)
            status = "delivered" if resp.status_code < 300 else "failed"
            record_push_metric(user_id=str(device.user_id), platform=device.platform, status=status, request_id=request_id)
            log.info(
                "push_sent_fcm",
                request_id=request_id,
                user_id=str(device.user_id),
                status_code=resp.status_code,
                collapse_key=collapse_key,
            )

    async def _send_apns(
        self,
        device: PushDeviceToken,
        title: str,
        body: str,
        *,
        data: dict[str, Any],
        collapse_key: str | None,
        request_id: str | None,
    ) -> None:
        # Real APNs integration would use token-based auth and HTTP/2. For the skeleton we log the request.
        record_push_metric(user_id=str(device.user_id), platform=device.platform, status="queued", request_id=request_id)
        log.info(
            "push_sent_apns",
            request_id=request_id,
            user_id=str(device.user_id),
            collapse_key=collapse_key,
            payload={"title": title, "body": body, "data": data},
        )


push_service = PushService()
