from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.schemas import (
    AnalysisDomain,
    AnalysisReport,
    AnalysisRequest,
    ComparisonMetric,
    CrossStockComparison,
    DomainOutcome,
    ErrorDetail,
    EvidenceItem,
    ExecutionMetadata,
    NormalizedRequest,
    OutcomeStatus,
    RunState,
    RunStatus,
    Signal,
    SignalDirection,
    SourceType,
    StockAnalysis,
)
from src.core.ids import new_run_id

NOW = datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc)


def make_request() -> NormalizedRequest:
    return NormalizedRequest(
        request_text="Compare AAPL and TSLA",
        tickers=["aapl", " TSLA ", "AAPL"],
        domains=[AnalysisDomain.TECHNICAL, AnalysisDomain.FUNDAMENTAL],
    )


def make_evidence() -> EvidenceItem:
    return EvidenceItem(
        evidence_id="mock:AAPL:ohlcv:2026-09-11",
        title="AAPL one-year price series",
        source="finance_mcp.get_ohlcv",
        source_type=SourceType.MOCK,
        observed_at=NOW,
        details={"points": 12},
    )


def make_outcome() -> DomainOutcome:
    return DomainOutcome(
        ticker="AAPL",
        domain=AnalysisDomain.TECHNICAL,
        status=OutcomeStatus.SUCCEEDED,
        summary="Momentum remains constructive in the mock series.",
        signals=[
            Signal(
                name="RSI",
                direction=SignalDirection.NEUTRAL,
                value=58.2,
                rationale="The reading is below the overbought threshold.",
            )
        ],
        opportunities=["Positive medium-term momentum"],
        risks=["Price is near mock resistance"],
        evidence=[make_evidence()],
        data={"rsi": 58.2},
        duration_ms=14.5,
    )


def make_report(run_id: str) -> AnalysisReport:
    outcome = make_outcome()
    request = make_request()
    return AnalysisReport(
        run_id=run_id,
        status=RunStatus.SUCCEEDED,
        request=request,
        executive_summary="AAPL has constructive technical momentum in mock data.",
        stocks=[
            StockAnalysis(
                ticker="AAPL",
                summary="Constructive mock technical setup.",
                domains={AnalysisDomain.TECHNICAL: outcome},
                opportunities=outcome.opportunities,
                risks=outcome.risks,
            )
        ],
        opportunities=outcome.opportunities,
        risks=outcome.risks,
        comparison=CrossStockComparison(
            summary="Only one completed stock is available for this fixture.",
            metrics=[ComparisonMetric(label="RSI", values={"AAPL": 58.2})],
        ),
        evidence=outcome.evidence,
        execution=ExecutionMetadata(
            requested_tasks=1,
            succeeded_tasks=1,
            failed_tasks=0,
            started_at=NOW,
            completed_at=NOW,
            duration_ms=14.5,
            model="gpt-5.6-luna",
        ),
        generated_at=NOW,
        disclaimer="Mock data for demonstration only; not investment advice.",
    )


def test_raw_request_normalizes_and_deduplicates_explicit_fields() -> None:
    request = AnalysisRequest(
        request_text="  Compare the companies  ",
        tickers=["aapl", " TSLA ", "AAPL"],
        domains=[AnalysisDomain.TECHNICAL, AnalysisDomain.TECHNICAL],
        focus_areas=[" growth ", "growth", "profitability"],
    )

    assert request.request_text == "Compare the companies"
    assert request.tickers == ["AAPL", "TSLA"]
    assert request.domains == [AnalysisDomain.TECHNICAL]
    assert request.focus_areas == ["growth", "profitability"]


def test_raw_request_requires_text_or_ticker() -> None:
    with pytest.raises(ValidationError, match="request_text or at least one ticker"):
        AnalysisRequest(request_text=" ", tickers=[])


def test_unknown_fields_and_invalid_ticker_format_are_rejected() -> None:
    with pytest.raises(ValidationError):
        AnalysisRequest(tickers=["AAPL$"], unexpected=True)


def test_failed_outcome_requires_structured_error() -> None:
    with pytest.raises(ValidationError, match="require an error"):
        DomainOutcome(
            ticker="AAPL",
            domain=AnalysisDomain.SENTIMENT,
            status=OutcomeStatus.FAILED,
            duration_ms=1,
        )

    failed = DomainOutcome(
        ticker="AAPL",
        domain=AnalysisDomain.SENTIMENT,
        status=OutcomeStatus.FAILED,
        duration_ms=1,
        error=ErrorDetail(code="provider_down", message="Provider unavailable"),
    )
    assert failed.error is not None


def test_report_and_run_state_round_trip_through_json() -> None:
    run_id = new_run_id()
    report = make_report(str(run_id))
    state = RunState(
        run_id=run_id,
        status=RunStatus.SUCCEEDED,
        request=report.request,
        domain_outcomes=[make_outcome()],
        report=report,
        created_at=NOW,
        started_at=NOW,
        completed_at=NOW,
    )

    restored = RunState.model_validate_json(state.model_dump_json())

    assert restored == state
    assert AnalysisReport.model_validate_json(report.model_dump_json()) == report


def test_terminal_run_requires_completion_timestamp() -> None:
    with pytest.raises(ValidationError, match="terminal runs require completed_at"):
        RunState(
            run_id=new_run_id(),
            status=RunStatus.FAILED,
            request=make_request(),
            created_at=NOW,
            started_at=NOW,
        )
