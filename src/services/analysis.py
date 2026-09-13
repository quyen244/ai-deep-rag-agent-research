"""Synchronous-MVP transaction boundary from request acceptance to persistence."""

import asyncio
from datetime import datetime
from time import perf_counter
from typing import Protocol
from uuid import UUID

from src.core.clock import Clock, SystemClock
from src.core.errors import (
    ApplicationError,
    OrchestratorError,
    PersistenceError,
    RequestValidationError,
    ResultNotFoundError,
)
from src.core.ids import new_run_id
from src.orchestration.normalization import RequestNormalizer
from src.persistence.repository import ResultRepository
from src.schemas.common import ErrorDetail
from src.schemas.enums import RunStatus
from src.schemas.request import AnalysisRequest, NormalizedRequest
from src.schemas.run import RunState
from src.services.metrics import ApiMetrics

_TERMINAL_STATUSES = frozenset({RunStatus.SUCCEEDED, RunStatus.PARTIAL, RunStatus.FAILED})


class AnalysisRunner(Protocol):
    async def run(
        self,
        *,
        run_id: UUID,
        request: AnalysisRequest,
        created_at: datetime | None = None,
    ) -> RunState: ...


class AnalysisService:
    """Create one run, execute it once, then persist its terminal artifact."""

    def __init__(
        self,
        *,
        runner: AnalysisRunner,
        repository: ResultRepository,
        normalizer: RequestNormalizer | None = None,
        metrics: ApiMetrics | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._runner = runner
        self._repository = repository
        self._normalizer = normalizer or RequestNormalizer()
        self._metrics = metrics or ApiMetrics()
        self._clock = clock or SystemClock()
        self._idempotency_locks: dict[str, asyncio.Lock] = {}

    @property
    def metrics(self) -> ApiMetrics:
        return self._metrics

    async def execute(self, request: AnalysisRequest) -> RunState:
        """Validate semantics, execute at most once per key, and save the result."""

        normalized_request = self._normalize_request(request)
        self._metrics.record_submission()
        if request.idempotency_key is None:
            return await self._execute_new_run(request, normalized_request)

        lock = self._idempotency_locks.setdefault(request.idempotency_key, asyncio.Lock())
        async with lock:
            existing = self._repository.find_by_idempotency_key(request.idempotency_key)
            if existing is not None:
                self._metrics.record_idempotency_hit()
                return existing
            return await self._execute_new_run(request, normalized_request)

    def get(self, run_id: UUID) -> RunState:
        result = self._repository.get(run_id)
        if result is None:
            raise ResultNotFoundError(
                "No persisted analysis exists for this run ID.",
                run_id=str(run_id),
                operation="result_lookup",
            )
        return result

    def _normalize_request(self, request: AnalysisRequest) -> NormalizedRequest:
        try:
            return self._normalizer.normalize(request)
        except ValueError as exc:
            raise RequestValidationError(
                str(exc),
                operation="request_normalization",
                context={"field": "tickers"},
            ) from exc

    async def _execute_new_run(
        self, request: AnalysisRequest, normalized_request: NormalizedRequest
    ) -> RunState:
        started = perf_counter()
        run_id = new_run_id()
        created_at = self._clock.now()
        try:
            result = RunState.model_validate(
                await self._runner.run(run_id=run_id, request=request, created_at=created_at)
            )
            if result.run_id != run_id or result.status not in _TERMINAL_STATUSES:
                raise OrchestratorError(
                    "The analysis workflow returned an invalid terminal result.",
                    run_id=str(run_id),
                    operation="analysis_execution",
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            result = self._failed_run(run_id, normalized_request, created_at, exc)

        try:
            saved = self._repository.save(result)
        except PersistenceError:
            raise
        elapsed_ms = (perf_counter() - started) * 1_000
        self._metrics.record_terminal(saved.status, elapsed_ms)
        return saved

    def _failed_run(
        self,
        run_id: UUID,
        request: NormalizedRequest,
        created_at: datetime,
        exc: Exception,
    ) -> RunState:
        completed_at = self._clock.now()
        if isinstance(exc, ApplicationError):
            error = exc.to_detail()
        else:
            error = OrchestratorError(
                "The analysis workflow could not complete.",
                run_id=str(run_id),
                operation="analysis_execution",
                context={"failure_type": type(exc).__name__},
            ).to_detail()
        return RunState(
            run_id=run_id,
            status=RunStatus.FAILED,
            request=request,
            errors=[self._run_error(error, run_id)],
            created_at=created_at,
            started_at=created_at,
            completed_at=completed_at,
        )

    @staticmethod
    def _run_error(error: ErrorDetail, run_id: UUID) -> ErrorDetail:
        return ErrorDetail(
            code=error.code,
            message=error.message,
            retryable=error.retryable,
            context={**error.context, "run_id": str(run_id), "operation": "analysis_execution"},
        )
