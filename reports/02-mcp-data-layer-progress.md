# Feature 02 MCP data layer progress

Status: complete
Date: 2026-09-12

## Outcome

The project now has a typed finance-data boundary backed by distinct deterministic fixtures for AAPL, TSLA, and MSFT. Executors can depend on one asynchronous `FinanceMCPClient` while transport selection remains configurable between in-memory, stdio, and HTTP modes.

## Implemented boundaries

- `src/providers/protocols.py`: market, company, news, and macro provider interfaces.
- `src/providers/schemas.py`: validated OHLCV, financial, metric, news, macro, sector, and competitor payloads with timestamps and units.
- `src/providers/fixtures.py`: compact, distinct mock data for three supported tickers and the US macro region.
- `src/providers/mock.py`: deterministic copy-on-read provider implementation safe for concurrent access.
- `src/mcp/server.py`: six finance tools with strict MCP inputs and sanitized provider failures.
- `src/mcp/client.py`: typed asynchronous adapter whose calls all pass through `FastMCP.Client.call_tool`.
- `src/mcp/transport.py`: in-memory default plus working stdio and HTTP transport selection.
- `src/mcp/telemetry.py`: non-blocking tool event hook carrying tool, ticker, run ID, status, duration, and error code.
- `src/mcp/main.py`: standalone stdio server entry point.

The unrelated demo tools, HTTP-only demo client, and duplicated MCP command notes were removed.

## Verification evidence

Command:

```text
.\venv\Scripts\python.exe -m pytest
```

Result:

```text
37 passed in 5.58s
```

The suite includes:

- direct tests of all provider capabilities;
- all six tools called through the typed in-memory MCP client boundary;
- a real stdio subprocess call through `python -m src.mcp.main`;
- concurrent AAPL, TSLA, and MSFT calls with distinct closing values;
- repeat-read and mutation-isolation checks;
- unknown ticker, unsupported timeframe, unknown region, provider failure, and malformed response cases;
- observer event context for successful and failed calls;
- assertions that provider credential text is absent from serialized errors and captured logs.

Additional checks:

- `python -m compileall -q src/providers src/mcp tests/unit/providers tests/integration`: passed.
- `python -m pip check`: no broken requirements found.
- `git diff --check`: no whitespace errors; only Windows line-ending notices.
- Search confirmed the obsolete `add`, `greet`, `code_review`, and hard-coded demo HTTP URL are absent from `src/mcp`.

## Design decisions confirmed by implementation

- Protocol-native MCP parameters use strings at the wire boundary. The provider converts and validates the timeframe enum so strict FastMCP validation remains compatible with JSON clients.
- FastMCP reconstructs typed results as generated dataclasses. The adapter intentionally validates `structured_content` back into application-owned Pydantic models.
- Unexpected provider exceptions are converted to a generic safe `ToolError` before FastMCP can log sensitive exception text.
- Observability failures are non-fatal and cannot change a finance-tool outcome.

## Deferred integration

The legacy `src/tools.py` remains until Feature 03 replaces its direct LangChain tool usage with the typed MCP client. Real providers, caching, authentication, and a separately deployed MCP service remain out of scope.

## Next dependency

Feature 03 can now implement independently invocable technical, fundamental, sentiment, and macro executor agents against `FinanceMCPClient` only.
