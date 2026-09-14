import asyncio

from src.core.errors import AgentExecutionError, MCPToolError
from src.executors import (
    ExecutorContext,
    FundamentalExecutor,
    MacroExecutor,
    SentimentExecutor,
    TechnicalExecutor,
)
from src.executors.interpreter import LunaStructuredInterpreter
from src.executors import technical as technical_module
from src.providers.mock import MockFinanceProvider
from src.schemas import AnalysisDomain, NormalizedRequest, OutcomeStatus


class FakeMCPClient:
    def __init__(self, provider: MockFinanceProvider | None = None) -> None:
        self.provider = provider or MockFinanceProvider()
        self.calls: list[str] = []
        self.failure: Exception | None = None
        self.fail_method: str | None = None

    def _result(self, method: str, *args):  # type: ignore[no-untyped-def]
        self.calls.append(method)
        if self.failure is not None and self.fail_method == method:
            raise self.failure
        return getattr(self.provider, method)(*args)

    async def get_ohlcv(self, ticker, timeframe, *, run_id=None):  # type: ignore[no-untyped-def]
        return self._result("get_ohlcv", ticker, timeframe)

    async def get_company_financials(self, ticker, *, run_id=None):  # type: ignore[no-untyped-def]
        return self._result("get_company_financials", ticker)

    async def get_company_metrics(self, ticker, *, run_id=None):  # type: ignore[no-untyped-def]
        return self._result("get_company_metrics", ticker)

    async def get_news(self, ticker, *, run_id=None):  # type: ignore[no-untyped-def]
        return self._result("get_news", ticker)

    async def get_macro_indicators(self, region="US", *, run_id=None):  # type: ignore[no-untyped-def]
        return self._result("get_macro_indicators", region)

    async def get_sector_data(self, ticker, *, run_id=None):  # type: ignore[no-untyped-def]
        return self._result("get_sector_data", ticker)


def make_request() -> NormalizedRequest:
    return NormalizedRequest(tickers=["AAPL"], domains=list(AnalysisDomain))


def test_each_executor_runs_independently_with_its_allowed_mcp_methods() -> None:
    async def scenario() -> None:
        client = FakeMCPClient()
        context = ExecutorContext(run_id="run-executors", mcp_client=client)
        request = make_request()
        cases = [
            (TechnicalExecutor(), {"get_ohlcv"}),
            (FundamentalExecutor(), {"get_company_financials", "get_company_metrics", "get_sector_data"}),
            (SentimentExecutor(), {"get_news"}),
            (MacroExecutor(), {"get_macro_indicators", "get_sector_data"}),
        ]
        for executor, expected_calls in cases:
            client.calls.clear()
            outcome = await executor.execute(context, "aapl", request)

            assert outcome.status is OutcomeStatus.SUCCEEDED
            assert outcome.ticker == "AAPL"
            assert outcome.domain is executor.domain
            assert outcome.data
            assert outcome.evidence
            assert set(client.calls) == expected_calls

    asyncio.run(scenario())


def test_every_domain_completes_for_every_supported_ticker() -> None:
    async def scenario() -> None:
        client = FakeMCPClient()
        context = ExecutorContext(run_id="run-all-tickers", mcp_client=client)
        request = make_request()
        executors = [TechnicalExecutor(), FundamentalExecutor(), SentimentExecutor(), MacroExecutor()]
        outcomes = await asyncio.gather(
            *(
                executor.execute(context, ticker, request)
                for ticker in client.provider.supported_tickers
                for executor in executors
            )
        )

        assert len(outcomes) == 12
        assert {outcome.ticker for outcome in outcomes} == {"AAPL", "TSLA", "MSFT"}
        assert {outcome.domain for outcome in outcomes} == set(AnalysisDomain)
        assert all(outcome.status is OutcomeStatus.SUCCEEDED for outcome in outcomes)

    asyncio.run(scenario())


def test_mcp_failure_becomes_a_context_rich_failed_domain_outcome() -> None:
    async def scenario() -> None:
        client = FakeMCPClient()
        client.fail_method = "get_news"
        client.failure = MCPToolError(
            "provider credential=private-value",
            ticker="AAPL",
            tool="get_news",
            operation="mcp_call",
        )
        outcome = await SentimentExecutor().execute(
            ExecutorContext(run_id="run-tool-failure", mcp_client=client), "AAPL", make_request()
        )

        assert outcome.status is OutcomeStatus.FAILED
        assert outcome.error is not None
        assert outcome.error.code == "mcp_tool_error"
        assert outcome.error.context == {
            "ticker": "AAPL",
            "tool": "get_news",
            "operation": "sentiment_analysis",
            "run_id": "run-tool-failure",
            "agent": "sentiment_executor",
            "error_type": "MCPToolError",
        }
        assert "private-value" not in outcome.error.model_dump_json()

    asyncio.run(scenario())


def test_structured_interpretation_failure_fails_only_that_domain() -> None:
    class FailingInterpreter:
        async def interpret(self, **kwargs):  # type: ignore[no-untyped-def]
            raise AgentExecutionError("invalid schema", context={"failure_type": "ValidationError"})

    async def scenario() -> None:
        outcome = await TechnicalExecutor().execute(
            ExecutorContext(
                run_id="run-interpretation-failure",
                mcp_client=FakeMCPClient(),
                interpreter=FailingInterpreter(),
            ),
            "AAPL",
            make_request(),
        )
        assert outcome.status is OutcomeStatus.FAILED
        assert outcome.error is not None
        assert outcome.error.context["agent"] == "technical_executor"
        assert outcome.error.context["operation"] == "technical_analysis"

    asyncio.run(scenario())


def test_calculation_failure_becomes_a_context_rich_failed_domain_outcome(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def failing_calculation(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise ValueError("invalid price series")

    monkeypatch.setattr(technical_module, "calculate_technical_indicators", failing_calculation)

    async def scenario() -> None:
        outcome = await TechnicalExecutor().execute(
            ExecutorContext(run_id="run-calculation-failure", mcp_client=FakeMCPClient()),
            "AAPL",
            make_request(),
        )
        assert outcome.status is OutcomeStatus.FAILED
        assert outcome.error is not None
        assert outcome.error.code == "agent_execution_error"
        assert outcome.error.context["error_type"] == "ValueError"
        assert outcome.error.context["run_id"] == "run-calculation-failure"

    asyncio.run(scenario())


def test_luna_interpreter_retries_one_invalid_structured_response() -> None:
    class FakeRunnable:
        def __init__(self) -> None:
            self.calls = 0

        async def ainvoke(self, prompt: str):
            self.calls += 1
            if self.calls == 1:
                return {"summary": "missing citations", "evidence_ids": []}
            return {
                "summary": "Grounded summary.",
                "opportunities": ["Supported opportunity."],
                "risks": [],
                "evidence_ids": ["mock:AAPL:ohlcv:2026-09-01"],
            }

    class FakeModel:
        def __init__(self) -> None:
            self.runnable = FakeRunnable()

        def with_structured_output(self, schema):  # type: ignore[no-untyped-def]
            return self.runnable

    async def scenario() -> None:
        model = FakeModel()
        result = await LunaStructuredInterpreter(model).interpret(
            domain="technical",
            ticker="AAPL",
            facts={"trend": "uptrend"},
            evidence_ids=["mock:AAPL:ohlcv:2026-09-01"],
        )
        assert result.summary == "Grounded summary."
        assert model.runnable.calls == 2

    asyncio.run(scenario())


def test_luna_interpreter_stops_after_one_schema_retry() -> None:
    class InvalidRunnable:
        def __init__(self) -> None:
            self.calls = 0

        async def ainvoke(self, prompt: str):
            self.calls += 1
            return {"summary": "uncited", "evidence_ids": []}

    class FakeModel:
        def __init__(self) -> None:
            self.runnable = InvalidRunnable()

        def with_structured_output(self, schema):  # type: ignore[no-untyped-def]
            return self.runnable

    async def scenario() -> None:
        model = FakeModel()
        try:
            await LunaStructuredInterpreter(model).interpret(
                domain="technical",
                ticker="AAPL",
                facts={"trend": "uptrend"},
                evidence_ids=["mock:AAPL:ohlcv:2026-09-01"],
            )
        except AgentExecutionError as error:
            assert error.to_detail().context["attempts"] == 2
        else:
            raise AssertionError("invalid structured output must fail after one retry")
        assert model.runnable.calls == 2

    asyncio.run(scenario())
