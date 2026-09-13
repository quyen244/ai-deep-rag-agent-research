import asyncio

from src.core.config import Settings
from src.executors import (
    ExecutorContext,
    FundamentalExecutor,
    MacroExecutor,
    SentimentExecutor,
    TechnicalExecutor,
)
from src.mcp.client import FinanceMCPClient
from src.mcp.server import build_finance_server
from src.providers.mock import MockFinanceProvider
from src.schemas import AnalysisDomain, NormalizedRequest, OutcomeStatus, SourceType


def test_all_executors_complete_through_real_in_memory_mcp_client() -> None:
    async def scenario() -> None:
        client = FinanceMCPClient(
            Settings(_env_file=None, openai_api_key="test-only"),
            transport=build_finance_server(),
        )
        context = ExecutorContext(run_id="run-real-mcp", mcp_client=client)
        request = NormalizedRequest(
            tickers=list(MockFinanceProvider.supported_tickers), domains=list(AnalysisDomain)
        )
        executors = [TechnicalExecutor(), FundamentalExecutor(), SentimentExecutor(), MacroExecutor()]
        outcomes = await asyncio.gather(
            *(
                executor.execute(context, ticker, request)
                for ticker in request.tickers
                for executor in executors
            )
        )

        assert len(outcomes) == 12
        assert all(outcome.status is OutcomeStatus.SUCCEEDED for outcome in outcomes)
        assert all(outcome.evidence for outcome in outcomes)
        assert all(
            any(item.source_type is SourceType.MOCK for item in outcome.evidence)
            for outcome in outcomes
        )

    asyncio.run(scenario())
