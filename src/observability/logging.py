"""Secret-safe JSON logging without a provider-specific logging backend."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from src.core.redaction import redact_value
from src.observability.context import current_context


class JsonFormatter(logging.Formatter):
    """Render only the deliberately supplied structured event payload."""

    def format(self, record: logging.LogRecord) -> str:
        payload = getattr(record, "observability_event", None)
        if not isinstance(payload, dict):
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "event": "unstructured_log_record",
            }
        return json.dumps(redact_value(payload), ensure_ascii=False, sort_keys=True, default=str)


class StructuredLogger:
    """Emit a fixed-schema event through the standard-library logging pipeline."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("financial_analysis")

    def emit(
        self,
        event: str,
        *,
        level: int = logging.INFO,
        run_id: str | None = None,
        request_id: str | None = None,
        agent: str | None = None,
        ticker: str | None = None,
        tool: str | None = None,
        operation: str | None = None,
        status: str | None = None,
        duration_ms: float | None = None,
        error_type: str | None = None,
        **extra: object,
    ) -> None:
        context = current_context()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": logging.getLevelName(level),
            "event": event,
            "run_id": run_id or (context.run_id if context else None),
            "request_id": request_id or (context.request_id if context else None),
            "agent": agent,
            "ticker": ticker,
            "tool": tool,
            "operation": operation,
            "status": status,
            "duration_ms": round(max(0.0, duration_ms), 3) if duration_ms is not None else None,
            "error_type": error_type,
        }
        payload.update(extra)
        self._logger.log(
            level,
            event,
            extra={"observability_event": {key: value for key, value in payload.items() if value is not None}},
        )


def configure_structured_logging(level: str = "INFO") -> None:
    """Install one JSON handler for application events, without touching root logging."""

    logger = logging.getLogger("financial_analysis")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    if any(getattr(handler, "_financial_analysis_json", False) for handler in logger.handlers):
        return
    handler = logging.StreamHandler()
    handler._financial_analysis_json = True  # type: ignore[attr-defined]
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
