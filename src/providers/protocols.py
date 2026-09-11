"""Dependency-inversion boundaries implemented by mock and future live providers."""

from typing import Protocol

from src.providers.schemas import (
    CompanyFinancialsResponse,
    CompanyMetricsResponse,
    MacroIndicatorsResponse,
    NewsResponse,
    OHLCVResponse,
    SectorDataResponse,
)
from src.schemas.enums import Timeframe


class MarketProvider(Protocol):
    def get_ohlcv(self, ticker: str, timeframe: Timeframe | str) -> OHLCVResponse: ...


class CompanyProvider(Protocol):
    def get_company_financials(self, ticker: str) -> CompanyFinancialsResponse: ...

    def get_company_metrics(self, ticker: str) -> CompanyMetricsResponse: ...

    def get_sector_data(self, ticker: str) -> SectorDataResponse: ...


class NewsProvider(Protocol):
    def get_news(self, ticker: str) -> NewsResponse: ...


class MacroProvider(Protocol):
    def get_macro_indicators(self, region: str) -> MacroIndicatorsResponse: ...
