"""Explicit LangGraph workflow for normalization, fan-out, and synthesis."""

import asyncio
from collections.abc import Mapping
from datetime import datetime
from time import perf_counter
from typing import Protocol
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from src.core.clock import Clock, SystemClock
from src.core.errors import ApplicationError, OrchestratorError, SynthesisError
from src.executors.context import FinanceDataClient, InterpretationClient, RunContext
from src.executors.fundamental import FundamentalExecutor
from src.executors.macro import MacroExecutor
from src.executors.sentiment import SentimentExecutor
from src.executors.technical import TechnicalExecutor
from src.orchestration.contracts import GraphState, TaskSpec
from src.orchestration.normalization import DEFAULT_SUPPORTED_TICKERS, RequestNormalizer
from src.orchestration.planner import TaskPlanner
from src.orchestration.synthesis import BoundedReportSynthesizer, ReportSynthesizer
from src.schemas.common import ErrorDetail
from src.schemas.domain import DomainOutcome
from src.schemas.enums import AnalysisDomain, OutcomeStatus, RunStatus
from src.schemas.request import AnalysisRequest, NormalizedRequest
from src.schemas.run import RunState


class DomainExecutor(Protocol):
    domain: AnalysisDomain

    async def execute(
        self,
        run_context: RunContext,
        ticker: str,
        normalized_request: NormalizedRequest,
    ) -> DomainOutcome: ...


def validator_bypass(state: GraphState) -> dict[str, str]:
    """Frozen Validator seam; validation behavior is intentionally deferred."""

    del state
    return {"phase": "validator_bypassed"}


class AnalysisOrchestrator:
    """Run the approved deterministic topology and return a serializable RunState."""

    def __init__(
        self,
        *,
        mcp_client: FinanceDataClient,
        executors: Mapping[AnalysisDomain, DomainExecutor] | None = None,
        synthesizer: ReportSynthesizer | None = None,
        supported_tickers: tuple[str, ...] = DEFAULT_SUPPORTED_TICKERS,
        clock: Clock | None = None,
        interpreter: InterpretationClient | None = None,
        macro_region: str = "US",
    ) -> None:
        self._mcp_client = mcp_client
        self._clock = clock or SystemClock()
        self._interpreter = interpreter
        self._macro_region = macro_region
        self._normalizer = RequestNormalizer(supported_tickers)
        self._planner = TaskPlanner()
        self._executors: dict[AnalysisDomain, DomainExecutor] = dict(
            executors
            or {
                AnalysisDomain.TECHNICAL: TechnicalExecutor(),
                AnalysisDomain.FUNDAMENTAL: FundamentalExecutor(),
                AnalysisDomain.SENTIMENT: SentimentExecutor(),
                AnalysisDomain.MACRO: MacroExecutor(),
            }
        )
        self._synthesizer = BoundedReportSynthesizer(synthesizer)
        self._graph = self._build_graph()

    async def run(
        self,
        *,
        run_id: UUID,
        request: AnalysisRequest,
        created_at: datetime | None = None,
    ) -> RunState:
        """Execute one immutable analysis run after input has been accepted."""

        started_at = self._clock.now()
        state = await self._graph.ainvoke(
            {
                "run_id": str(run_id),
                "raw_request": request,
                "started_at": started_at,
                "outcomes": [],
                "errors": [],
                "phase": "received",
            }
        )
        report = state.get("report")
        completed_at = state.get("completed_at", self._clock.now())
        return RunState(
            run_id=run_id,
            status=report.status if report is not None else RunStatus.FAILED,
            request=state["request"],
            domain_outcomes=state["outcomes"],
            report=report,
            errors=state["errors"],
            created_at=created_at or started_at,
            started_at=started_at,
            completed_at=completed_at,
        )

    @property
    def graph(self):  # type: ignore[no-untyped-def]
        """Expose the compiled graph for workflow-level tests and instrumentation."""

        return self._graph

    def _build_graph(self):  # type: ignore[no-untyped-def]
        workflow = StateGraph(GraphState)
        workflow.add_node("normalize_request", self._normalize_request)
        workflow.add_node("plan_tasks", self._plan_tasks)
        workflow.add_node("execute_tasks", self._execute_tasks)
        workflow.add_node("validator_bypass", validator_bypass)
        workflow.add_node("synthesize_report", self._synthesize_report)
        workflow.add_edge(START, "normalize_request")
        workflow.add_edge("normalize_request", "plan_tasks")
        workflow.add_edge("plan_tasks", "execute_tasks")
        workflow.add_edge("execute_tasks", "validator_bypass")
        workflow.add_edge("validator_bypass", "synthesize_report")
        workflow.add_edge("synthesize_report", END)
        return workflow.compile()

    def _normalize_request(self, state: GraphState) -> dict[str, object]:
        request = self._normalizer.normalize(state["raw_request"])
        return {"request": request, "phase": "request_normalized"}

    def _plan_tasks(self, state: GraphState) -> dict[str, object]:
        tasks = self._planner.plan(run_id=state["run_id"], request=state["request"])
        return {"tasks": tasks, "phase": "tasks_planned"}

    async def _execute_tasks(self, state: GraphState) -> dict[str, object]:
        request = state["request"]
        run_context = RunContext(
            run_id=state["run_id"],
            mcp_client=self._mcp_client,
            clock=self._clock,
            interpreter=self._interpreter,
            macro_region=self._macro_region,
        )
        # Each explicit task starts before this node awaits any outcome. This is
        # the graph's concurrency boundary and has no model-controlled routing.
        outcomes = await asyncio.gather(
            *(
                self._execute_task(
                    task=task,
                    run_context=run_context,
                    request=request,
                )
                for task in state["tasks"]
            )
        )
        return {"outcomes": outcomes, "phase": "outcomes_collected"}

    async def _execute_task(
        self,
        *,
        task: TaskSpec,
        run_context: RunContext,
        request: NormalizedRequest,
    ) -> DomainOutcome:
        started = perf_counter()
        try:
            executor = self._executors.get(task.domain)
            if executor is None:
                raise OrchestratorError(
                    "No executor is configured for the requested domain.",
                    run_id=task.run_id,
                    ticker=task.ticker,
                    operation="task_dispatch",
                    context={"domain": task.domain.value},
                )
            outcome = DomainOutcome.model_validate(
                await executor.execute(run_context, task.ticker, request)
            )
            if outcome.ticker != task.ticker or outcome.domain is not task.domain:
                raise OrchestratorError(
                    "An executor returned an outcome for a different task.",
                    run_id=task.run_id,
                    ticker=task.ticker,
                    operation="task_validation",
                    context={"expected_domain": task.domain.value},
                )
            return outcome
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            return DomainOutcome(
                ticker=task.ticker,
                domain=task.domain,
                status=OutcomeStatus.FAILED,
                duration_ms=round((perf_counter() - started) * 1_000, 3),
                error=self._task_error_detail(exc, task),
            )

    async def _synthesize_report(self, state: GraphState) -> dict[str, object]:
        completed_at = self._clock.now()
        succeeded = [
            outcome for outcome in state["outcomes"] if outcome.status is OutcomeStatus.SUCCEEDED
        ]
        if not succeeded:
            return {
                "errors": [
                    ErrorDetail(
                        code="no_successful_domain_outcomes",
                        message="All requested domain analyses failed; no report was synthesized.",
                        retryable=False,
                        context={"run_id": state["run_id"], "operation": "report_synthesis"},
                    )
                ],
                "report": None,
                "phase": "failed",
                "completed_at": completed_at,
            }
        return await self._synthesize_successful_outcomes(state, completed_at)

    async def _synthesize_successful_outcomes(
        self, state: GraphState, completed_at: datetime
    ) -> dict[str, object]:
        try:
            report = await self._synthesizer.synthesize(
                run_id=state["run_id"],
                request=state["request"],
                outcomes=state["outcomes"],
                started_at=state["started_at"],
                completed_at=completed_at,
            )
        except Exception as exc:
            return self._synthesis_failure(state, completed_at, exc)
        return {
            "report": report,
            "phase": "synthesized",
            "completed_at": completed_at,
        }

    def _synthesis_failure(
        self, state: GraphState, completed_at: datetime, exc: Exception
    ) -> dict[str, object]:
        if isinstance(exc, ApplicationError):
            detail = exc.to_detail()
        else:
            detail = SynthesisError(
                "The analysis report could not be synthesized.",
                run_id=state["run_id"],
                operation="report_synthesis",
                context={"failure_type": type(exc).__name__},
            ).to_detail()
        return {
            "errors": [
                ErrorDetail(
                    code=detail.code,
                    message=detail.message,
                    retryable=detail.retryable,
                    context={
                        **detail.context,
                        "run_id": state["run_id"],
                        "operation": "report_synthesis",
                    },
                )
            ],
            "report": None,
            "phase": "failed",
            "completed_at": completed_at,
        }

    @staticmethod
    def _task_error_detail(exc: Exception, task: TaskSpec) -> ErrorDetail:
        if isinstance(exc, ApplicationError):
            original = exc.to_detail()
        else:
            original = OrchestratorError(
                "A planned domain task could not complete.",
                context={"failure_type": type(exc).__name__},
            ).to_detail()
        return ErrorDetail(
            code=original.code,
            message=original.message,
            retryable=original.retryable,
            context={
                **original.context,
                "run_id": task.run_id,
                "ticker": task.ticker,
                "domain": task.domain.value,
                "operation": "task_execution",
                "error_type": type(exc).__name__,
            },
        )
