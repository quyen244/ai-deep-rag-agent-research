"""Shared executor envelope, safe failure conversion, and execution telemetry."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from src.core.errors import AgentExecutionError, ApplicationError
from src.executors.context import RunContext
from src.executors.contracts import ExecutorResult
from src.schemas.common import ErrorDetail, EvidenceItem
from src.schemas.domain import DomainOutcome
from src.schemas.enums import AnalysisDomain, OutcomeStatus, SourceType
from src.schemas.request import NormalizedRequest

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ExecutorEvent:
    run_id: str
    ticker: str
    agent: str
    domain: AnalysisDomain
    operation: str
    status: OutcomeStatus
    duration_ms: float
    error_code: str | None = None


class ExecutorObserver(Protocol):
    def record(self, event: ExecutorEvent) -> None: ...


class NoOpExecutorObserver:
    def record(self, event: ExecutorEvent) -> None:
        return None


class ExecutorRunner:
    """Run one domain worker and return a fully validated DomainOutcome."""

    def __init__(self, observer: ExecutorObserver | None = None) -> None:
        self._observer = observer or NoOpExecutorObserver()

    async def run(
        self,
        *,
        run_context: RunContext,
        ticker: str,
        request: NormalizedRequest,
        domain: AnalysisDomain,
        agent: str,
        operation: str,
        worker: Callable[[], Awaitable[ExecutorResult]],
    ) -> DomainOutcome:
        del request  # Included in the uniform invocation contract for every executor.
        started = perf_counter()
        outcome: DomainOutcome
        try:
            result = await worker()
            outcome = DomainOutcome(
                ticker=ticker,
                domain=domain,
                status=OutcomeStatus.SUCCEEDED,
                summary=result.summary,
                signals=result.signals,
                opportunities=result.opportunities,
                risks=result.risks,
                evidence=result.evidence,
                data=result.data,
                duration_ms=self._duration_ms(started),
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            outcome = DomainOutcome(
                ticker=ticker,
                domain=domain,
                status=OutcomeStatus.FAILED,
                error=self._to_error_detail(
                    exc,
                    run_id=run_context.run_id,
                    ticker=ticker,
                    agent=agent,
                    operation=operation,
                ),
                duration_ms=self._duration_ms(started),
            )

        event = ExecutorEvent(
            run_id=run_context.run_id,
            ticker=ticker,
            agent=agent,
            domain=domain,
            operation=operation,
            status=outcome.status,
            duration_ms=outcome.duration_ms,
            error_code=outcome.error.code if outcome.error else None,
        )
        self._record(event)
        return outcome

    @staticmethod
    def model_evidence(
        *,
        run_context: RunContext,
        agent: str,
        cited_evidence_ids: list[str],
    ) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=f"model:{run_context.run_id}:{agent}",
            title="Bounded Luna structured interpretation",
            source="openai.gpt-5.6-luna",
            source_type=SourceType.MODEL,
            observed_at=run_context.clock.now(),
            details={"grounded_evidence_ids": cited_evidence_ids},
        )

    @staticmethod
    def _duration_ms(started: float) -> float:
        return round((perf_counter() - started) * 1_000, 3)

    @staticmethod
    def _to_error_detail(
        exc: Exception,
        *,
        run_id: str,
        ticker: str,
        agent: str,
        operation: str,
    ) -> ErrorDetail:
        if isinstance(exc, ApplicationError):
            original = exc.to_detail()
        else:
            original = AgentExecutionError(
                "The domain executor could not complete its analysis.",
                context={"failure_type": type(exc).__name__},
            ).to_detail()
        return ErrorDetail(
            code=original.code,
            message=original.message,
            retryable=original.retryable,
            context={
                **original.context,
                "run_id": run_id,
                "ticker": ticker,
                "agent": agent,
                "operation": operation,
                "error_type": type(exc).__name__,
            },
        )

    def _record(self, event: ExecutorEvent) -> None:
        try:
            self._observer.record(event)
            logger.info(
                "executor_completed",
                extra={
                    "run_id": event.run_id,
                    "ticker": event.ticker,
                    "agent": event.agent,
                    "operation": event.operation,
                    "status": event.status.value,
                    "duration_ms": event.duration_ms,
                    "error_code": event.error_code,
                },
            )
        except Exception:
            # An observer or logging adapter cannot alter an analysis outcome.
            pass
