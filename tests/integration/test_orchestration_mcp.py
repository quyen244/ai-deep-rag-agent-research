import asyncio

from src.core.config import Settings
from src.core.ids import new_run_id
from src.mcp.client import FinanceMCPClient
from src.mcp.server import build_finance_server
from src.orchestration import AnalysisOrchestrator
from src.schemas import AnalysisRequest, RunStatus


def test_orchestrator_runs_two_tickers_through_real_in_memory_mcp() -> None:
    async def scenario() -> None:
        orchestrator = AnalysisOrchestrator(
            mcp_client=FinanceMCPClient(
                Settings(_env_file=None, openai_api_key="test-only"),
                transport=build_finance_server(),
            )
        )
        run = await orchestrator.run(
            run_id=new_run_id(), request=AnalysisRequest(request_text="Analyze AAPL and TSLA")
        )

        assert run.status is RunStatus.SUCCEEDED
        assert run.report is not None
        assert run.report.comparison is not None
        assert run.report.execution.requested_tasks == 8
        assert run.report.execution.succeeded_tasks == 8

    asyncio.run(scenario())
