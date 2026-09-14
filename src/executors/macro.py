"""Macro executor joining economy-wide and ticker-sector MCP evidence."""

import asyncio

from src.executors.context import RunContext
from src.executors.contracts import ExecutorResult, MacroData
from src.executors.runner import ExecutorRunner
from src.schemas.common import EvidenceItem, Signal
from src.schemas.domain import DomainOutcome
from src.schemas.enums import AnalysisDomain, SignalDirection, SourceType
from src.schemas.request import NormalizedRequest


def _indicator_value(indicators, key: str, unavailable: dict[str, str]) -> float | None:  # type: ignore[no-untyped-def]
    item = indicators.get(key)
    if item is None:
        unavailable[key] = f"The MCP macro source did not provide {key}."
        return None
    return item.value


class MacroExecutor:
    """Describe macro conditions, sector context, competitors, and implications."""

    domain = AnalysisDomain.MACRO
    agent_name = "macro_executor"

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
            operation="macro_analysis",
            worker=lambda: self._analyze(run_context, normalized_ticker),
        )

    async def _analyze(self, run_context: RunContext, ticker: str) -> ExecutorResult:
        macro, sector = await asyncio.gather(
            run_context.mcp_client.get_macro_indicators(
                run_context.macro_region, run_id=run_context.run_id
            ),
            run_context.mcp_client.get_sector_data(ticker, run_id=run_context.run_id),
        )
        unavailable: dict[str, str] = {}
        gdp = _indicator_value(macro.indicators, "gdp_growth_annualized", unavailable)
        inflation = _indicator_value(macro.indicators, "inflation_year_over_year", unavailable)
        policy_rate = _indicator_value(macro.indicators, "policy_rate", unavailable)
        treasury = _indicator_value(macro.indicators, "ten_year_treasury_yield", unavailable)
        unemployment = _indicator_value(macro.indicators, "unemployment_rate", unavailable)
        sector_growth_metric = sector.metrics.get("annual_growth")
        if sector_growth_metric is None:
            unavailable["sector_annual_growth"] = "The MCP sector source did not provide annual growth."
        sector_growth = sector_growth_metric.value if sector_growth_metric else None

        market_condition = self._market_condition(gdp, inflation)
        implications = self._implications(
            sector=sector.sector,
            sector_growth=sector_growth,
            policy_rate=policy_rate,
            competitors=[competitor.ticker for competitor in sector.competitors],
        )
        data = MacroData(
            region=macro.region,
            gdp_growth_annualized=gdp,
            inflation_year_over_year=inflation,
            policy_rate=policy_rate,
            ten_year_treasury_yield=treasury,
            unemployment_rate=unemployment,
            market_condition=market_condition,
            sector=sector.sector,
            industry=sector.industry,
            sector_annual_growth=sector_growth,
            competitors=[competitor.model_dump(mode="json") for competitor in sector.competitors],
            company_implications=implications,
            unavailable=unavailable,
        )
        evidence = [
            EvidenceItem(
                evidence_id=f"mock:{macro.region}:macro:{macro.as_of.date().isoformat()}",
                title=f"{macro.region} macro indicators",
                source="finance_mcp.get_macro_indicators",
                source_type=SourceType.MOCK,
                observed_at=macro.as_of,
                details={key: value.model_dump(mode="json") for key, value in macro.indicators.items()},
            ),
            EvidenceItem(
                evidence_id=f"mock:{ticker}:sector:{sector.as_of.date().isoformat()}",
                title=f"{ticker} sector and competitor snapshot",
                source="finance_mcp.get_sector_data",
                source_type=SourceType.MOCK,
                observed_at=sector.as_of,
                details={
                    "sector": sector.sector,
                    "industry": sector.industry,
                    "metrics": {key: value.model_dump(mode="json") for key, value in sector.metrics.items()},
                    "competitors": [competitor.model_dump(mode="json") for competitor in sector.competitors],
                },
            ),
        ]
        opportunities, risks = self._opportunities_and_risks(data)
        result = ExecutorResult(
            summary=(
                f"{ticker} operates in {sector.sector}/{sector.industry}; {market_condition}. "
                f"The supplied sector annual growth is {sector_growth}% if available."
            ),
            signals=self._signals(data),
            opportunities=opportunities,
            risks=risks,
            evidence=evidence,
            data=data.model_dump(mode="json"),
        )
        return await self._interpret_if_configured(run_context, ticker, result)

    @staticmethod
    def _market_condition(gdp: float | None, inflation: float | None) -> str:
        if gdp is not None and gdp > 0 and inflation is not None and inflation <= 3:
            return "positive_growth_with_contained_inflation"
        if gdp is not None and gdp <= 0:
            return "contracting_or_stalled_growth"
        if inflation is not None and inflation > 3:
            return "elevated_inflation"
        return "incomplete_macro_evidence"

    @staticmethod
    def _implications(
        *, sector: str, sector_growth: float | None, policy_rate: float | None, competitors: list[str]
    ) -> list[str]:
        implications: list[str] = []
        if sector_growth is not None and sector_growth > 0:
            implications.append(f"The supplied {sector} sector benchmark reports positive annual growth.")
        elif sector_growth is not None:
            implications.append(f"The supplied {sector} sector benchmark reports non-positive annual growth.")
        if policy_rate is not None and policy_rate >= 4:
            implications.append("The supplied policy rate keeps discount-rate sensitivity elevated.")
        if competitors:
            implications.append("The supplied competitor set is " + ", ".join(competitors) + ".")
        return implications

    @staticmethod
    def _signals(data: MacroData) -> list[Signal]:
        signals: list[Signal] = []
        if data.gdp_growth_annualized is not None:
            signals.append(
                Signal(
                    name="GDP growth",
                    direction=SignalDirection.POSITIVE if data.gdp_growth_annualized > 0 else SignalDirection.NEGATIVE,
                    value=data.gdp_growth_annualized,
                    unit="percent",
                    rationale="Annualized GDP growth from the supplied regional macro indicators.",
                )
            )
        if data.policy_rate is not None:
            signals.append(
                Signal(
                    name="Policy rate",
                    direction=SignalDirection.NEGATIVE if data.policy_rate >= 4 else SignalDirection.NEUTRAL,
                    value=data.policy_rate,
                    unit="percent",
                    rationale="A higher supplied policy rate can increase discount-rate sensitivity.",
                )
            )
        return signals

    @staticmethod
    def _opportunities_and_risks(data: MacroData) -> tuple[list[str], list[str]]:
        opportunities = [
            implication for implication in data.company_implications if "positive annual growth" in implication
        ]
        risks = [
            implication
            for implication in data.company_implications
            if "discount-rate sensitivity" in implication or "non-positive" in implication
        ]
        risks.extend("Unavailable: " + reason for reason in data.unavailable.values())
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
