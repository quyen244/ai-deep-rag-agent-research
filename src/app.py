"""Small application-facing helper over the deterministic orchestrator."""

from uuid import UUID

from src.orchestration.graph import AnalysisOrchestrator
from src.schemas.request import AnalysisRequest
from src.schemas.run import RunState


async def run_financial_analysis(
    orchestrator: AnalysisOrchestrator, *, run_id: UUID, request: AnalysisRequest
) -> RunState:
    """Run one typed analysis without message scraping or supervisor routing."""

    return await orchestrator.run(run_id=run_id, request=request)
