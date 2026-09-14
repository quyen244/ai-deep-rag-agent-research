"""Injectable UTC clock used to keep tests deterministic."""

from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Return an aware UTC timestamp."""


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
