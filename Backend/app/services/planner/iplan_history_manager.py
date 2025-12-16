from __future__ import annotations

from typing import Protocol


class IPlanHistoryManager(Protocol):
    def append_version(self, plan: dict, *, status: str, created_task_ids=None, updated_task_ids=None) -> None:
        ...

    def get_version_history(self, plan: dict) -> list[dict]:
        ...

    def restore_version(self, plan: dict, version: int) -> dict | None:
        ...
