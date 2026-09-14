"""End-to-end correlation and metric coverage across the real local pipeline."""

import io
import json
import logging
from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.core.config import Settings
from src.mcp.client import FinanceMCPClient
from src.mcp.server import build_finance_server
from src.observability import (
    Observability,
    PersistenceTelemetryObserver,
    StructuredLogger,
    ToolTelemetryObserver,
)
from src.observability.logging import JsonFormatter
from src.orchestration.graph import AnalysisOrchestrator
from src.persistence.repository import FileResultRepository
from src.providers.mock import MockFinanceProvider
from src.services.analysis import AnalysisService


class PartiallyFailingProvider(MockFinanceProvider):
    def get_news(self, ticker: str):  # type: ignore[no-untyped-def]
        del ticker
        raise RuntimeError("provider credential=private-value")


class FullyFailingProvider(MockFinanceProvider):
    def get_ohlcv(self, ticker: str, timeframe):  # type: ignore[no-untyped-def]
        del ticker, timeframe
        raise RuntimeError("provider password=private-value")


def build_instrumented_client(tmp_path, provider=None):  # type: ignore[no-untyped-def]
    stream = io.StringIO()
    logger = logging.getLogger(f"test.observability.pipeline.{uuid4()}")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    observability = Observability(logger=StructuredLogger(logger))
    settings = Settings(
        _env_file=None,
        app_environment="test",
        result_output_dir=tmp_path,
        cors_allowed_origins=["http://localhost:3000"],
        langsmith_tracing=False,
    )
    mcp_client = FinanceMCPClient(
        settings,
        transport=build_finance_server(provider),
        observer=ToolTelemetryObserver(observability),
    )
    service = AnalysisService(
        runner=AnalysisOrchestrator(mcp_client=mcp_client, observability=observability),
        repository=FileResultRepository(
            tmp_path,
            observer=PersistenceTelemetryObserver(observability),
        ),
        observability=observability,
    )
    return TestClient(create_app(settings=settings, service=service)), observability, stream


def events(stream: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines() if line]


def test_successful_pipeline_has_one_run_id_at_all_meaningful_boundaries(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client, observability, stream = build_instrumented_client(tmp_path)

    response = client.post(
        "/api/v1/analyses",
        json={"tickers": ["AAPL"], "domains": ["technical", "sentiment"]},
    )

    assert response.status_code == 200
    run_id = response.json()["run_id"]
    recorded = events(stream)
    names = {event["event"] for event in recorded}
    assert {
        "analysis_request_accepted",
        "pipeline_started",
        "agent_execution_completed",
        "mcp_tool_completed",
        "synthesis_completed",
        "persistence_completed",
        "pipeline_completed",
        "analysis_execution_completed",
    } <= names
    correlated = [event for event in recorded if event["event"] != "observability_context_missing"]
    assert {event["run_id"] for event in correlated} == {run_id}
    assert all(event["request_id"] for event in correlated)

    metrics = observability.metrics.snapshot()
    assert metrics.analyses_succeeded == 1
    assert metrics.agents["technical_executor"].succeeded == 1
    assert metrics.agents["sentiment_executor"].succeeded == 1
    assert metrics.tools["get_ohlcv"].succeeded == 1
    assert metrics.tools["get_news"].succeeded == 1
    assert metrics.synthesis["report_synthesis"].succeeded == 1
    assert metrics.persistence["result_save"].succeeded == 1
    assert metrics.pipeline.duration_ms.count == 1


def test_partial_and_failed_runs_count_failures_without_leaking_provider_secrets(tmp_path) -> None:  # type: ignore[no-untyped-def]
    partial_client, partial_observability, partial_stream = build_instrumented_client(
        tmp_path / "partial", PartiallyFailingProvider()
    )
    partial = partial_client.post(
        "/api/v1/analyses",
        json={"tickers": ["AAPL"], "domains": ["technical", "sentiment"]},
    )
    assert partial.status_code == 200
    assert partial.json()["status"] == "partial"
    partial_metrics = partial_observability.metrics.snapshot()
    assert partial_metrics.analyses_partial == 1
    assert partial_metrics.agents["sentiment_executor"].failed == 1
    assert partial_metrics.tools["get_news"].failed == 1
    assert partial_metrics.failures["mcp_tool_error"] >= 1
    assert "private-value" not in partial_stream.getvalue()

    failed_client, failed_observability, failed_stream = build_instrumented_client(
        tmp_path / "failed", FullyFailingProvider()
    )
    failed = failed_client.post(
        "/api/v1/analyses",
        json={"tickers": ["AAPL"], "domains": ["technical"]},
    )
    assert failed.status_code == 200
    assert failed.json()["status"] == "failed"
    failed_metrics = failed_observability.metrics.snapshot()
    assert failed_metrics.analyses_failed == 1
    assert failed_metrics.agents["technical_executor"].failed == 1
    assert failed_metrics.tools["get_ohlcv"].failed == 1
    assert failed_metrics.synthesis["report_synthesis"].failed == 1
    assert "private-value" not in failed_stream.getvalue()
