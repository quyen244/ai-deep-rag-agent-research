"""Application exception taxonomy and safe error serialization."""

from collections.abc import Mapping
from typing import Any

from src.core.redaction import redact_text, redact_value
from src.schemas.common import ErrorDetail


class ApplicationError(Exception):
    code = "application_error"
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        run_id: str | None = None,
        ticker: str | None = None,
        agent: str | None = None,
        tool: str | None = None,
        operation: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        safe_context: dict[str, Any] = dict(context or {})
        for key, value in {
            "run_id": run_id,
            "ticker": ticker,
            "agent": agent,
            "tool": tool,
            "operation": operation,
        }.items():
            if value is not None:
                safe_context[key] = value

        self.safe_message = redact_text(message)
        self.context = redact_value(safe_context)
        super().__init__(self.safe_message)

    def to_detail(self) -> ErrorDetail:
        return ErrorDetail(
            code=self.code,
            message=self.safe_message,
            retryable=self.retryable,
            context=self.context,
        )


class ConfigurationError(ApplicationError):
    code = "configuration_error"


class MCPToolError(ApplicationError):
    code = "mcp_tool_error"
    retryable = True


class AgentExecutionError(ApplicationError):
    code = "agent_execution_error"
    retryable = True


class OrchestratorError(ApplicationError):
    code = "orchestrator_error"
    retryable = True


class SynthesisError(ApplicationError):
    code = "synthesis_error"
    retryable = True


class PersistenceError(ApplicationError):
    code = "persistence_error"
    retryable = True


class RequestValidationError(ApplicationError):
    """A semantic request error that is safe to render as HTTP 422."""

    code = "request_validation_error"


class ResultNotFoundError(ApplicationError):
    """A requested immutable run artifact does not exist."""

    code = "analysis_not_found"
