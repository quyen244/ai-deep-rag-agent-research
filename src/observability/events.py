"""Provider-neutral event facade shared across business boundaries."""

import logging

from src.observability.context import current_context
from src.observability.logging import StructuredLogger
from src.observability.metrics import MetricRegistry


class Observability:
    """Record safe structured events and bounded metrics without affecting work."""

    def __init__(
        self,
        *,
        metrics: MetricRegistry | None = None,
        logger: StructuredLogger | None = None,
    ) -> None:
        self.metrics = metrics or MetricRegistry()
        self.logger = logger or StructuredLogger()

    def emit(self, event: str, *, level: int = logging.INFO, **fields: object) -> None:
        if current_context() is None:
            self.metrics.record_boundary(
                "pipeline",
                "analysis_execution",
                status="failed",
                error_type="missing_run_context",
            )
            self.logger.emit(
                "observability_context_missing",
                level=logging.ERROR,
                operation=event,
                status="failed",
                error_type="MissingRunContext",
            )
            return
        self.logger.emit(event, level=level, **fields)

    def boundary(
        self,
        event: str,
        *,
        group: str,
        label: str,
        status: str,
        duration_ms: float | None = None,
        error_type: str | None = None,
        **fields: object,
    ) -> None:
        self.metrics.record_boundary(
            group,
            label,
            status=status,
            duration_ms=duration_ms,
            error_type=error_type,
        )
        self.emit(
            event,
            level=logging.ERROR if status == "failed" else logging.INFO,
            status=status,
            duration_ms=duration_ms,
            error_type=error_type,
            **fields,
        )
