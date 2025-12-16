from __future__ import annotations

from typing import Protocol

from fastapi import Request


class IAIOrchestrator(Protocol):
    async def request_ai_plan(self, *, request: Request, plan_request_id, payload: dict) -> dict:
        ...

    def parse_ai_response(self, plan_data: dict, *, payload: dict, previous_version: int) -> dict:
        ...

    def handle_ai_fallback(self, *, payload: dict, previous_version: int) -> dict:
        ...
