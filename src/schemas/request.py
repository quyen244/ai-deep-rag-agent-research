"""Raw and normalized analysis request contracts."""

import re
from typing import Self

from pydantic import Field, field_validator, model_validator

from src.schemas.base import ContractModel
from src.schemas.enums import AnalysisDomain, Timeframe

_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")
_ALL_DOMAINS = list(AnalysisDomain)


def _normalize_tickers(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        ticker = value.strip().upper()
        if not _TICKER_PATTERN.fullmatch(ticker):
            raise ValueError(f"invalid ticker format: {value!r}")
        if ticker not in seen:
            seen.add(ticker)
            normalized.append(ticker)
    return normalized


def _deduplicate_domains(values: list[AnalysisDomain]) -> list[AnalysisDomain]:
    return list(dict.fromkeys(values))


class AnalysisRequest(ContractModel):
    request_text: str | None = Field(default=None, max_length=2_000)
    tickers: list[str] = Field(default_factory=list, max_length=10)
    domains: list[AnalysisDomain] = Field(default_factory=lambda: _ALL_DOMAINS.copy())
    timeframe: Timeframe = Timeframe.ONE_YEAR
    focus_areas: list[str] = Field(default_factory=list, max_length=20)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=120)

    @field_validator("request_text")
    @classmethod
    def normalize_request_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("tickers")
    @classmethod
    def normalize_tickers(cls, values: list[str]) -> list[str]:
        return _normalize_tickers(values)

    @field_validator("domains")
    @classmethod
    def normalize_domains(cls, values: list[AnalysisDomain]) -> list[AnalysisDomain]:
        if not values:
            raise ValueError("at least one analysis domain is required")
        return _deduplicate_domains(values)

    @field_validator("focus_areas")
    @classmethod
    def normalize_focus_areas(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        return list(dict.fromkeys(cleaned))

    @model_validator(mode="after")
    def require_request_content(self) -> Self:
        if not self.request_text and not self.tickers:
            raise ValueError("request_text or at least one ticker is required")
        return self


class NormalizedRequest(ContractModel):
    request_text: str | None = Field(default=None, max_length=2_000)
    tickers: list[str] = Field(min_length=1, max_length=10)
    domains: list[AnalysisDomain] = Field(min_length=1)
    timeframe: Timeframe = Timeframe.ONE_YEAR
    focus_areas: list[str] = Field(default_factory=list, max_length=20)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=120)

    @field_validator("tickers")
    @classmethod
    def normalize_tickers(cls, values: list[str]) -> list[str]:
        return _normalize_tickers(values)

    @field_validator("domains")
    @classmethod
    def normalize_domains(cls, values: list[AnalysisDomain]) -> list[AnalysisDomain]:
        return _deduplicate_domains(values)
