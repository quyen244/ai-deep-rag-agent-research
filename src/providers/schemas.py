"""Validated payloads returned by finance MCP tools."""

from datetime import datetime

from pydantic import Field

from src.schemas.base import ContractModel
from src.schemas.enums import SourceType, Timeframe


class MockDataResponse(ContractModel):
    as_of: datetime
    source_type: SourceType = SourceType.MOCK
    source: str = "deterministic_mock"


class PriceBar(ContractModel):
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: int = Field(ge=0)


class OHLCVResponse(MockDataResponse):
    ticker: str
    timeframe: Timeframe
    currency: str = "USD"
    price_unit: str = "USD_per_share"
    volume_unit: str = "shares"
    bars: list[PriceBar] = Field(min_length=1)


class CompanyFinancialsResponse(MockDataResponse):
    ticker: str
    fiscal_year: int = Field(ge=2000)
    currency: str = "USD"
    unit: str = "USD_millions"
    revenue: float
    gross_profit: float
    operating_income: float
    net_income: float
    total_assets: float
    total_liabilities: float
    shareholders_equity: float
    operating_cash_flow: float
    free_cash_flow: float


class MetricValue(ContractModel):
    value: float
    unit: str


class CompanyMetricsResponse(MockDataResponse):
    ticker: str
    metrics: dict[str, MetricValue]


class NewsArticle(ContractModel):
    headline: str
    published_at: datetime
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    topics: list[str] = Field(default_factory=list)


class NewsResponse(MockDataResponse):
    ticker: str
    score_unit: str = "normalized_-1_to_1"
    articles: list[NewsArticle]


class MacroIndicatorsResponse(MockDataResponse):
    region: str
    indicators: dict[str, MetricValue]


class CompetitorSnapshot(ContractModel):
    ticker: str
    name: str
    market_cap_usd_billions: float = Field(gt=0)
    revenue_growth_percent: float


class SectorDataResponse(MockDataResponse):
    ticker: str
    sector: str
    industry: str
    metrics: dict[str, MetricValue]
    competitors: list[CompetitorSnapshot]
