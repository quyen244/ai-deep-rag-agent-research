"""Deterministic technical-analysis executor using only finance MCP OHLCV data."""

from collections.abc import Sequence

from src.executors.calculations import (
    bollinger_bands,
    exponential_moving_average,
    macd,
    relative_strength_index,
    rounded,
    simple_moving_average,
)
from src.executors.context import RunContext
from src.executors.contracts import ExecutorResult, TechnicalData
from src.executors.runner import ExecutorRunner
from src.schemas.common import EvidenceItem, Signal
from src.schemas.domain import DomainOutcome
from src.schemas.enums import AnalysisDomain, SignalDirection, SourceType
from src.schemas.request import NormalizedRequest

_RSI_PERIOD = 5
_FAST_EMA_PERIOD = 3
_SLOW_EMA_PERIOD = 5
_MACD_SIGNAL_PERIOD = 2
_BOLLINGER_PERIOD = 5
_VOLUME_PERIOD = 5


def calculate_technical_indicators(
    closes: Sequence[float], volumes: Sequence[int], lows: Sequence[float], highs: Sequence[float]
) -> TechnicalData:
    """Calculate compact-series indicators without silently inventing inputs.

    The mock provider has six monthly bars, so these windows are deliberately
    compact. Each unavailable field carries an explicit reason rather than a
    substituted price or denominator.
    """

    if not closes:
        raise ValueError("at least one closing price is required")
    unavailable: dict[str, str] = {}
    current_close = closes[-1]

    sma_short = simple_moving_average(closes, _FAST_EMA_PERIOD)
    sma_long = simple_moving_average(closes, _SLOW_EMA_PERIOD)
    ema_short = exponential_moving_average(closes, _FAST_EMA_PERIOD)
    ema_long = exponential_moving_average(closes, _SLOW_EMA_PERIOD)
    rsi = relative_strength_index(closes, _RSI_PERIOD)
    macd_values = macd(
        closes,
        fast_period=_FAST_EMA_PERIOD,
        slow_period=_SLOW_EMA_PERIOD,
        signal_period=_MACD_SIGNAL_PERIOD,
    )
    bands = bollinger_bands(closes, _BOLLINGER_PERIOD)

    sma: dict[str, float] = {}
    ema: dict[str, float] = {}
    for name, value in ((f"sma_{_FAST_EMA_PERIOD}", sma_short), (f"sma_{_SLOW_EMA_PERIOD}", sma_long)):
        if value is None:
            unavailable[name] = "Insufficient price bars for the requested moving-average window."
        else:
            sma[name] = rounded(value)  # type: ignore[assignment]
    for name, value in ((f"ema_{_FAST_EMA_PERIOD}", ema_short), (f"ema_{_SLOW_EMA_PERIOD}", ema_long)):
        if value is None:
            unavailable[name] = "Insufficient price bars for the requested moving-average window."
        else:
            ema[name] = rounded(value)  # type: ignore[assignment]

    if rsi is None:
        unavailable["rsi"] = "Insufficient price bars for RSI(5)."
    if macd_values is None:
        unavailable["macd"] = "Insufficient price bars for MACD(3,5,2)."
    if bands is None:
        unavailable["bollinger_bands"] = "Insufficient price bars for Bollinger Bands(5)."

    support: float | None = None
    resistance: float | None = None
    if len(lows) >= _BOLLINGER_PERIOD and len(highs) >= _BOLLINGER_PERIOD:
        support = min(lows[-_BOLLINGER_PERIOD:])
        resistance = max(highs[-_BOLLINGER_PERIOD:])
    else:
        unavailable["support"] = "Insufficient OHLCV bars for the five-period support lookback."
        unavailable["resistance"] = "Insufficient OHLCV bars for the five-period resistance lookback."

    volume_context: dict[str, float | str] | None = None
    if len(volumes) > _VOLUME_PERIOD:
        baseline = sum(volumes[-(_VOLUME_PERIOD + 1) : -1]) / _VOLUME_PERIOD
        ratio = volumes[-1] / baseline if baseline else None
        if ratio is None:
            unavailable["volume_context"] = "Prior-period volume baseline is zero."
        else:
            label = "above_average" if ratio >= 1.1 else "below_average" if ratio <= 0.9 else "near_average"
            volume_context = {
                "latest_volume": float(volumes[-1]),
                "average_prior_volume": rounded(baseline),
                "volume_ratio": rounded(ratio),
                "label": label,
            }
    else:
        unavailable["volume_context"] = "Insufficient bars for a five-period prior-volume comparison."

    if sma_short is not None and sma_long is not None:
        if current_close > sma_long and sma_short > sma_long:
            trend = "uptrend"
        elif current_close < sma_long and sma_short < sma_long:
            trend = "downtrend"
        else:
            trend = "sideways"
    else:
        trend = "unavailable"
        unavailable["trend"] = "Moving-average trend needs both short and long windows."

    return TechnicalData(
        current_close=rounded(current_close),  # type: ignore[arg-type]
        trend=trend,
        rsi=rounded(rsi),
        rsi_period=_RSI_PERIOD if rsi is not None else None,
        macd={key: rounded(value) for key, value in macd_values.items()} if macd_values else None,
        sma=sma,
        ema=ema,
        bollinger_bands={key: rounded(value) for key, value in bands.items()} if bands else None,
        volume_context=volume_context,
        support=rounded(support),
        resistance=rounded(resistance),
        unavailable=unavailable,
    )


class TechnicalExecutor:
    """Analyze price, momentum, volatility, and volume for one ticker."""

    domain = AnalysisDomain.TECHNICAL
    agent_name = "technical_executor"

    def __init__(self, runner: ExecutorRunner | None = None) -> None:
        self._runner = runner or ExecutorRunner()

    async def execute(
        self, run_context: RunContext, ticker: str, normalized_request: NormalizedRequest
    ) -> DomainOutcome:
        normalized_ticker = ticker.strip().upper()
        return await self._runner.run(
            run_context=run_context,
            ticker=normalized_ticker,
            request=normalized_request,
            domain=self.domain,
            agent=self.agent_name,
            operation="technical_analysis",
            worker=lambda: self._analyze(run_context, normalized_ticker, normalized_request),
        )

    async def _analyze(
        self, run_context: RunContext, ticker: str, request: NormalizedRequest
    ) -> ExecutorResult:
        response = await run_context.mcp_client.get_ohlcv(
            ticker, request.timeframe, run_id=run_context.run_id
        )
        closes = [bar.close for bar in response.bars]
        data = calculate_technical_indicators(
            closes,
            [bar.volume for bar in response.bars],
            [bar.low for bar in response.bars],
            [bar.high for bar in response.bars],
        )
        evidence = [
            EvidenceItem(
                evidence_id=f"mock:{ticker}:ohlcv:{response.as_of.date().isoformat()}",
                title=f"{ticker} {response.timeframe.value} OHLCV series",
                source="finance_mcp.get_ohlcv",
                source_type=SourceType.MOCK,
                observed_at=response.as_of,
                details={
                    "timeframe": response.timeframe.value,
                    "bar_count": len(response.bars),
                    "latest_close": response.bars[-1].close,
                    "latest_volume": response.bars[-1].volume,
                    "bars": [
                        {
                            "timestamp": bar.timestamp,
                            "high": bar.high,
                            "low": bar.low,
                            "close": bar.close,
                            "volume": bar.volume,
                        }
                        for bar in response.bars
                    ],
                },
            )
        ]
        signals = self._signals(data)
        opportunities, risks = self._opportunities_and_risks(data)
        result = ExecutorResult(
            summary=self._summary(ticker, data),
            signals=signals,
            opportunities=opportunities,
            risks=risks,
            evidence=evidence,
            data=data.model_dump(mode="json"),
        )
        return await self._interpret_if_configured(run_context, ticker, result)

    @staticmethod
    def _summary(ticker: str, data: TechnicalData) -> str:
        rsi_text = f" RSI({data.rsi_period}) is {data.rsi}." if data.rsi is not None else " RSI is unavailable."
        return f"{ticker} is in a {data.trend} on the compact mock OHLCV series.{rsi_text}"

    @staticmethod
    def _signals(data: TechnicalData) -> list[Signal]:
        signals = [
            Signal(
                name="Trend",
                direction={
                    "uptrend": SignalDirection.POSITIVE,
                    "downtrend": SignalDirection.NEGATIVE,
                }.get(data.trend, SignalDirection.NEUTRAL),
                value=data.trend,
                rationale="Trend compares the latest close and short moving average with the long moving average.",
            )
        ]
        if data.rsi is not None:
            rsi_direction = (
                SignalDirection.NEGATIVE
                if data.rsi >= 70
                else SignalDirection.POSITIVE
                if data.rsi >= 50
                else SignalDirection.NEGATIVE
                if data.rsi <= 30
                else SignalDirection.NEUTRAL
            )
            signals.append(
                Signal(
                    name="RSI",
                    direction=rsi_direction,
                    value=data.rsi,
                    unit="index",
                    rationale="RSI is calculated from the latest five price changes in the supplied series.",
                )
            )
        if data.macd is not None:
            histogram = data.macd["histogram"]
            signals.append(
                Signal(
                    name="MACD histogram",
                    direction=SignalDirection.POSITIVE if histogram > 0 else SignalDirection.NEGATIVE if histogram < 0 else SignalDirection.NEUTRAL,
                    value=histogram,
                    unit="USD_per_share",
                    rationale="The compact MACD histogram compares the 3/5-period MACD line with its 2-period signal line.",
                )
            )
        return signals

    @staticmethod
    def _opportunities_and_risks(data: TechnicalData) -> tuple[list[str], list[str]]:
        opportunities: list[str] = []
        risks: list[str] = []
        if data.trend == "uptrend":
            opportunities.append("The compact trend and moving-average alignment are constructive.")
        elif data.trend == "downtrend":
            risks.append("The compact trend and moving-average alignment remain weak.")
        if data.rsi is not None and data.rsi >= 70:
            risks.append("RSI is elevated on the compact lookback and may indicate stretched momentum.")
        elif data.rsi is not None and 50 <= data.rsi < 70:
            opportunities.append("RSI remains above its neutral midpoint without being overbought.")
        if data.volume_context and data.volume_context["label"] == "above_average":
            opportunities.append("Latest volume is above the five-period prior baseline.")
        elif data.volume_context and data.volume_context["label"] == "below_average":
            risks.append("Latest volume is below the five-period prior baseline.")
        return opportunities, risks

    async def _interpret_if_configured(
        self, run_context: RunContext, ticker: str, result: ExecutorResult
    ) -> ExecutorResult:
        if run_context.interpreter is None:
            return result
        interpretation = await run_context.interpreter.interpret(
            domain=self.domain.value,
            ticker=ticker,
            facts=result.data,
            evidence_ids=[item.evidence_id for item in result.evidence],
        )
        return result.model_copy(
            update={
                "summary": interpretation.summary,
                "opportunities": interpretation.opportunities,
                "risks": interpretation.risks,
                "evidence": [
                    *result.evidence,
                    self._runner.model_evidence(
                        run_context=run_context,
                        agent=self.agent_name,
                        cited_evidence_ids=interpretation.evidence_ids,
                    ),
                ],
            }
        )
