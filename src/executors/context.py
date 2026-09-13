"""Dependencies and stable identity passed to every executor invocation."""

from dataclasses import dataclass, field
from typing import Protocol

from src.core.clock import Clock, SystemClock
from src.providers.schemas import (
    CompanyFinancialsResponse,
    CompanyMetricsResponse,
    MacroIndicatorsResponse,
    NewsResponse,
    OHLCVResponse,
    SectorDataResponse,
)
from src.schemas.enums import Timeframe


class FinanceDataClient(Protocol):
    """The narrow MCP-client surface used by executors.

    Keeping this protocol local makes fake clients straightforward and prevents an
    executor from reaching into a provider implementation.
    """

    async def get_ohlcv(
        self, ticker: str, timeframe: Timeframe = Timeframe.ONE_YEAR, *, run_id: str | None = None
    ) -> OHLCVResponse: ...

    async def get_company_financials(
        self, ticker: str, *, run_id: str | None = None
    ) -> CompanyFinancialsResponse: ...

    async def get_company_metrics(
        self, ticker: str, *, run_id: str | None = None
    ) -> CompanyMetricsResponse: ...

    async def get_news(self, ticker: str, *, run_id: str | None = None) -> NewsResponse: ...

    async def get_macro_indicators(
        self, region: str = "US", *, run_id: str | None = None
    ) -> MacroIndicatorsResponse: ...

    async def get_sector_data(
        self, ticker: str, *, run_id: str | None = None) -> SectorDataResponse: ...


class InterpretationClient(Protocol):
    """Optional structured interpretation boundary, normally backed by Luna."""

    async def interpret(
        self,
        *,
        domain: str,
        ticker: str,
        facts: dict[str, object],
        evidence_ids: list[str],
    ) -> "StructuredInterpretation": ...


@dataclass(frozen=True, slots=True)
class RunContext:
    """Run-scoped dependencies shared by all domain executors."""

    run_id: str
    mcp_client: FinanceDataClient
    clock: Clock = field(default_factory=SystemClock)
    interpreter: InterpretationClient | None = None
    macro_region: str = "US"


# ``ExecutorContext`` is retained as the public spelling used in the feature
# contract; ``RunContext`` better communicates that it is created once per run.
ExecutorContext = RunContext


# This import is deliberately deferred for type checking only, avoiding a
# runtime cycle between context and the optional interpreter implementation.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.executors.interpreter import StructuredInterpretation
