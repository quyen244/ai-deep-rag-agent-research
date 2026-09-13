"""Public error and operational response envelopes."""

from typing import Literal

from pydantic import Field

from src.schemas.base import ContractModel
from src.services.metrics import MetricsSnapshot


class ApiFieldError(ContractModel):
    location: list[str | int] = Field(min_length=1)
    message: str = Field(min_length=1, max_length=500)
    type: str = Field(min_length=1, max_length=120)


class ApiError(ContractModel):
    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=500)
    context: dict[str, object] = Field(default_factory=dict)
    fields: list[ApiFieldError] = Field(default_factory=list)


class ErrorResponse(ContractModel):
    error: ApiError


class HealthResponse(ContractModel):
    status: Literal["ok"]
    app_name: str = Field(min_length=1, max_length=160)
    environment: str = Field(min_length=1, max_length=40)
    storage: Literal["configured"]


__all__ = ["ApiError", "ApiFieldError", "ErrorResponse", "HealthResponse", "MetricsSnapshot"]
