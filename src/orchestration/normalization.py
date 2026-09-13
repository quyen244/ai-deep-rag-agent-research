"""Deterministic request parsing and supported-ticker validation."""

import re
from collections.abc import Collection

from src.schemas.enums import AnalysisDomain
from src.schemas.request import AnalysisRequest, NormalizedRequest

DEFAULT_SUPPORTED_TICKERS = ("AAPL", "TSLA", "MSFT")
_SYMBOL = re.compile(r"\b[A-Z][A-Z0-9.-]{0,9}\b")
_DOMAIN_KEYWORDS: tuple[tuple[AnalysisDomain, tuple[str, ...]], ...] = (
    (AnalysisDomain.TECHNICAL, ("technical", "technicals", "tech analysis")),
    (AnalysisDomain.FUNDAMENTAL, ("fundamental", "fundamentals", "financial health")),
    (AnalysisDomain.SENTIMENT, ("sentiment", "news sentiment", "news")),
    (AnalysisDomain.MACRO, ("macro", "macroeconomic", "economy")),
)


class RequestNormalizer:
    """Normalize explicit request fields, or extract supported symbols from text."""

    def __init__(self, supported_tickers: Collection[str] = DEFAULT_SUPPORTED_TICKERS) -> None:
        normalized = tuple(dict.fromkeys(ticker.strip().upper() for ticker in supported_tickers))
        if not normalized:
            raise ValueError("at least one supported ticker must be configured")
        self._supported_tickers = normalized
        self._supported_set = set(normalized)

    @property
    def supported_tickers(self) -> tuple[str, ...]:
        return self._supported_tickers

    def normalize(self, request: AnalysisRequest) -> NormalizedRequest:
        explicit_tickers = "tickers" in request.model_fields_set and bool(request.tickers)
        tickers = request.tickers if explicit_tickers else self._tickers_from_text(request.request_text)
        if not tickers:
            raise ValueError(
                "No supported ticker was supplied. Supported tickers: "
                + ", ".join(self._supported_tickers)
            )
        unsupported = [ticker for ticker in tickers if ticker not in self._supported_set]
        if unsupported:
            raise ValueError(
                "Unsupported ticker(s): "
                + ", ".join(unsupported)
                + ". Supported tickers: "
                + ", ".join(self._supported_tickers)
            )

        explicit_domains = "domains" in request.model_fields_set
        domains = request.domains if explicit_domains else self._domains_from_text(request.request_text)
        return NormalizedRequest(
            request_text=request.request_text,
            tickers=tickers,
            domains=domains or list(AnalysisDomain),
            timeframe=request.timeframe,
            focus_areas=request.focus_areas,
            idempotency_key=request.idempotency_key,
        )

    def _tickers_from_text(self, request_text: str | None) -> list[str]:
        if not request_text:
            return []
        candidates = list(dict.fromkeys(_SYMBOL.findall(request_text)))
        supported = [ticker for ticker in candidates if ticker in self._supported_set]
        # A concise all-caps token in a ticker request is most often a symbol.
        # Reject it if unsupported rather than silently dropping a requested stock.
        unsupported = [
            ticker
            for ticker in candidates
            if ticker not in self._supported_set and 1 < len(ticker) <= 5
        ]
        if unsupported:
            raise ValueError(
                "Unsupported ticker(s): "
                + ", ".join(unsupported)
                + ". Supported tickers: "
                + ", ".join(self._supported_tickers)
            )
        return supported

    @staticmethod
    def _domains_from_text(request_text: str | None) -> list[AnalysisDomain]:
        if not request_text:
            return []
        lowered = request_text.lower()
        return [
            domain
            for domain, keywords in _DOMAIN_KEYWORDS
            if any(keyword in lowered for keyword in keywords)
        ]
