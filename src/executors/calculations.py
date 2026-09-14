"""Pure deterministic calculations shared by domain executors."""

from collections.abc import Sequence
from math import sqrt


def rounded(value: float | None, digits: int = 2) -> float | None:
    return round(value, digits) if value is not None else None


def safe_divide(
    numerator: float, denominator: float, *, multiplier: float = 1.0
) -> float | None:
    """Calculate a ratio without replacing a zero denominator with a false value."""

    if denominator == 0:
        return None
    return numerator / denominator * multiplier


def simple_moving_average(values: Sequence[float], period: int) -> float | None:
    if period <= 0 or len(values) < period:
        return None
    return sum(values[-period:]) / period


def exponential_moving_average(values: Sequence[float], period: int) -> float | None:
    if period <= 0 or len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    value = sum(values[:period]) / period
    for price in values[period:]:
        value = price * multiplier + value * (1 - multiplier)
    return value


def exponential_moving_average_series(values: Sequence[float], period: int) -> list[float] | None:
    if period <= 0 or len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    value = sum(values[:period]) / period
    result = [value]
    for price in values[period:]:
        value = price * multiplier + value * (1 - multiplier)
        result.append(value)
    return result


def relative_strength_index(values: Sequence[float], period: int) -> float | None:
    if period <= 0 or len(values) < period + 1:
        return None
    changes = [right - left for left, right in zip(values[-(period + 1) :], values[-period:])]
    average_gain = sum(change for change in changes if change > 0) / period
    average_loss = -sum(change for change in changes if change < 0) / period
    if average_loss == 0:
        return 100.0 if average_gain > 0 else 50.0
    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))


def macd(
    values: Sequence[float], *, fast_period: int, slow_period: int, signal_period: int
) -> dict[str, float] | None:
    if fast_period <= 0 or slow_period <= fast_period or signal_period <= 0:
        raise ValueError("MACD periods must be positive and slow_period must exceed fast_period")
    if len(values) < slow_period + signal_period - 1:
        return None

    # Seed both EMA series at their respective first fully populated windows,
    # then align them by the first slow EMA observation.
    fast = exponential_moving_average_series(values, fast_period)
    slow = exponential_moving_average_series(values, slow_period)
    if fast is None or slow is None:
        return None
    fast_aligned = fast[slow_period - fast_period :]
    macd_series = [fast_value - slow_value for fast_value, slow_value in zip(fast_aligned, slow)]
    signal = exponential_moving_average(macd_series, signal_period)
    if signal is None:
        return None
    macd_line = macd_series[-1]
    return {
        "macd_line": macd_line,
        "signal_line": signal,
        "histogram": macd_line - signal,
    }


def bollinger_bands(values: Sequence[float], period: int, deviations: float = 2.0) -> dict[str, float] | None:
    if period <= 0 or len(values) < period:
        return None
    window = values[-period:]
    middle = sum(window) / period
    variance = sum((value - middle) ** 2 for value in window) / period
    standard_deviation = sqrt(variance)
    return {
        "lower": middle - deviations * standard_deviation,
        "middle": middle,
        "upper": middle + deviations * standard_deviation,
    }
