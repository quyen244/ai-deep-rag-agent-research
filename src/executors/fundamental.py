"""Deterministic fundamental-analysis executor using typed finance MCP data."""

import asyncio

from src.executors.calculations import rounded, safe_divide
from src.executors.context import RunContext
from src.executors.contracts import ExecutorResult, FundamentalData
from src.executors.runner import ExecutorRunner
from src.providers.schemas import (
    CompanyFinancialsResponse,
    CompanyMetricsResponse,
    SectorDataResponse,
)
from src.schemas.common import EvidenceItem, Signal
from src.schemas.domain import DomainOutcome
from src.schemas.enums import AnalysisDomain, SignalDirection, SourceType
from src.schemas.request import NormalizedRequest


def calculate_fundamental_analysis(
    financials: CompanyFinancialsResponse,
    metrics: CompanyMetricsResponse,
    sector: SectorDataResponse,
) -> FundamentalData:
    """Compute source-supported margins, returns, and leverage deterministically."""

    unavailable: dict[str, str] = {
        "revenue_trend": "Only one fiscal-year revenue observation is available from the MCP source.",
        "earnings_trend": "Only one fiscal-year net-income observation is available from the MCP source.",
        "price_to_book": "The MCP source does not provide book value per share or price-to-book.",
        "ev_to_ebitda": "The MCP source does not provide enterprise value or EBITDA.",
        "current_ratio": "The MCP source does not provide current assets and current liabilities.",
    }
    price_to_earnings = metrics.metrics.get("price_to_earnings")
    sector_pe = sector.metrics.get("median_price_to_earnings")
    if price_to_earnings is None:
        unavailable["price_to_earnings"] = "The company metrics source did not provide price-to-earnings."
    if sector_pe is None:
        unavailable["valuation_premium_to_sector_percent"] = "The sector source did not provide median price-to-earnings."

    gross_margin = safe_divide(financials.gross_profit, financials.revenue, multiplier=100)
    operating_margin = safe_divide(financials.operating_income, financials.revenue, multiplier=100)
    net_margin = safe_divide(financials.net_income, financials.revenue, multiplier=100)
    roe = safe_divide(financials.net_income, financials.shareholders_equity, multiplier=100)
    roa = safe_divide(financials.net_income, financials.total_assets, multiplier=100)
    debt_to_equity = safe_divide(financials.total_liabilities, financials.shareholders_equity)
    liabilities_to_assets = safe_divide(financials.total_liabilities, financials.total_assets, multiplier=100)
    fcf_margin = safe_divide(financials.free_cash_flow, financials.revenue, multiplier=100)
    for key, value in {
        "gross_margin": gross_margin,
        "operating_margin": operating_margin,
        "net_margin": net_margin,
        "return_on_equity": roe,
        "return_on_assets": roa,
        "debt_to_equity": debt_to_equity,
        "liabilities_to_assets": liabilities_to_assets,
        "free_cash_flow_margin": fcf_margin,
    }.items():
        if value is None:
            unavailable[key] = "A required financial-statement denominator is zero."

    valuation_premium = None
    if price_to_earnings is not None and sector_pe is not None:
        valuation_premium = safe_divide(
            price_to_earnings.value - sector_pe.value, sector_pe.value, multiplier=100
        )
        if valuation_premium is None:
            unavailable["valuation_premium_to_sector_percent"] = "Sector median price-to-earnings is zero."

    if financials.free_cash_flow > 0 and (liabilities_to_assets is None or liabilities_to_assets < 70):
        financial_health = "cash-generative"
    elif financials.free_cash_flow > 0:
        financial_health = "cash-generative_with_elevated_liabilities"
    else:
        financial_health = "cash-flow-under-pressure"

    return FundamentalData(
        fiscal_year=financials.fiscal_year,
        revenue=financials.revenue,
        net_income=financials.net_income,
        gross_margin=rounded(gross_margin),
        operating_margin=rounded(operating_margin),
        net_margin=rounded(net_margin),
        price_to_earnings=rounded(price_to_earnings.value) if price_to_earnings else None,
        price_to_book=None,
        ev_to_ebitda=None,
        return_on_equity=rounded(roe),
        return_on_assets=rounded(roa),
        debt_to_equity=rounded(debt_to_equity),
        liabilities_to_assets=rounded(liabilities_to_assets),
        current_ratio=None,
        free_cash_flow_margin=rounded(fcf_margin),
        revenue_trend=None,
        earnings_trend=None,
        financial_health=financial_health,
        valuation_premium_to_sector_percent=rounded(valuation_premium),
        unavailable=unavailable,
    )


class FundamentalExecutor:
    """Analyze financial statements, supplied market metrics, and sector benchmark."""

    domain = AnalysisDomain.FUNDAMENTAL
    agent_name = "fundamental_executor"

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
            operation="fundamental_analysis",
            worker=lambda: self._analyze(run_context, normalized_ticker),
        )

    async def _analyze(self, run_context: RunContext, ticker: str) -> ExecutorResult:
        financials, metrics, sector = await asyncio.gather(
            run_context.mcp_client.get_company_financials(ticker, run_id=run_context.run_id),
            run_context.mcp_client.get_company_metrics(ticker, run_id=run_context.run_id),
            run_context.mcp_client.get_sector_data(ticker, run_id=run_context.run_id),
        )
        data = calculate_fundamental_analysis(financials, metrics, sector)
        evidence = [
            EvidenceItem(
                evidence_id=f"mock:{ticker}:financials:{financials.fiscal_year}",
                title=f"{ticker} fiscal {financials.fiscal_year} financial statements",
                source="finance_mcp.get_company_financials",
                source_type=SourceType.MOCK,
                observed_at=financials.as_of,
                details={
                    "revenue": financials.revenue,
                    "gross_profit": financials.gross_profit,
                    "operating_income": financials.operating_income,
                    "net_income": financials.net_income,
                    "total_assets": financials.total_assets,
                    "total_liabilities": financials.total_liabilities,
                    "shareholders_equity": financials.shareholders_equity,
                    "free_cash_flow": financials.free_cash_flow,
                    "operating_cash_flow": financials.operating_cash_flow,
                },
            ),
            EvidenceItem(
                evidence_id=f"mock:{ticker}:company_metrics:{metrics.as_of.date().isoformat()}",
                title=f"{ticker} supplied valuation metrics",
                source="finance_mcp.get_company_metrics",
                source_type=SourceType.MOCK,
                observed_at=metrics.as_of,
                details={key: value.model_dump(mode="json") for key, value in metrics.metrics.items()},
            ),
            EvidenceItem(
                evidence_id=f"mock:{ticker}:sector:{sector.as_of.date().isoformat()}",
                title=f"{ticker} sector benchmark",
                source="finance_mcp.get_sector_data",
                source_type=SourceType.MOCK,
                observed_at=sector.as_of,
                details={"sector": sector.sector, "metrics": {key: value.model_dump(mode="json") for key, value in sector.metrics.items()}},
            ),
        ]
        opportunities, risks = self._opportunities_and_risks(data)
        result = ExecutorResult(
            summary=(
                f"{ticker} is {data.financial_health}; fiscal {data.fiscal_year} net margin is "
                f"{data.net_margin}% and free-cash-flow margin is {data.free_cash_flow_margin}%."
            ),
            signals=self._signals(data),
            opportunities=opportunities,
            risks=risks,
            evidence=evidence,
            data=data.model_dump(mode="json"),
        )
        return await self._interpret_if_configured(run_context, ticker, result)

    @staticmethod
    def _signals(data: FundamentalData) -> list[Signal]:
        signals: list[Signal] = []
        if data.net_margin is not None:
            signals.append(
                Signal(
                    name="Net margin",
                    direction=SignalDirection.POSITIVE if data.net_margin >= 15 else SignalDirection.NEGATIVE if data.net_margin < 5 else SignalDirection.NEUTRAL,
                    value=data.net_margin,
                    unit="percent",
                    rationale="Net income divided by revenue from the supplied financial statements.",
                )
            )
        if data.debt_to_equity is not None:
            signals.append(
                Signal(
                    name="Liabilities to equity",
                    direction=SignalDirection.NEGATIVE if data.debt_to_equity > 2 else SignalDirection.POSITIVE if data.debt_to_equity <= 1 else SignalDirection.NEUTRAL,
                    value=data.debt_to_equity,
                    unit="ratio",
                    rationale="Total liabilities divided by shareholders' equity; it is not a debt-only measure.",
                )
            )
        if data.valuation_premium_to_sector_percent is not None:
            signals.append(
                Signal(
                    name="P/E premium to sector",
                    direction=SignalDirection.NEGATIVE if data.valuation_premium_to_sector_percent > 0 else SignalDirection.POSITIVE,
                    value=data.valuation_premium_to_sector_percent,
                    unit="percent",
                    rationale="Company P/E compared with the supplied sector median P/E.",
                )
            )
        return signals

    @staticmethod
    def _opportunities_and_risks(data: FundamentalData) -> tuple[list[str], list[str]]:
        opportunities: list[str] = []
        risks: list[str] = []
        if data.free_cash_flow_margin is not None and data.free_cash_flow_margin > 10:
            opportunities.append("Free cash flow is positive and represents more than 10% of supplied revenue.")
        if data.return_on_assets is not None and data.return_on_assets >= 10:
            opportunities.append("Return on assets is above 10% on the supplied fiscal-year values.")
        if data.debt_to_equity is not None and data.debt_to_equity > 2:
            risks.append("Total liabilities are more than twice shareholders' equity.")
        if data.valuation_premium_to_sector_percent is not None and data.valuation_premium_to_sector_percent > 0:
            risks.append("Supplied P/E is above the supplied sector median.")
        risks.extend(
            "Unavailable: " + reason
            for name, reason in data.unavailable.items()
            if name in {"price_to_book", "ev_to_ebitda", "current_ratio"}
        )
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
