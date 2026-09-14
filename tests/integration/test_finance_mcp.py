import asyncio
import pytest
from fastmcp import Client, FastMCP
from fastmcp.client.transports import StdioTransport
from fastmcp.exceptions import ToolError

from src.core.config import Settings
from src.core.errors import MCPToolError
from src.mcp.client import FinanceMCPClient
from src.mcp.server import build_finance_server
from src.mcp.telemetry import ToolCallEvent
from src.mcp.transport import create_client_transport
from src.providers.mock import MockFinanceProvider
from src.schemas.enums import SourceType, Timeframe


def make_settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, openai_api_key="test-only", **overrides)


class CapturingObserver:
    def __init__(self) -> None:
        self.events: list[ToolCallEvent] = []

    def record(self, event: ToolCallEvent) -> None:
        self.events.append(event)


def test_six_tools_are_exposed_by_finance_server() -> None:
    async def scenario() -> None:
        async with Client(build_finance_server()) as client:
            names = {tool.name for tool in await client.list_tools()}

        assert names == {
            "get_ohlcv",
            "get_company_financials",
            "get_company_metrics",
            "get_news",
            "get_macro_indicators",
            "get_sector_data",
        }

    asyncio.run(scenario())


def test_every_tool_round_trips_through_typed_client_adapter() -> None:
    async def scenario() -> None:
        observer = CapturingObserver()
        client = FinanceMCPClient(
            make_settings(), transport=build_finance_server(), observer=observer
        )

        payloads = [
            await client.get_ohlcv("AAPL", Timeframe.ONE_YEAR, run_id="run-1"),
            await client.get_company_financials("AAPL", run_id="run-1"),
            await client.get_company_metrics("AAPL", run_id="run-1"),
            await client.get_news("AAPL", run_id="run-1"),
            await client.get_macro_indicators("US", run_id="run-1"),
            await client.get_sector_data("AAPL", run_id="run-1"),
        ]

        assert all(payload.source_type is SourceType.MOCK for payload in payloads)
        assert [event.tool for event in observer.events] == [
            "get_ohlcv",
            "get_company_financials",
            "get_company_metrics",
            "get_news",
            "get_macro_indicators",
            "get_sector_data",
        ]
        assert all(event.status == "succeeded" for event in observer.events)
        assert all(event.duration_ms >= 0 for event in observer.events)
        assert observer.events[0].ticker == "AAPL"
        assert observer.events[0].run_id == "run-1"

    asyncio.run(scenario())


def test_concurrent_ticker_calls_through_in_memory_transport() -> None:
    async def scenario() -> None:
        client = FinanceMCPClient(make_settings(), transport=build_finance_server())
        responses = await asyncio.gather(
            *(client.get_ohlcv(ticker) for ticker in ("AAPL", "TSLA", "MSFT"))
        )
        assert [response.ticker for response in responses] == ["AAPL", "TSLA", "MSFT"]
        assert len({response.bars[-1].close for response in responses}) == 3

    asyncio.run(scenario())


def test_unknown_ticker_is_translated_with_safe_context() -> None:
    async def scenario() -> None:
        observer = CapturingObserver()
        client = FinanceMCPClient(
            make_settings(), transport=build_finance_server(), observer=observer
        )

        with pytest.raises(MCPToolError) as caught:
            await client.get_news("NVDA", run_id="run-failed")

        detail = caught.value.to_detail()
        assert detail.code == "mcp_tool_error"
        assert detail.context["ticker"] == "NVDA"
        assert detail.context["tool"] == "get_news"
        assert observer.events[-1].status == "failed"
        assert observer.events[-1].error_code == "mcp_tool_error"

    asyncio.run(scenario())


def test_invalid_timeframe_is_rejected_at_mcp_boundary() -> None:
    async def scenario() -> None:
        async with Client(build_finance_server()) as client:
            with pytest.raises(ToolError):
                await client.call_tool("get_ohlcv", {"ticker": "AAPL", "timeframe": "2y"})

    asyncio.run(scenario())


class FailingProvider(MockFinanceProvider):
    def get_news(self, ticker: str):  # type: ignore[no-untyped-def]
        raise RuntimeError("provider credential=private-value")


def test_provider_failure_is_translated_without_leaking_details(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def scenario() -> None:
        client = FinanceMCPClient(
            make_settings(), transport=build_finance_server(FailingProvider())
        )
        with pytest.raises(MCPToolError) as caught:
            await client.get_news("AAPL")

        serialized = caught.value.to_detail().model_dump_json()
        assert "private-value" not in serialized
        assert caught.value.to_detail().context["failure_type"] == "ToolError"

    asyncio.run(scenario())
    assert "private-value" not in caplog.text


def test_malformed_tool_response_is_rejected_by_adapter() -> None:
    malformed_server = FastMCP("Malformed finance server")

    @malformed_server.tool(name="get_company_metrics")
    def malformed_metrics(ticker: str) -> dict[str, str]:
        return {"ticker": ticker}

    async def scenario() -> None:
        client = FinanceMCPClient(make_settings(), transport=malformed_server)
        with pytest.raises(MCPToolError) as caught:
            await client.get_company_metrics("AAPL")
        assert caught.value.to_detail().context["failure_type"] == "ValidationError"

    asyncio.run(scenario())


def test_transport_factory_keeps_client_interface_stable() -> None:
    memory_server = build_finance_server()
    assert create_client_transport(
        make_settings(mcp_transport="memory"), in_memory_server=memory_server
    ) is memory_server

    http_transport = create_client_transport(
        make_settings(mcp_transport="http", mcp_url="https://finance.example.test/mcp")
    )
    assert str(http_transport).startswith("https://finance.example.test/mcp")

    stdio_transport = create_client_transport(make_settings(mcp_transport="stdio"))
    assert isinstance(stdio_transport, StdioTransport)
    assert stdio_transport.args == ["-m", "src.mcp.main"]


def test_stdio_transport_can_call_finance_server() -> None:
    async def scenario() -> None:
        client = FinanceMCPClient(make_settings(mcp_transport="stdio"))
        response = await client.get_company_metrics("AAPL")
        assert response.metrics["price_to_earnings"].value == 31.8

    asyncio.run(scenario())
