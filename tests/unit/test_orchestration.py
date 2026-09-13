import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.core.clock import Clock
from src.orchestration.contracts import TaskSpec, append_outcomes
from src.orchestration.graph import AnalysisOrchestrator, validator_bypass
from src.orchestration.normalization import RequestNormalizer
from src.orchestration.planner import TaskPlanner, ensure_unique_tasks
from src.orchestration.synthesis import (
    BoundedReportSynthesizer,
    DeterministicReportSynthesizer,
)
from src.schemas import (
    AnalysisDomain,
    AnalysisRequest,
    DomainOutcome,
    ErrorDetail,
    NormalizedRequest,
    OutcomeStatus,
    RunStatus,
)

NOW = datetime(2026, 9, 13, 10, 0, tzinfo=timezone.utc)


class FixedClock(Clock):
    def now(self) -> datetime:
        return NOW


class FakeExecutor:
    def __init__(
        self,
        domain: AnalysisDomain,
        *,
        failing_tasks: set[tuple[str, AnalysisDomain]] | None = None,
        concurrency: dict[str, int] | None = None,
    ) -> None:
        self.domain = domain
        self.failing_tasks = failing_tasks or set()
        self.concurrency = concurrency

    async def execute(self, run_context, ticker, normalized_request):  # type: ignore[no-untyped-def]
        if self.concurrency is not None:
            self.concurrency["active"] += 1
            self.concurrency["maximum"] = max(
                self.concurrency["maximum"], self.concurrency["active"]
            )
            await asyncio.sleep(0.02)
            self.concurrency["active"] -= 1
        if (ticker, self.domain) in self.failing_tasks:
            return DomainOutcome(
                ticker=ticker,
                domain=self.domain,
                status=OutcomeStatus.FAILED,
                duration_ms=1,
                error=ErrorDetail(code="fake_failure", message="Configured executor failure."),
            )
        return DomainOutcome(
            ticker=ticker,
            domain=self.domain,
            status=OutcomeStatus.SUCCEEDED,
            summary=f"{ticker} {self.domain.value} completed.",
            opportunities=[f"{ticker} {self.domain.value} opportunity"],
            risks=[f"{ticker} {self.domain.value} risk"],
            data=self._data_for(ticker),
            duration_ms=1,
        )

    def _data_for(self, ticker: str) -> dict[str, object]:
        index = {"AAPL": 1, "TSLA": 2, "MSFT": 3}[ticker]
        if self.domain is AnalysisDomain.TECHNICAL:
            return {"trend": "uptrend", "current_close": 100.0 * index, "rsi": 50.0 + index}
        if self.domain is AnalysisDomain.FUNDAMENTAL:
            return {"net_margin": 10.0 * index, "price_to_earnings": 30.0 / index}
        if self.domain is AnalysisDomain.SENTIMENT:
            return {"sentiment_score": 0.1 * index}
        return {"sector_annual_growth": 2.0 * index}


def make_executors(
    *,
    failing_tasks: set[tuple[str, AnalysisDomain]] | None = None,
    concurrency: dict[str, int] | None = None,
) -> dict[AnalysisDomain, FakeExecutor]:
    return {
        domain: FakeExecutor(domain, failing_tasks=failing_tasks, concurrency=concurrency)
        for domain in AnalysisDomain
    }


def make_orchestrator(
    *,
    failing_tasks: set[tuple[str, AnalysisDomain]] | None = None,
    concurrency: dict[str, int] | None = None,
    synthesizer=None,  # type: ignore[no-untyped-def]
) -> AnalysisOrchestrator:
    return AnalysisOrchestrator(
        mcp_client=object(),  # type: ignore[arg-type]
        executors=make_executors(failing_tasks=failing_tasks, concurrency=concurrency),
        synthesizer=synthesizer,
        clock=FixedClock(),
    )


def test_request_normalizer_parses_text_and_respects_explicit_fields() -> None:
    normalizer = RequestNormalizer()
    parsed = normalizer.normalize(
        AnalysisRequest(request_text="Analyze AAPL and TSLA technical and sentiment")
    )
    explicit = normalizer.normalize(
        AnalysisRequest(
            request_text="Analyze AAPL technical",
            tickers=["tsla"],
            domains=[AnalysisDomain.MACRO],
        )
    )

    assert parsed.tickers == ["AAPL", "TSLA"]
    assert parsed.domains == [AnalysisDomain.TECHNICAL, AnalysisDomain.SENTIMENT]
    assert explicit.tickers == ["TSLA"]
    assert explicit.domains == [AnalysisDomain.MACRO]


def test_normalizer_rejects_an_unsupported_explicit_ticker() -> None:
    with pytest.raises(ValueError, match="Unsupported ticker"):
        RequestNormalizer().normalize(AnalysisRequest(tickers=["NVDA"]))


def test_default_two_ticker_request_plans_eight_unique_tasks() -> None:
    request = RequestNormalizer().normalize(AnalysisRequest(request_text="Analyze AAPL and TSLA"))
    tasks = TaskPlanner().plan(run_id="run-04", request=request)

    assert len(tasks) == 8
    assert {task.identity for task in tasks} == {
        ("run-04", ticker, domain)
        for ticker in ("AAPL", "TSLA")
        for domain in AnalysisDomain
    }


def test_task_planner_and_outcome_reducer_reject_duplicates() -> None:
    task = TaskSpec.create(
        run_id="run-04",
        ticker="AAPL",
        domain=AnalysisDomain.TECHNICAL,
        timeframe="1y",
        focus_areas=[],
    )
    outcome = DomainOutcome(
        ticker="AAPL",
        domain=AnalysisDomain.TECHNICAL,
        status=OutcomeStatus.SUCCEEDED,
        summary="Completed.",
        duration_ms=1,
    )

    with pytest.raises(ValueError, match="duplicate task identity"):
        ensure_unique_tasks([task, task])
    with pytest.raises(ValueError, match="domain outcomes must be unique"):
        append_outcomes([outcome], [outcome])


def test_graph_fans_out_tasks_and_produces_a_serializable_two_ticker_report() -> None:
    async def scenario() -> None:
        concurrency = {"active": 0, "maximum": 0}
        run = await make_orchestrator(concurrency=concurrency).run(
            run_id=uuid4(), request=AnalysisRequest(request_text="Analyze AAPL and TSLA")
        )

        assert run.status is RunStatus.SUCCEEDED
        assert len(run.domain_outcomes) == 8
        assert run.report is not None
        assert run.report.comparison is not None
        assert all(set(metric.values) == {"AAPL", "TSLA"} for metric in run.report.comparison.metrics)
        assert concurrency["maximum"] == 8
        restored = type(run).model_validate_json(run.model_dump_json())
        assert restored == run
        assert "messages" not in run.model_dump_json()

    asyncio.run(scenario())


def test_validator_bypass_is_an_explicit_no_op_seam() -> None:
    assert validator_bypass({}) == {"phase": "validator_bypassed"}


def test_partial_failure_keeps_every_outcome_and_marks_comparison_cells_unavailable() -> None:
    async def scenario() -> None:
        run = await make_orchestrator(
            failing_tasks={("TSLA", AnalysisDomain.FUNDAMENTAL)}
        ).run(run_id=uuid4(), request=AnalysisRequest(request_text="Analyze AAPL and TSLA"))

        assert run.status is RunStatus.PARTIAL
        assert len(run.domain_outcomes) == 8
        assert run.report is not None
        assert run.report.execution.succeeded_tasks == 7
        assert run.report.execution.failed_tasks == 1
        pe_metric = next(metric for metric in run.report.comparison.metrics if metric.label == "P/E")
        assert pe_metric.values == {"AAPL": 30.0, "TSLA": None}
        tsla = next(stock for stock in run.report.stocks if stock.ticker == "TSLA")
        assert tsla.domains[AnalysisDomain.FUNDAMENTAL].status is OutcomeStatus.FAILED

    asyncio.run(scenario())


def test_total_failure_skips_synthesis_and_returns_a_failed_run_artifact() -> None:
    async def scenario() -> None:
        failures = {(ticker, domain) for ticker in ("AAPL", "TSLA") for domain in AnalysisDomain}
        run = await make_orchestrator(failing_tasks=failures).run(
            run_id=uuid4(), request=AnalysisRequest(request_text="Analyze AAPL and TSLA")
        )

        assert run.status is RunStatus.FAILED
        assert run.report is None
        assert len(run.domain_outcomes) == 8
        assert all(outcome.status is OutcomeStatus.FAILED for outcome in run.domain_outcomes)
        assert run.errors[0].code == "no_successful_domain_outcomes"

    asyncio.run(scenario())


def test_bounded_synthesizer_retries_one_invalid_schema_response() -> None:
    class RetryDelegate:
        def __init__(self) -> None:
            self.calls = 0
            self.good = DeterministicReportSynthesizer()

        async def synthesize(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls += 1
            if self.calls == 1:
                return {"invalid": True}
            return await self.good.synthesize(**kwargs)

    async def scenario() -> None:
        delegate = RetryDelegate()
        report = await BoundedReportSynthesizer(delegate).synthesize(
            run_id="run-retry",
            request=NormalizedRequest(tickers=["AAPL"], domains=[AnalysisDomain.TECHNICAL]),
            outcomes=[
                DomainOutcome(
                    ticker="AAPL",
                    domain=AnalysisDomain.TECHNICAL,
                    status=OutcomeStatus.SUCCEEDED,
                    summary="Completed.",
                    duration_ms=1,
                )
            ],
            started_at=NOW,
            completed_at=NOW,
        )
        assert report.status is RunStatus.SUCCEEDED
        assert delegate.calls == 2

    asyncio.run(scenario())


def test_synthesis_failure_after_retry_retains_domain_outcomes_without_a_report() -> None:
    class InvalidDelegate:
        def __init__(self) -> None:
            self.calls = 0

        async def synthesize(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls += 1
            return {"invalid": True}

    async def scenario() -> None:
        delegate = InvalidDelegate()
        run = await make_orchestrator(synthesizer=delegate).run(
            run_id=uuid4(), request=AnalysisRequest(tickers=["AAPL"])
        )
        assert run.status is RunStatus.FAILED
        assert run.report is None
        assert len(run.domain_outcomes) == 4
        assert run.errors[0].code == "synthesis_error"
        assert delegate.calls == 2

    asyncio.run(scenario())
