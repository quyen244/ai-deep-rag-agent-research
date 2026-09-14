"""Validated internal contracts used before data enters a DomainOutcome."""

from typing import Any

from pydantic import Field, model_validator

from src.schemas.base import ContractModel
from src.schemas.common import EvidenceItem, Signal


class ExecutorResult(ContractModel):
    """Successful executor content before the shared runner adds its envelope."""

    summary: str = Field(min_length=1, max_length=4_000)
    signals: list[Signal] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    data: dict[str, Any]


class UnavailableFields(ContractModel):
    """Explicit reasons for source fields that cannot be responsibly calculated."""

    fields: dict[str, str] = Field(default_factory=dict)


class TechnicalData(ContractModel):
    current_close: float
    trend: str
    rsi: float | None = None
    rsi_period: int | None = None
    macd: dict[str, float] | None = None
    sma: dict[str, float] = Field(default_factory=dict)
    ema: dict[str, float] = Field(default_factory=dict)
    bollinger_bands: dict[str, float] | None = None
    volume_context: dict[str, float | str] | None = None
    support: float | None = None
    resistance: float | None = None
    unavailable: dict[str, str] = Field(default_factory=dict)


class FundamentalData(ContractModel):
    fiscal_year: int
    revenue: float
    net_income: float
    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    price_to_earnings: float | None = None
    price_to_book: float | None = None
    ev_to_ebitda: float | None = None
    return_on_equity: float | None = None
    return_on_assets: float | None = None
    debt_to_equity: float | None = None
    liabilities_to_assets: float | None = None
    current_ratio: float | None = None
    free_cash_flow_margin: float | None = None
    revenue_trend: str | None = None
    earnings_trend: str | None = None
    financial_health: str
    valuation_premium_to_sector_percent: float | None = None
    unavailable: dict[str, str] = Field(default_factory=dict)


class SentimentData(ContractModel):
    sentiment_label: str
    sentiment_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    positive_items: int = Field(ge=0)
    neutral_items: int = Field(ge=0)
    negative_items: int = Field(ge=0)
    narratives: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    unavailable: dict[str, str] = Field(default_factory=dict)


class MacroData(ContractModel):
    region: str
    gdp_growth_annualized: float | None = None
    inflation_year_over_year: float | None = None
    policy_rate: float | None = None
    ten_year_treasury_yield: float | None = None
    unemployment_rate: float | None = None
    market_condition: str
    sector: str
    industry: str
    sector_annual_growth: float | None = None
    competitors: list[dict[str, str | float]] = Field(default_factory=list)
    company_implications: list[str] = Field(default_factory=list)
    unavailable: dict[str, str] = Field(default_factory=dict)


class GroundedInterpretation(ContractModel):
    """A model interpretation that may cite only evidence supplied to it."""

    summary: str = Field(min_length=1, max_length=1_200)
    opportunities: list[str] = Field(default_factory=list, max_length=5)
    risks: list[str] = Field(default_factory=list, max_length=5)
    evidence_ids: list[str] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def require_citations_for_model_narrative(self) -> "GroundedInterpretation":
        if not self.evidence_ids:
            raise ValueError("structured interpretations must cite at least one evidence ID")
        return self
