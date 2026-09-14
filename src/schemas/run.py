"""Serializable lifecycle state owned by orchestration and persistence."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from src.schemas.base import ContractModel
from src.schemas.common import ErrorDetail
from src.schemas.domain import DomainOutcome
from src.schemas.enums import RunStatus
from src.schemas.report import AnalysisReport
from src.schemas.request import NormalizedRequest


class RunState(ContractModel):
    run_id: UUID
    status: RunStatus = RunStatus.QUEUED
    request: NormalizedRequest
    domain_outcomes: list[DomainOutcome] = Field(default_factory=list)
    report: AnalysisReport | None = None
    errors: list[ErrorDetail] = Field(default_factory=list)
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_lifecycle_timestamps(self) -> "RunState":
        terminal = {RunStatus.SUCCEEDED, RunStatus.PARTIAL, RunStatus.FAILED}
        if self.status in terminal and self.completed_at is None:
            raise ValueError("terminal runs require completed_at")
        if self.completed_at is not None and self.started_at is None:
            raise ValueError("completed runs require started_at")
        return self
