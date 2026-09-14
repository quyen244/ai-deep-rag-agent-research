from concurrent.futures import ThreadPoolExecutor

import pytest

from src.providers.errors import ProviderError, UnknownTickerError, UnsupportedTimeframeError
from src.providers.mock import MockFinanceProvider
from src.schemas.enums import SourceType


def test_supported_tickers_return_distinct_deterministic_data() -> None:
    provider = MockFinanceProvider()

    first = {ticker: provider.get_ohlcv(ticker, "1y") for ticker in provider.supported_tickers}
    second = {ticker: provider.get_ohlcv(ticker, "1y") for ticker in provider.supported_tickers}

    assert provider.supported_tickers == ("AAPL", "TSLA", "MSFT")
    assert len({response.bars[-1].close for response in first.values()}) == 3
    assert first == second
    assert all(response.source_type is SourceType.MOCK for response in first.values())


def test_reads_are_copy_isolated() -> None:
    provider = MockFinanceProvider()
    response = provider.get_company_metrics("AAPL")
    response.metrics["price_to_earnings"].value = 999

    fresh = provider.get_company_metrics("AAPL")

    assert fresh.metrics["price_to_earnings"].value == 31.8


def test_unknown_ticker_and_timeframe_fail_deterministically() -> None:
    provider = MockFinanceProvider()

    with pytest.raises(UnknownTickerError) as ticker_error:
        provider.get_news("NVDA")
    assert ticker_error.value.supported == ("AAPL", "TSLA", "MSFT")

    with pytest.raises(UnsupportedTimeframeError) as timeframe_error:
        provider.get_ohlcv("AAPL", "2y")
    assert "1y" in timeframe_error.value.supported


def test_unknown_macro_region_has_provider_error() -> None:
    with pytest.raises(ProviderError, match="Unsupported region"):
        MockFinanceProvider().get_macro_indicators("EU")


def test_concurrent_reads_are_stable() -> None:
    provider = MockFinanceProvider()
    tickers = ("AAPL", "TSLA", "MSFT") * 8

    with ThreadPoolExecutor(max_workers=8) as executor:
        closes = list(
            executor.map(lambda ticker: provider.get_ohlcv(ticker, "1y").bars[-1].close, tickers)
        )

    expected = {"AAPL": 233.1, "TSLA": 283.5, "MSFT": 527.3}
    assert closes == [expected[ticker] for ticker in tickers]


def test_all_provider_capabilities_return_units_and_as_of() -> None:
    provider = MockFinanceProvider()
    payloads = [
        provider.get_ohlcv("AAPL", "1y"),
        provider.get_company_financials("AAPL"),
        provider.get_company_metrics("AAPL"),
        provider.get_news("AAPL"),
        provider.get_macro_indicators("US"),
        provider.get_sector_data("AAPL"),
    ]

    assert all(payload.as_of.isoformat() == "2026-09-01T00:00:00+00:00" for payload in payloads)
    assert payloads[0].price_unit == "USD_per_share"
    assert payloads[1].unit == "USD_millions"
    assert payloads[2].metrics["net_margin"].unit == "percent"
    assert payloads[3].score_unit == "normalized_-1_to_1"
    assert payloads[4].indicators["policy_rate"].unit == "percent"
    assert payloads[5].metrics["annual_growth"].unit == "percent"
