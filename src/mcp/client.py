"""Typed asynchronous adapter around FastMCP.Client.call_tool."""

from time import perf_counter
from typing import TypeVar

from fastmcp import Client
from pydantic import BaseModel

from src.core.config import Settings
from src.core.errors import MCPToolError
from src.mcp.telemetry import NoOpToolCallObserver, ToolCallEvent, ToolCallObserver
from src.mcp.transport import ClientTransportTarget, create_client_transport
from src.providers.schemas import (
    CompanyFinancialsResponse,
    CompanyMetricsResponse,
    MacroIndicatorsResponse,
    NewsResponse,
    OHLCVResponse,
    SectorDataResponse,
)
from src.schemas.enums import Timeframe

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class FinanceMCPClient:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: ClientTransportTarget | None = None,
        observer: ToolCallObserver | None = None,
    ) -> None:
        self._transport = transport or create_client_transport(settings)
        self._observer = observer or NoOpToolCallObserver()

    async def _call(
        self,
        tool: str,
        arguments: dict[str, object],
        response_type: type[ResponseT],
        *,
        ticker: str | None = None,
        run_id: str | None = None,
    ) -> ResponseT:
        started = perf_counter()
        status = "succeeded"
        error_code: str | None = None
        try:
            async with Client(self._transport) as client:
                result = await client.call_tool(
                    tool,
                    arguments,
                    meta={"run_id": run_id} if run_id else None,
                )
            payload = (
                result.structured_content
                if result.structured_content is not None
                else result.data
            )
            if isinstance(payload, response_type):
                return payload
            if isinstance(payload, BaseModel):
                payload = payload.model_dump(mode="json")
            return response_type.model_validate(payload)
        except Exception as exc:
            status = "failed"
            error_code = "mcp_tool_error"
            raise MCPToolError(
                "The finance data tool could not return a valid response.",
                run_id=run_id,
                ticker=ticker,
                tool=tool,
                operation="mcp_call",
                context={"failure_type": type(exc).__name__},
            ) from exc
        finally:
            event = ToolCallEvent(
                tool=tool,
                ticker=ticker,
                run_id=run_id,
                status=status,
                duration_ms=round((perf_counter() - started) * 1000, 3),
                error_code=error_code,
            )
            try:
                self._observer.record(event)
            except Exception:
                pass

    async def get_ohlcv(
        self,
        ticker: str,
        timeframe: Timeframe = Timeframe.ONE_YEAR,
        *,
        run_id: str | None = None,
    ) -> OHLCVResponse:
        return await self._call(
            "get_ohlcv",
            {"ticker": ticker, "timeframe": timeframe.value},
            OHLCVResponse,
            ticker=ticker,
            run_id=run_id,
        )

    async def get_company_financials(
        self, ticker: str, *, run_id: str | None = None
    ) -> CompanyFinancialsResponse:
        return await self._call(
            "get_company_financials",
            {"ticker": ticker},
            CompanyFinancialsResponse,
            ticker=ticker,
            run_id=run_id,
        )

    async def get_company_metrics(
        self, ticker: str, *, run_id: str | None = None
    ) -> CompanyMetricsResponse:
        return await self._call(
            "get_company_metrics",
            {"ticker": ticker},
            CompanyMetricsResponse,
            ticker=ticker,
            run_id=run_id,
        )

    async def get_news(self, ticker: str, *, run_id: str | None = None) -> NewsResponse:
        return await self._call(
            "get_news",
            {"ticker": ticker},
            NewsResponse,
            ticker=ticker,
            run_id=run_id,
        )

    async def get_macro_indicators(
        self, region: str = "US", *, run_id: str | None = None
    ) -> MacroIndicatorsResponse:
        return await self._call(
            "get_macro_indicators",
            {"region": region},
            MacroIndicatorsResponse,
            run_id=run_id,
        )

    async def get_sector_data(
        self, ticker: str, *, run_id: str | None = None
    ) -> SectorDataResponse:
        return await self._call(
            "get_sector_data",
            {"ticker": ticker},
            SectorDataResponse,
            ticker=ticker,
            run_id=run_id,
        )
