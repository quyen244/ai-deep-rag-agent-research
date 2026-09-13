from src.executors.calculations import safe_divide
from src.executors.fundamental import calculate_fundamental_analysis
from src.executors.sentiment import calculate_sentiment
from src.executors.technical import calculate_technical_indicators
from src.providers.mock import MockFinanceProvider
from src.schemas.enums import Timeframe


def test_technical_indicators_are_deterministic_for_compact_ohlcv_series() -> None:
    response = MockFinanceProvider().get_ohlcv("AAPL", Timeframe.ONE_YEAR)
    data = calculate_technical_indicators(
        [bar.close for bar in response.bars],
        [bar.volume for bar in response.bars],
        [bar.low for bar in response.bars],
        [bar.high for bar in response.bars],
    )

    assert data.trend == "uptrend"
    assert data.rsi == 100.0
    assert data.macd is not None
    assert data.bollinger_bands is not None
    assert data.support == 191.8
    assert data.resistance == 236.4
    assert data.volume_context == {
        "latest_volume": 485_000_000.0,
        "average_prior_volume": 1_177_000_000.0,
        "volume_ratio": 0.41,
        "label": "below_average",
    }


def test_technical_calculation_marks_short_series_fields_unavailable() -> None:
    data = calculate_technical_indicators([10.0], [100], [9.0], [11.0])

    assert data.rsi is None
    assert data.macd is None
    assert data.support is None
    assert set(data.unavailable) >= {"rsi", "macd", "support", "resistance", "volume_context"}


def test_fundamental_calculations_use_financial_statement_denominators() -> None:
    provider = MockFinanceProvider()
    data = calculate_fundamental_analysis(
        provider.get_company_financials("AAPL"),
        provider.get_company_metrics("AAPL"),
        provider.get_sector_data("AAPL"),
    )

    assert data.gross_margin == 47.04
    assert data.net_margin == 24.48
    assert data.return_on_equity == 142.32
    assert data.return_on_assets == 27.86
    assert data.debt_to_equity == 4.11
    assert data.price_to_earnings == 31.8
    assert data.valuation_premium_to_sector_percent == 16.06
    assert data.price_to_book is None
    assert "price_to_book" in data.unavailable


def test_zero_denominators_return_unavailable_instead_of_a_substitute_value() -> None:
    assert safe_divide(20, 0) is None


def test_sentiment_calculation_classifies_article_scores_deterministically() -> None:
    result = calculate_sentiment([0.64, 0.31, -0.42])

    assert result == {
        "sentiment_score": 0.18,
        "sentiment_label": "positive",
        "positive_items": 2,
        "neutral_items": 0,
        "negative_items": 1,
    }
