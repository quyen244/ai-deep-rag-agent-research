import pytest

from src.core.errors import (
    AgentExecutionError,
    ApplicationError,
    ConfigurationError,
    MCPToolError,
    OrchestratorError,
    PersistenceError,
    SynthesisError,
)


@pytest.mark.parametrize(
    ("error_type", "code"),
    [
        (ApplicationError, "application_error"),
        (ConfigurationError, "configuration_error"),
        (MCPToolError, "mcp_tool_error"),
        (AgentExecutionError, "agent_execution_error"),
        (OrchestratorError, "orchestrator_error"),
        (SynthesisError, "synthesis_error"),
        (PersistenceError, "persistence_error"),
    ],
)
def test_all_errors_share_one_safe_envelope(
    error_type: type[ApplicationError], code: str
) -> None:
    error = error_type(
        "provider failed; api_key=sk-private Bearer secret-token",
        run_id="run-123",
        ticker="AAPL",
        operation="test",
        context={"authorization": "Bearer hidden", "attempt": 2},
    )

    payload = error.to_detail().model_dump(mode="json")

    assert payload["code"] == code
    assert payload["context"]["run_id"] == "run-123"
    assert payload["context"]["ticker"] == "AAPL"
    serialized = str(payload)
    assert "sk-private" not in serialized
    assert "secret-token" not in serialized
    assert "Bearer hidden" not in serialized
    assert "[REDACTED]" in serialized
