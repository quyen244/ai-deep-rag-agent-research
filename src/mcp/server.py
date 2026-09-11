"""FastMCP finance server whose handlers delegate only to providers."""

from functools import lru_cache
from collections.abc import Callable
from typing import Protocol, TypeVar

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.providers.errors import ProviderError
from src.providers.mock import MockFinanceProvider
from src.providers.schemas import (
    CompanyFinancialsResponse,
    CompanyMetricsResponse,
    MacroIndicatorsResponse,
    NewsResponse,
    OHLCVResponse,
    SectorDataResponse,
)
from src.schemas.enums import Timeframe


class FinanceProvider(Protocol):
    def get_ohlcv(self, ticker: str, timeframe: Timeframe | str) -> OHLCVResponse: ...

    def get_company_financials(self, ticker: str) -> CompanyFinancialsResponse: ...

    def get_company_metrics(self, ticker: str) -> CompanyMetricsResponse: ...

    def get_news(self, ticker: str) -> NewsResponse: ...

    def get_macro_indicators(self, region: str) -> MacroIndicatorsResponse: ...

    def get_sector_data(self, ticker: str) -> SectorDataResponse: ...


ProviderResult = TypeVar("ProviderResult")


def build_finance_server(provider: FinanceProvider | None = None) -> FastMCP:
    """Build an injectable finance server for in-memory or stdio transport."""

    data_provider = provider or MockFinanceProvider()
    server = FastMCP(
        "Financial Analysis Data",
        version="1.0.0",
        instructions="Deterministic mock finance data for analysis executors.",
        mask_error_details=True,
        strict_input_validation=True,
    )

    def provider_call(operation: Callable[[], ProviderResult]) -> ProviderResult:
        try:
            return operation()
        except ProviderError as exc:
            raise ToolError(str(exc)) from None
        except Exception:
            raise ToolError("The configured finance provider failed.") from None

    @server.tool(name="get_ohlcv")
    def get_ohlcv(ticker: str, timeframe: str = Timeframe.ONE_YEAR.value) -> OHLCVResponse:
        """Return deterministic OHLCV price bars for a supported ticker."""

        return provider_call(lambda: data_provider.get_ohlcv(ticker, timeframe))

    @server.tool(name="get_company_financials")
    def get_company_financials(ticker: str) -> CompanyFinancialsResponse:
        """Return a compact income, balance-sheet, and cash-flow snapshot."""

        return provider_call(lambda: data_provider.get_company_financials(ticker))

    @server.tool(name="get_company_metrics")
    def get_company_metrics(ticker: str) -> CompanyMetricsResponse:
        """Return valuation, profitability, and leverage metrics."""

        return provider_call(lambda: data_provider.get_company_metrics(ticker))

    @server.tool(name="get_news")
    def get_news(ticker: str) -> NewsResponse:
        """Return deterministic news items and normalized sentiment scores."""

        return provider_call(lambda: data_provider.get_news(ticker))

    @server.tool(name="get_macro_indicators")
    def get_macro_indicators(region: str = "US") -> MacroIndicatorsResponse:
        """Return deterministic macroeconomic indicators for a region."""

        return provider_call(lambda: data_provider.get_macro_indicators(region))

    @server.tool(name="get_sector_data")
    def get_sector_data(ticker: str) -> SectorDataResponse:
        """Return sector benchmarks and a compact competitor set."""

        return provider_call(lambda: data_provider.get_sector_data(ticker))

    return server


@lru_cache(maxsize=1)
def get_finance_server() -> FastMCP:
    return build_finance_server()
