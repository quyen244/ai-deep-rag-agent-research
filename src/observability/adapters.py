"""Small adapters from existing observer seams to the shared telemetry facade."""

from src.observability.events import Observability


class ToolTelemetryObserver:
    def __init__(self, observability: Observability) -> None:
        self._observability = observability

    def record(self, event: object) -> None:
        self._observability.boundary(
            "mcp_tool_completed",
            group="tool",
            label=str(getattr(event, "tool")),
            status=str(getattr(event, "status")),
            duration_ms=float(getattr(event, "duration_ms")),
            error_type=getattr(event, "error_code"),
            tool=str(getattr(event, "tool")),
            ticker=getattr(event, "ticker"),
            operation="mcp_call",
            run_id=getattr(event, "run_id"),
        )


class ExecutorTelemetryObserver:
    def __init__(self, observability: Observability) -> None:
        self._observability = observability

    def record(self, event: object) -> None:
        status = getattr(event, "status")
        status_value = getattr(status, "value", str(status))
        self._observability.boundary(
            "agent_execution_completed",
            group="agent",
            label=str(getattr(event, "agent")),
            status=str(status_value),
            duration_ms=float(getattr(event, "duration_ms")),
            error_type=getattr(event, "error_code"),
            agent=str(getattr(event, "agent")),
            ticker=str(getattr(event, "ticker")),
            operation=str(getattr(event, "operation")),
            run_id=str(getattr(event, "run_id")),
        )


class PersistenceTelemetryObserver:
    def __init__(self, observability: Observability) -> None:
        self._observability = observability

    def record(self, event: object) -> None:
        self._observability.boundary(
            "persistence_completed",
            group="persistence",
            label=str(getattr(event, "operation")),
            status=str(getattr(event, "status")),
            duration_ms=float(getattr(event, "duration_ms")),
            error_type=getattr(event, "error_code"),
            operation=str(getattr(event, "operation")),
            run_id=getattr(event, "run_id"),
        )
