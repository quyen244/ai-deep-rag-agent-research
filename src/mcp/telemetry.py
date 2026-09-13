"""Tool-call observer seam consumed by structured observability adapters."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ToolCallEvent:
    tool: str
    status: str
    duration_ms: float
    ticker: str | None = None
    run_id: str | None = None
    error_code: str | None = None


class ToolCallObserver(Protocol):
    def record(self, event: ToolCallEvent) -> None: ...


class NoOpToolCallObserver:
    def record(self, event: ToolCallEvent) -> None:
        del event
