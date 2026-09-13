"""Small in-process metrics seam for the API MVP."""

from threading import Lock

from pydantic import Field

from src.schemas.base import ContractModel
from src.schemas.enums import RunStatus


class DurationSummary(ContractModel):
    count: int = Field(ge=0)
    total_ms: float = Field(ge=0.0)
    average_ms: float = Field(ge=0.0)


class MetricsSnapshot(ContractModel):
    analyses_submitted: int = Field(ge=0)
    analyses_succeeded: int = Field(ge=0)
    analyses_partial: int = Field(ge=0)
    analyses_failed: int = Field(ge=0)
    idempotency_hits: int = Field(ge=0)
    validation_failures: int = Field(ge=0)
    persistence_failures: int = Field(ge=0)
    duration_ms: DurationSummary


class ApiMetrics:
    """Thread-safe counters intentionally limited to the current process."""

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

    def record_submission(self) -> None:
        with self._lock:
            self._submitted += 1

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

    def record_idempotency_hit(self) -> None:
        with self._lock:
            self._idempotency_hits += 1

    def record_validation_failure(self) -> None:
        with self._lock:
            self._validation_failures += 1

    def record_persistence_failure(self) -> None:
        with self._lock:
            self._persistence_failures += 1

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            average = (
                self._duration_total_ms / self._duration_count if self._duration_count else 0.0
            )
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
            )
