"""Structured synthesis contract rendered by the API and Next.js dashboard."""

from datetime import datetime

from pydantic import Field

from src.schemas.base import ContractModel
from src.schemas.common import EvidenceItem
from src.schemas.domain import DomainOutcome
from src.schemas.enums import AnalysisDomain, RunStatus
from src.schemas.request import NormalizedRequest


class StockAnalysis(ContractModel):
    ticker: str = Field(pattern=r"^[A-Z][A-Z0-9.-]{0,9}$")
    summary: str = Field(min_length=1, max_length=4_000)
    domains: dict[AnalysisDomain, DomainOutcome]
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class ComparisonMetric(ContractModel):
    label: str = Field(min_length=1, max_length=120)
    values: dict[str, float | int | str | bool | None]
    unit: str | None = Field(default=None, max_length=40)
    preferred_ticker: str | None = Field(default=None, max_length=10)


class CrossStockComparison(ContractModel):
    summary: str = Field(min_length=1, max_length=4_000)
    metrics: list[ComparisonMetric] = Field(default_factory=list)


class ExecutionMetadata(ContractModel):
    requested_tasks: int = Field(ge=1)
    succeeded_tasks: int = Field(ge=0)
    failed_tasks: int = Field(ge=0)
    started_at: datetime
    completed_at: datetime
    duration_ms: float = Field(ge=0.0)
    model: str = Field(min_length=1, max_length=120)


class AnalysisReport(ContractModel):
    run_id: str = Field(min_length=1, max_length=80)
    status: RunStatus
    request: NormalizedRequest
    executive_summary: str = Field(min_length=1, max_length=8_000)
    stocks: list[StockAnalysis] = Field(min_length=1)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    comparison: CrossStockComparison | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    execution: ExecutionMetadata
    generated_at: datetime
    disclaimer: str = Field(min_length=1, max_length=1_000)
