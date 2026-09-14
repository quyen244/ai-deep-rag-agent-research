"""Bounded, thread-safe in-process counters and duration summaries."""

from collections import defaultdict
from threading import Lock

from pydantic import Field

from src.schemas.base import ContractModel
from src.schemas.enums import RunStatus

_ALLOWED_LABELS: dict[str, frozenset[str]] = {
    "agent": frozenset(
        {
            "technical_executor",
            "fundamental_executor",
            "sentiment_executor",
            "macro_executor",
            "orchestrator_dispatch",
        }
    ),
    "tool": frozenset(
        {
            "get_ohlcv",
            "get_company_financials",
            "get_company_metrics",
            "get_news",
            "get_macro_indicators",
            "get_sector_data",
        }
    ),
    "synthesis": frozenset({"report_synthesis"}),
    "persistence": frozenset({"result_save", "result_read", "idempotency_lookup"}),
    "pipeline": frozenset({"analysis_execution"}),
    "request": frozenset({"analysis_request"}),
}
_ALLOWED_FAILURES = frozenset(
    {
        "agent_execution_error",
        "configuration_error",
        "mcp_tool_error",
        "orchestrator_error",
        "persistence_error",
        "request_validation_error",
        "synthesis_error",
        "missing_run_context",
        "unknown",
    }
)


class DurationSummary(ContractModel):
    count: int = Field(ge=0)
    total_ms: float = Field(ge=0.0)
    average_ms: float = Field(ge=0.0)


class BoundaryMetrics(ContractModel):
    total: int = Field(ge=0)
    succeeded: int = Field(ge=0)
    failed: int = Field(ge=0)
    duration_ms: DurationSummary


class MetricsSnapshot(ContractModel):
    """The JSON contract exposed by ``GET /api/v1/metrics``."""

    analyses_submitted: int = Field(ge=0)
    analyses_succeeded: int = Field(ge=0)
    analyses_partial: int = Field(ge=0)
    analyses_failed: int = Field(ge=0)
    idempotency_hits: int = Field(ge=0)
    validation_failures: int = Field(ge=0)
    persistence_failures: int = Field(ge=0)
    duration_ms: DurationSummary
    requests: BoundaryMetrics
    pipeline: BoundaryMetrics
    agents: dict[str, BoundaryMetrics] = Field(default_factory=dict)
    tools: dict[str, BoundaryMetrics] = Field(default_factory=dict)
    synthesis: dict[str, BoundaryMetrics] = Field(default_factory=dict)
    persistence: dict[str, BoundaryMetrics] = Field(default_factory=dict)
    failures: dict[str, int] = Field(default_factory=dict)


class _MutableBoundary:
    def __init__(self) -> None:
        self.total = 0
        self.succeeded = 0
        self.failed = 0
        self.duration_count = 0
        self.duration_total_ms = 0.0

    def record(self, status: str, duration_ms: float | None) -> None:
        self.total += 1
        if status == "failed":
            self.failed += 1
        else:
            self.succeeded += 1
        if duration_ms is not None:
            self.duration_count += 1
            self.duration_total_ms += max(0.0, duration_ms)

    def snapshot(self) -> BoundaryMetrics:
        average = self.duration_total_ms / self.duration_count if self.duration_count else 0.0
        return BoundaryMetrics(
            total=self.total,
            succeeded=self.succeeded,
            failed=self.failed,
            duration_ms=DurationSummary(
                count=self.duration_count,
                total_ms=round(self.duration_total_ms, 3),
                average_ms=round(average, 3),
            ),
        )


class MetricRegistry:
    """Metric storage with bounded labels and no process-external dependency."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._submitted = 0
        self._succeeded = 0
        self._partial = 0
        self._failed = 0
        self._idempotency_hits = 0
        self._validation_failures = 0
        self._persistence_failures = 0
        self._duration_count = 0
        self._duration_total_ms = 0.0
        self._requests = _MutableBoundary()
        self._pipeline = _MutableBoundary()
        self._groups: dict[str, dict[str, _MutableBoundary]] = {
            group: defaultdict(_MutableBoundary)
            for group in ("agent", "tool", "synthesis", "persistence")
        }
        self._failures: dict[str, int] = defaultdict(int)

    def record_submission(self) -> None:
        with self._lock:
            self._submitted += 1
            self._requests.record("succeeded", None)

    def record_terminal(self, status: RunStatus, duration_ms: float) -> None:
        with self._lock:
            if status is RunStatus.SUCCEEDED:
                self._succeeded += 1
            elif status is RunStatus.PARTIAL:
                self._partial += 1
            else:
                self._failed += 1
            self._duration_count += 1
            self._duration_total_ms += max(0.0, duration_ms)
            self._pipeline.record(status.value, duration_ms)

    def record_idempotency_hit(self) -> None:
        with self._lock:
            self._idempotency_hits += 1

    def record_validation_failure(self) -> None:
        with self._lock:
            self._validation_failures += 1
            self._record_failure("request_validation_error")

    def record_persistence_failure(self) -> None:
        with self._lock:
            self._persistence_failures += 1
            self._record_failure("persistence_error")

    def record_boundary(
        self,
        group: str,
        label: str,
        *,
        status: str,
        duration_ms: float | None = None,
        error_type: str | None = None,
    ) -> None:
        with self._lock:
            normalized_group = group if group in _ALLOWED_LABELS else "pipeline"
            normalized_label = (
                label if label in _ALLOWED_LABELS[normalized_group] else "unknown"
            )
            if normalized_group == "request":
                self._requests.record(status, duration_ms)
            elif normalized_group == "pipeline":
                self._pipeline.record(status, duration_ms)
            else:
                self._groups[normalized_group][normalized_label].record(status, duration_ms)
            if error_type:
                self._record_failure(error_type)

    def _record_failure(self, error_type: str) -> None:
        normalized = error_type if error_type in _ALLOWED_FAILURES else "unknown"
        self._failures[normalized] += 1

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            average = self._duration_total_ms / self._duration_count if self._duration_count else 0.0
            return MetricsSnapshot(
                analyses_submitted=self._submitted,
                analyses_succeeded=self._succeeded,
                analyses_partial=self._partial,
                analyses_failed=self._failed,
                idempotency_hits=self._idempotency_hits,
                validation_failures=self._validation_failures,
                persistence_failures=self._persistence_failures,
                duration_ms=DurationSummary(
                    count=self._duration_count,
                    total_ms=round(self._duration_total_ms, 3),
                    average_ms=round(average, 3),
                ),
                requests=self._requests.snapshot(),
                pipeline=self._pipeline.snapshot(),
                agents={label: metric.snapshot() for label, metric in self._groups["agent"].items()},
                tools={label: metric.snapshot() for label, metric in self._groups["tool"].items()},
                synthesis={
                    label: metric.snapshot() for label, metric in self._groups["synthesis"].items()
                },
                persistence={
                    label: metric.snapshot() for label, metric in self._groups["persistence"].items()
                },
                failures=dict(self._failures),
            )
