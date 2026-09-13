"""Contracts and reducers owned by the deterministic orchestration graph."""

from datetime import datetime
from typing import Annotated, NotRequired

from pydantic import Field, model_validator
from typing_extensions import TypedDict

from src.schemas.base import ContractModel
from src.schemas.common import ErrorDetail
from src.schemas.domain import DomainOutcome
from src.schemas.enums import AnalysisDomain, Timeframe
from src.schemas.report import AnalysisReport
from src.schemas.request import AnalysisRequest, NormalizedRequest


class TaskSpec(ContractModel):
    """One unique `(run, ticker, domain)` executor invocation."""

    task_id: str = Field(min_length=1, max_length=120)
    run_id: str = Field(min_length=1, max_length=80)
    ticker: str = Field(pattern=r"^[A-Z][A-Z0-9.-]{0,9}$")
    domain: AnalysisDomain
    timeframe: Timeframe
    focus_areas: list[str] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        ticker: str,
        domain: AnalysisDomain,
        timeframe: Timeframe,
        focus_areas: list[str],
    ) -> "TaskSpec":
        return cls(
            task_id=f"{run_id}:{ticker}:{domain.value}",
            run_id=run_id,
            ticker=ticker,
            domain=domain,
            timeframe=timeframe,
            focus_areas=focus_areas,
        )

    @property
    def identity(self) -> tuple[str, str, AnalysisDomain]:
        return self.run_id, self.ticker, self.domain

    @model_validator(mode="after")
    def validate_task_id(self) -> "TaskSpec":
        expected = f"{self.run_id}:{self.ticker}:{self.domain.value}"
        if self.task_id != expected:
            raise ValueError("task_id must match the run, ticker, and domain identity")
        return self


def append_outcomes(
    existing: list[DomainOutcome] | None, updates: list[DomainOutcome] | None
) -> list[DomainOutcome]:
    """Reducer that makes an accidental last-write-wins update impossible."""

    combined = [
        *(DomainOutcome.model_validate(outcome) for outcome in (existing or [])),
        *(DomainOutcome.model_validate(outcome) for outcome in (updates or [])),
    ]
    identities = [(outcome.ticker, outcome.domain) for outcome in combined]
    if len(identities) != len(set(identities)):
        raise ValueError("domain outcomes must be unique per ticker and domain")
    return combined


def append_errors(
    existing: list[ErrorDetail] | None, updates: list[ErrorDetail] | None
) -> list[ErrorDetail]:
    return [
        *(ErrorDetail.model_validate(error) for error in (existing or [])),
        *(ErrorDetail.model_validate(error) for error in (updates or [])),
    ]


class GraphState(TypedDict):
    """Serializable LangGraph state; executor outputs are append-only."""

    run_id: str
    raw_request: AnalysisRequest
    started_at: datetime
    request: NotRequired[NormalizedRequest]
    tasks: NotRequired[list[TaskSpec]]
    outcomes: Annotated[list[DomainOutcome], append_outcomes]
    errors: Annotated[list[ErrorDetail], append_errors]
    phase: NotRequired[str]
    report: NotRequired[AnalysisReport | None]
    completed_at: NotRequired[datetime]
