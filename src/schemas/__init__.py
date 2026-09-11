"""Public typed contracts shared across backend layers."""

from src.schemas.common import ErrorDetail, EvidenceItem, Signal
from src.schemas.domain import DomainOutcome
from src.schemas.enums import (
    AnalysisDomain,
    OutcomeStatus,
    RunStatus,
    SignalDirection,
    SourceType,
    Timeframe,
)
from src.schemas.report import (
    AnalysisReport,
    ComparisonMetric,
    CrossStockComparison,
    ExecutionMetadata,
    StockAnalysis,
)
from src.schemas.request import AnalysisRequest, NormalizedRequest
from src.schemas.run import RunState

__all__ = [
    "AnalysisDomain",
    "AnalysisReport",
    "AnalysisRequest",
    "ComparisonMetric",
    "CrossStockComparison",
    "DomainOutcome",
    "ErrorDetail",
    "EvidenceItem",
    "ExecutionMetadata",
    "NormalizedRequest",
    "OutcomeStatus",
    "RunState",
    "RunStatus",
    "Signal",
    "SignalDirection",
    "SourceType",
    "StockAnalysis",
    "Timeframe",
]
