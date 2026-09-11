"""Typed envelope returned by every independently invocable executor."""

from pydantic import Field, model_validator

from src.schemas.base import ContractModel
from src.schemas.common import ErrorDetail, EvidenceItem, Signal
from src.schemas.enums import AnalysisDomain, OutcomeStatus


class DomainOutcome(ContractModel):
    ticker: str = Field(pattern=r"^[A-Z][A-Z0-9.-]{0,9}$")
    domain: AnalysisDomain
    status: OutcomeStatus
    summary: str = Field(default="", max_length=4_000)
    signals: list[Signal] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    data: dict[str, object] = Field(default_factory=dict)
    duration_ms: float = Field(ge=0.0)
    error: ErrorDetail | None = None

    @model_validator(mode="after")
    def validate_error_state(self) -> "DomainOutcome":
        if self.status is OutcomeStatus.FAILED and self.error is None:
            raise ValueError("failed domain outcomes require an error")
        if self.status is OutcomeStatus.SUCCEEDED and self.error is not None:
            raise ValueError("successful domain outcomes cannot include an error")
        return self
