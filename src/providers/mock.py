"""Deterministic, copy-on-read implementation of all provider protocols."""

from copy import deepcopy

from src.providers.errors import ProviderError, UnknownTickerError, UnsupportedTimeframeError
from src.providers.fixtures import AS_OF, COMPANIES, MACRO
from src.providers.schemas import (
    CompanyFinancialsResponse,
    CompanyMetricsResponse,
    MacroIndicatorsResponse,
    NewsResponse,
    OHLCVResponse,
    SectorDataResponse,
)
from src.schemas.enums import Timeframe


class MockFinanceProvider:
    supported_tickers = tuple(COMPANIES.keys())
    supported_timeframes = tuple(timeframe.value for timeframe in Timeframe)
    supported_regions = tuple(MACRO.keys())

    def _company(self, ticker: str) -> tuple[str, dict]:
        normalized = ticker.strip().upper()
        if normalized not in COMPANIES:
            raise UnknownTickerError(normalized, self.supported_tickers)
        return normalized, deepcopy(COMPANIES[normalized])

    def get_ohlcv(self, ticker: str, timeframe: Timeframe | str) -> OHLCVResponse:
        normalized, company = self._company(ticker)
        try:
            normalized_timeframe = Timeframe(timeframe)
        except ValueError as exc:
            raise UnsupportedTimeframeError(str(timeframe), self.supported_timeframes) from exc

        return OHLCVResponse.model_validate(
            {
                "ticker": normalized,
                "timeframe": normalized_timeframe,
                "as_of": AS_OF,
                "bars": [
                    {
                        "timestamp": bar[0],
                        "open": bar[1],
                        "high": bar[2],
                        "low": bar[3],
                        "close": bar[4],
                        "volume": bar[5],
                    }
                    for bar in company["bars"]
                ],
            }
        )

    def get_company_financials(self, ticker: str) -> CompanyFinancialsResponse:
        normalized, company = self._company(ticker)
        return CompanyFinancialsResponse.model_validate(
            {"ticker": normalized, "as_of": AS_OF, **company["financials"]}
        )

    def get_company_metrics(self, ticker: str) -> CompanyMetricsResponse:
        normalized, company = self._company(ticker)
        return CompanyMetricsResponse.model_validate(
            {"ticker": normalized, "as_of": AS_OF, "metrics": company["metrics"]}
        )

    def get_news(self, ticker: str) -> NewsResponse:
        normalized, company = self._company(ticker)
        return NewsResponse.model_validate(
            {
                "ticker": normalized,
                "as_of": AS_OF,
                "articles": [
                    {
                        "headline": article[0],
                        "published_at": article[1],
                        "sentiment_score": article[2],
                        "topics": article[3],
                    }
                    for article in company["news"]
                ],
            }
        )

    def get_macro_indicators(self, region: str) -> MacroIndicatorsResponse:
        normalized = region.strip().upper()
        if normalized not in MACRO:
            raise ProviderError(
                f"Unsupported region {normalized!r}; supported: {', '.join(self.supported_regions)}"
            )
        return MacroIndicatorsResponse.model_validate(
            {"region": normalized, "as_of": AS_OF, "indicators": deepcopy(MACRO[normalized])}
        )

    def get_sector_data(self, ticker: str) -> SectorDataResponse:
        normalized, company = self._company(ticker)
        return SectorDataResponse.model_validate(
            {"ticker": normalized, "as_of": AS_OF, **company["sector"]}
        )
