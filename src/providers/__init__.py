"""Replaceable financial-data provider interfaces and mock implementation."""

from src.providers.errors import ProviderError, UnknownTickerError, UnsupportedTimeframeError
from src.providers.mock import MockFinanceProvider
from src.providers.protocols import CompanyProvider, MacroProvider, MarketProvider, NewsProvider

__all__ = [
    "CompanyProvider",
    "MacroProvider",
    "MarketProvider",
    "MockFinanceProvider",
    "NewsProvider",
    "ProviderError",
    "UnknownTickerError",
    "UnsupportedTimeframeError",
]
