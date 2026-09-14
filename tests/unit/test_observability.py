"""Focused contracts for JSON events, context scopes, metrics, and trace metadata."""

import asyncio
import io
import json
import logging
from uuid import uuid4

from src.executors.interpreter import LunaStructuredInterpreter
from src.observability.context import run_scope
from src.observability.events import Observability
from src.observability.logging import JsonFormatter, StructuredLogger


def make_observability() -> tuple[Observability, io.StringIO]:
    stream = io.StringIO()
    logger = logging.getLogger(f"test.observability.{uuid4()}")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return Observability(logger=StructuredLogger(logger)), stream


def test_json_events_include_correlation_fields_and_redact_sensitive_values() -> None:
    observability, stream = make_observability()

    with run_scope("run-observability", request_id="request-observability"):
        observability.boundary(
            "mcp_tool_completed",
            group="tool",
            label="get_news",
            status="failed",
            duration_ms=12.3456,
            error_type="mcp_tool_error",
            tool="get_news",
            ticker="AAPL",
            operation="mcp_call",
            diagnostic="Bearer private-token password=private-password",
        )

    event = json.loads(stream.getvalue())
    assert event["event"] == "mcp_tool_completed"
    assert event["run_id"] == "run-observability"
    assert event["request_id"] == "request-observability"
    assert event["duration_ms"] == 12.346
    assert event["error_type"] == "mcp_tool_error"
    assert "private-token" not in stream.getvalue()
    assert "private-password" not in stream.getvalue()
    assert observability.metrics.snapshot().tools["get_news"].failed == 1


def test_missing_context_creates_a_safe_programming_error_event() -> None:
    observability, stream = make_observability()

    observability.emit("agent_execution_completed", operation="technical_analysis")

    event = json.loads(stream.getvalue())
    assert event["event"] == "observability_context_missing"
    assert event["error_type"] == "MissingRunContext"
    assert "run_id" not in event
    assert observability.metrics.snapshot().failures["missing_run_context"] == 1


def test_trace_metadata_is_attached_without_requiring_enabled_langsmith() -> None:
    class Runnable:
        def __init__(self) -> None:
            self.config = None

        async def ainvoke(self, prompt: str, config=None):  # type: ignore[no-untyped-def]
            del prompt
            self.config = config
            return {
                "summary": "Grounded summary.",
                "opportunities": [],
                "risks": [],
                "evidence_ids": ["mock:AAPL:ohlcv:2026-09-01"],
            }

    class Model:
        def __init__(self) -> None:
            self.runnable = Runnable()

        def with_structured_output(self, schema):  # type: ignore[no-untyped-def]
            del schema
            return self.runnable

    async def scenario() -> None:
        model = Model()
        with run_scope("run-trace", request_id="request-trace"):
            result = await LunaStructuredInterpreter(model).interpret(
                domain="technical",
                ticker="AAPL",
                facts={"trend": "uptrend"},
                evidence_ids=["mock:AAPL:ohlcv:2026-09-01"],
            )
        assert result.summary == "Grounded summary."
        assert model.runnable.config == {
            "metadata": {
                "run_id": "run-trace",
                "request_id": "request-trace",
                "operation": "structured_interpretation",
            },
            "tags": ["run_id:run-trace", "request_id:request-trace"],
        }

    asyncio.run(scenario())
