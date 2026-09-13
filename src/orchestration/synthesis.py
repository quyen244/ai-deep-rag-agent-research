"""Validated deterministic report synthesis and cross-stock comparison."""

from collections.abc import Sequence
from datetime import datetime
from typing import Any, Protocol

from pydantic import ValidationError

from src.core.errors import SynthesisError
from src.schemas.common import EvidenceItem
from src.schemas.domain import DomainOutcome
from src.schemas.enums import AnalysisDomain, OutcomeStatus, RunStatus
from src.schemas.report import (
    AnalysisReport,
    ComparisonMetric,
    CrossStockComparison,
    ExecutionMetadata,
    StockAnalysis,
)
from src.schemas.request import NormalizedRequest

_DISCLAIMER = "Mock data for demonstration only; not investment advice."


class ReportSynthesizer(Protocol):
    async def synthesize(
        self,
        *,
        run_id: str,
        request: NormalizedRequest,
        outcomes: Sequence[DomainOutcome],
        started_at: datetime,
        completed_at: datetime,
    ) -> AnalysisReport | dict[str, Any]: ...


class DeterministicReportSynthesizer:
    """Compose public report fields directly from validated executor outcomes."""

    model_name = "deterministic-executor-synthesis"

    async def synthesize(
        self,
        *,
        run_id: str,
        request: NormalizedRequest,
        outcomes: Sequence[DomainOutcome],
        started_at: datetime,
        completed_at: datetime,
    ) -> AnalysisReport:
        validated = [DomainOutcome.model_validate(outcome) for outcome in outcomes]
        succeeded = [outcome for outcome in validated if outcome.status is OutcomeStatus.SUCCEEDED]
        if not succeeded:
            raise SynthesisError(
                "A report cannot be synthesized without a successful domain outcome.",
                run_id=run_id,
                operation="report_synthesis",
            )

        failed = len(validated) - len(succeeded)
        status = RunStatus.SUCCEEDED if failed == 0 else RunStatus.PARTIAL
        stocks = self._stocks(request, validated)
        return AnalysisReport(
            run_id=run_id,
            status=status,
            request=request,
            executive_summary=self._executive_summary(request, len(succeeded), failed),
            stocks=stocks,
            opportunities=self._unique(
                opportunity
                for outcome in succeeded
                for opportunity in outcome.opportunities
            ),
            risks=self._unique(
                [
                    *(
                        risk
                        for outcome in succeeded
                        for risk in outcome.risks
                    ),
                    *(
                        f"{outcome.ticker} {outcome.domain.value} unavailable: "
                        f"{outcome.error.message}"
                        for outcome in validated
                        if outcome.status is OutcomeStatus.FAILED and outcome.error is not None
                    ),
                ]
            ),
            comparison=self._comparison(request, validated) if len(request.tickers) >= 2 else None,
            evidence=self._evidence(validated),
            execution=ExecutionMetadata(
                requested_tasks=len(validated),
                succeeded_tasks=len(succeeded),
                failed_tasks=failed,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=max(0.0, round((completed_at - started_at).total_seconds() * 1_000, 3)),
                model=self.model_name,
            ),
            generated_at=completed_at,
            disclaimer=_DISCLAIMER,
        )

    def _stocks(
        self, request: NormalizedRequest, outcomes: Sequence[DomainOutcome]
    ) -> list[StockAnalysis]:
        stocks: list[StockAnalysis] = []
        for ticker in request.tickers:
            ticker_outcomes = [outcome for outcome in outcomes if outcome.ticker == ticker]
            domains = {outcome.domain: outcome for outcome in ticker_outcomes}
            succeeded = [
                outcome for outcome in ticker_outcomes if outcome.status is OutcomeStatus.SUCCEEDED
            ]
            failed = len(ticker_outcomes) - len(succeeded)
            if succeeded:
                summaries = " ".join(outcome.summary for outcome in succeeded)
                summary = (
                    f"{ticker}: {len(succeeded)} of {len(ticker_outcomes)} requested domain(s) "
                    f"completed. {summaries}"
                )
            else:
                summary = f"{ticker}: no requested domain completed."
            stocks.append(
                StockAnalysis(
                    ticker=ticker,
                    summary=summary,
                    domains=domains,
                    opportunities=self._unique(
                        opportunity for outcome in succeeded for opportunity in outcome.opportunities
                    ),
                    risks=self._unique(
                        [
                            *(risk for outcome in succeeded for risk in outcome.risks),
                            *(
                                f"{outcome.domain.value} unavailable: {outcome.error.message}"
                                for outcome in ticker_outcomes
                                if outcome.status is OutcomeStatus.FAILED and outcome.error is not None
                            ),
                        ]
                    ),
                )
            )
        return stocks

    @staticmethod
    def _executive_summary(
        request: NormalizedRequest, succeeded: int, failed: int
    ) -> str:
        total = succeeded + failed
        if failed:
            return (
                f"Completed {succeeded} of {total} requested analyses for "
                f"{', '.join(request.tickers)}; {failed} domain outcome(s) failed."
            )
        return (
            f"Completed all {total} requested analyses for {', '.join(request.tickers)} "
            "using deterministic mock-data evidence."
        )

    def _comparison(
        self, request: NormalizedRequest, outcomes: Sequence[DomainOutcome]
    ) -> CrossStockComparison:
        definitions: tuple[tuple[str, AnalysisDomain, str, str | None, str], ...] = (
            ("Technical trend", AnalysisDomain.TECHNICAL, "trend", None, "none"),
            ("Current close", AnalysisDomain.TECHNICAL, "current_close", "USD_per_share", "none"),
            ("RSI", AnalysisDomain.TECHNICAL, "rsi", "index", "none"),
            ("Net margin", AnalysisDomain.FUNDAMENTAL, "net_margin", "percent", "max"),
            ("P/E", AnalysisDomain.FUNDAMENTAL, "price_to_earnings", "ratio", "min"),
            ("News sentiment", AnalysisDomain.SENTIMENT, "sentiment_score", "normalized_-1_to_1", "max"),
            ("Sector annual growth", AnalysisDomain.MACRO, "sector_annual_growth", "percent", "max"),
        )
        metrics = [
            self._comparison_metric(
                label=label,
                domain=domain,
                key=key,
                unit=unit,
                preference=preference,
                tickers=request.tickers,
                outcomes=outcomes,
            )
            for label, domain, key, unit, preference in definitions
        ]
        return CrossStockComparison(
            summary=(
                "Comparison uses completed domain outcomes only; unavailable cells indicate "
                "a failed domain or source field unavailable in the supplied evidence."
            ),
            metrics=metrics,
        )

    def _comparison_metric(
        self,
        *,
        label: str,
        domain: AnalysisDomain,
        key: str,
        unit: str | None,
        preference: str,
        tickers: Sequence[str],
        outcomes: Sequence[DomainOutcome],
    ) -> ComparisonMetric:
        values: dict[str, float | int | str | bool | None] = {}
        for ticker in tickers:
            outcome = next(
                (
                    candidate
                    for candidate in outcomes
                    if candidate.ticker == ticker
                    and candidate.domain is domain
                    and candidate.status is OutcomeStatus.SUCCEEDED
                ),
                None,
            )
            value = outcome.data.get(key) if outcome is not None else None
            values[ticker] = value if isinstance(value, (float, int, str, bool)) else None
        return ComparisonMetric(
            label=label,
            values=values,
            unit=unit,
            preferred_ticker=self._preferred_ticker(values, preference),
        )

    @staticmethod
    def _preferred_ticker(
        values: dict[str, float | int | str | bool | None], preference: str
    ) -> str | None:
        numeric = {
            ticker: float(value)
            for ticker, value in values.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        if not numeric or preference == "none":
            return None
        selector = max if preference == "max" else min
        return selector(numeric, key=numeric.__getitem__)

    @staticmethod
    def _evidence(outcomes: Sequence[DomainOutcome]) -> list[EvidenceItem]:
        deduplicated: dict[str, EvidenceItem] = {}
        for outcome in outcomes:
            for item in outcome.evidence:
                deduplicated.setdefault(item.evidence_id, item)
        return list(deduplicated.values())

    @staticmethod
    def _unique(items: Sequence[str] | Any) -> list[str]:
        return list(dict.fromkeys(item for item in items if item))


class BoundedReportSynthesizer:
    """Validate arbitrary structured synthesis with at most one schema retry."""

    def __init__(self, delegate: ReportSynthesizer | None = None) -> None:
        self._delegate = delegate or DeterministicReportSynthesizer()

    async def synthesize(
        self,
        *,
        run_id: str,
        request: NormalizedRequest,
        outcomes: Sequence[DomainOutcome],
        started_at: datetime,
        completed_at: datetime,
    ) -> AnalysisReport:
        for attempt in range(2):
            try:
                result = await self._delegate.synthesize(
                    run_id=run_id,
                    request=request,
                    outcomes=outcomes,
                    started_at=started_at,
                    completed_at=completed_at,
                )
                return AnalysisReport.model_validate(result)
            except SynthesisError:
                raise
            except (ValidationError, TypeError, ValueError, KeyError) as exc:
                if attempt == 1:
                    raise SynthesisError(
                        "The structured synthesis could not be validated.",
                        run_id=run_id,
                        operation="report_synthesis",
                        context={"failure_type": type(exc).__name__, "attempts": attempt + 1},
                    ) from exc
        raise AssertionError("unreachable")
