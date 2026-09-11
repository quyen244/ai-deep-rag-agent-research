"""Provider-local errors translated at the MCP client boundary."""


class ProviderError(Exception):
    """Base failure raised by a financial-data provider."""


class UnknownTickerError(ProviderError):
    def __init__(self, ticker: str, supported: tuple[str, ...]) -> None:
        self.ticker = ticker
        self.supported = supported
        super().__init__(f"Unsupported ticker {ticker!r}; supported: {', '.join(supported)}")


class UnsupportedTimeframeError(ProviderError):
    def __init__(self, timeframe: str, supported: tuple[str, ...]) -> None:
        self.timeframe = timeframe
        self.supported = supported
        super().__init__(f"Unsupported timeframe {timeframe!r}; supported: {', '.join(supported)}")
