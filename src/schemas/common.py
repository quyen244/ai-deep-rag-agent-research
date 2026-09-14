"""Small value objects reused by domain and report contracts."""

from datetime import datetime
from typing import Any

from pydantic import Field

from src.schemas.base import ContractModel
from src.schemas.enums import SignalDirection, SourceType


class ErrorDetail(ContractModel):
    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=500)
    retryable: bool = False
    context: dict[str, Any] = Field(default_factory=dict)


class EvidenceItem(ContractModel):
    evidence_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=200)
    source: str = Field(min_length=1, max_length=120)
    source_type: SourceType
    observed_at: datetime
    reference: str | None = Field(default=None, max_length=500)
    details: dict[str, Any] = Field(default_factory=dict)


class Signal(ContractModel):
    name: str = Field(min_length=1, max_length=100)
    direction: SignalDirection
    value: float | int | str | bool | None = None
    unit: str | None = Field(default=None, max_length=40)
    rationale: str = Field(min_length=1, max_length=500)
