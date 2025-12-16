from __future__ import annotations

from dataclasses import dataclass
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Email:
    """Value object that encapsulates email validation."""

    value: str

    def __post_init__(self) -> None:
        if not EMAIL_RE.match(self.value):
            raise ValueError("Invalid email format")

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.value
