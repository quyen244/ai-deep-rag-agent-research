"""API and JSON persistence contracts for the synchronous MVP."""

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.core.config import Settings
from src.core.errors import PersistenceError
from src.orchestration.normalization import RequestNormalizer
from src.persistence.repository import FileResultRepository
from src.schemas import (
    AnalysisDomain,
    AnalysisReport,
    DomainOutcome,
    ErrorDetail,
    ExecutionMetadata,
    NormalizedRequest,
    OutcomeStatus,
    RunState,
    RunStatus,
    StockAnalysis,
)
from src.schemas.request import AnalysisRequest
from src.services.analysis import AnalysisService
from src.services.metrics import ApiMetrics

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)


class FakeRunner:
    def __init__(self, mode: str = "succeeded") -> None:
        self.mode = mode
        self.calls = 0

    async def run(
        self,
        *,
        run_id: UUID,
        request: AnalysisRequest,
        created_at: datetime | None = None,
    ) -> RunState:
        self.calls += 1
        if self.mode == "raises":
            raise RuntimeError("database password=not-for-response")
        normalized = RequestNormalizer().normalize(request)
        return make_terminal_run(run_id, normalized, self.mode, created_at or NOW)


class FailingRepository:
    def save(self, result: RunState) -> RunState:
        del result
        raise PersistenceError(
            "The output path has api_key=not-for-response.", operation="result_save"
        )

    def get(self, run_id: UUID) -> RunState | None:
        del run_id
        return None

    def find_by_idempotency_key(self, key: str) -> RunState | None:
        del key
        return None


def make_terminal_run(
    run_id: UUID,
    request: NormalizedRequest,
    mode: str,
    timestamp: datetime,
) -> RunState:
    technical = DomainOutcome(
        ticker=request.tickers[0],
        domain=AnalysisDomain.TECHNICAL,
        status=OutcomeStatus.SUCCEEDED,
        summary="Technical analysis completed against deterministic data.",
        opportunities=["Constructive momentum"],
        risks=["Momentum can reverse"],
        data={"rsi": 55.0},
        duration_ms=1.0,
    )
    outcomes = [technical]
    domains: dict[AnalysisDomain, DomainOutcome] = {AnalysisDomain.TECHNICAL: technical}
    if mode == "partial":
        failed = DomainOutcome(
            ticker=request.tickers[0],
            domain=AnalysisDomain.FUNDAMENTAL,
            status=OutcomeStatus.FAILED,
            duration_ms=1.0,
            error=ErrorDetail(code="fake_failure", message="Configured fake executor failure."),
        )
        outcomes.append(failed)
        domains[AnalysisDomain.FUNDAMENTAL] = failed
    status = RunStatus.PARTIAL if mode == "partial" else RunStatus.SUCCEEDED
    report = AnalysisReport(
        run_id=str(run_id),
        status=status,
        request=request,
        executive_summary="A structured report suitable for an API and dashboard consumer.",
        stocks=[
            StockAnalysis(
                ticker=request.tickers[0],
                summary="One deterministic stock analysis is available.",
                domains=domains,
                opportunities=["Constructive momentum"],
                risks=["Momentum can reverse"],
            )
        ],
        opportunities=["Constructive momentum"],
        risks=["Momentum can reverse"],
        execution=ExecutionMetadata(
            requested_tasks=len(outcomes),
            succeeded_tasks=1,
            failed_tasks=len(outcomes) - 1,
            started_at=timestamp,
            completed_at=timestamp,
            duration_ms=1.0,
            model="deterministic-test",
        ),
        generated_at=timestamp,
        disclaimer="Mock data for demonstration only; not investment advice.",
    )
    return RunState(
        run_id=run_id,
        status=status,
        request=request,
        domain_outcomes=outcomes,
        report=report,
        created_at=timestamp,
        started_at=timestamp,
        completed_at=timestamp,
    )


def build_client(tmp_path, runner: FakeRunner, repository=None):  # type: ignore[no-untyped-def]
    settings = Settings(
        _env_file=None,
        app_environment="test",
        result_output_dir=tmp_path,
        cors_allowed_origins=["http://localhost:3000"],
    )
    metrics = ApiMetrics()
    service = AnalysisService(
        runner=runner,
        repository=repository or FileResultRepository(tmp_path),
        metrics=metrics,
    )
    return TestClient(create_app(settings=settings, service=service)), service


def test_post_get_idempotency_and_json_artifact_share_one_run_schema(tmp_path) -> None:  # type: ignore[no-untyped-def]
    runner = FakeRunner()
    client, service = build_client(tmp_path, runner)
    payload = {"tickers": ["AAPL"], "domains": ["technical"]}

    created = client.post("/api/v1/analyses", json=payload, headers={"Idempotency-Key": "same-run"})

    assert created.status_code == 200
    result = created.json()
    run_id = result["run_id"]
    assert result["status"] == "succeeded"
    assert result["report"]["status"] == "succeeded"
    assert json.loads((tmp_path / f"{run_id}.json").read_text()) == result
    assert not list(tmp_path.glob("*.tmp"))

    retrieved = client.get(f"/api/v1/analyses/{run_id}")
    duplicate = client.post(
        "/api/v1/analyses", json=payload, headers={"Idempotency-Key": "same-run"}
    )
    assert retrieved.json() == result
    assert duplicate.json() == result
    assert runner.calls == 1
    assert service.metrics.snapshot().idempotency_hits == 1


def test_partial_and_failed_terminal_runs_are_persisted(tmp_path) -> None:  # type: ignore[no-untyped-def]
    partial_client, _ = build_client(tmp_path / "partial", FakeRunner("partial"))
    partial = partial_client.post("/api/v1/analyses", json={"tickers": ["AAPL"]})
    assert partial.status_code == 200
    assert partial.json()["status"] == "partial"
    assert partial.json()["report"]["execution"]["failed_tasks"] == 1

    failed_client, _ = build_client(tmp_path / "failed", FakeRunner("raises"))
    failed = failed_client.post("/api/v1/analyses", json={"tickers": ["AAPL"]})
    assert failed.status_code == 200
    assert failed.json()["status"] == "failed"
    assert failed.json()["report"] is None
    assert "not-for-response" not in failed.text
    assert (tmp_path / "failed" / f"{failed.json()['run_id']}.json").exists()


def test_malformed_and_unknown_requests_receive_safe_422_envelopes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client, _ = build_client(tmp_path, FakeRunner())

    malformed = client.post("/api/v1/analyses", json={})
    unknown = client.post("/api/v1/analyses", json={"tickers": ["NVDA"]})

    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "request_validation_error"
    assert malformed.json()["error"]["fields"][0]["location"] == ["body"]
    assert unknown.status_code == 422
    assert unknown.json()["error"]["code"] == "request_validation_error"
    assert "Unsupported ticker" in unknown.json()["error"]["message"]
    assert not list(tmp_path.glob("*.json"))


def test_unknown_run_persistence_failure_and_cors_are_safe(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client, _ = build_client(tmp_path, FakeRunner())
    missing = client.get(f"/api/v1/analyses/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "analysis_not_found"

    allowed = client.options(
        "/api/v1/analyses",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    denied = client.options(
        "/api/v1/analyses",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers

    failing_client, service = build_client(tmp_path / "failing", FakeRunner(), FailingRepository())
    persistence_failure = failing_client.post("/api/v1/analyses", json={"tickers": ["AAPL"]})
    assert persistence_failure.status_code == 500
    assert persistence_failure.json()["error"]["code"] == "persistence_error"
    assert "not-for-response" not in persistence_failure.text
    assert service.metrics.snapshot().persistence_failures == 1


def test_health_metrics_and_openapi_document_public_contracts(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client, _ = build_client(tmp_path, FakeRunner())

    health = client.get("/api/v1/health")
    metrics = client.get("/api/v1/metrics")
    schema = client.get("/openapi.json").json()

    assert health.json() == {
        "status": "ok",
        "app_name": "Multi-Agent Financial Analysis",
        "environment": "test",
        "storage": "configured",
    }
    assert metrics.status_code == 200
    assert metrics.json()["analyses_submitted"] == 0
    assert set(schema["paths"]) >= {
        "/api/v1/analyses",
        "/api/v1/analyses/{run_id}",
        "/api/v1/health",
        "/api/v1/metrics",
    }
    assert "AnalysisRequest" in schema["components"]["schemas"]
    assert "RunState" in schema["components"]["schemas"]
