# MCP mock data layer

Status: implemented
Owner: backend MCP and provider packages
Depends on: 01-foundation
Consumed by: 03-executor-agents

## Problem

Agents directly import LangChain tools that contain inline Apple-like data. Unsupported tickers are accepted and every ticker receives the same values. The FastMCP demo is unrelated to finance.

## Goal

Establish a real, typed MCP boundary backed by small, realistic, deterministic, and replaceable mock providers.

## Scope

Included: provider protocols, AAPL/TSLA/MSFT mock fixtures, one FastMCP finance server, one MCP client adapter, six finance tools, error translation, and tool metrics hooks.

Non-goals: external APIs, crawling, provider authentication, a separately deployed MCP process, caches, and databases.

## Current behavior

`src/tools.py` owns five regular LangChain tools. `src/mcp/main.py` exposes only `add`, `greet`, and `code_review`. The MCP client expects HTTP while the server starts on stdio.

## Desired behavior

Executors call a typed client adapter. The adapter opens a FastMCP client session against the finance server using in-memory transport. MCP tools delegate to provider interfaces and return validated structured data.

## Architecture impact

```mermaid
flowchart LR
    E[Executor] --> C[Finance MCP client adapter]
    C --> S[FastMCP finance server]
    S --> P[Mock provider interfaces]
    P --> F[Compact ticker fixtures]
```

Provider implementations know nothing about MCP or agents. MCP handlers contain no financial analysis logic.

## Interfaces and contracts

- `get_ohlcv(ticker, timeframe)`
- `get_company_financials(ticker)`
- `get_company_metrics(ticker)`
- `get_news(ticker)`
- `get_macro_indicators(region)`
- `get_sector_data(ticker)`

All responses include `as_of`, `source_type: "mock"`, and appropriate units. Unknown tickers raise `MCPToolError` with safe tool and ticker context.

## Edge cases and recovery

| Case | Behavior | Recovery |
|---|---|---|
| Unknown ticker | Typed not-found tool error | Use one of the supported mock tickers |
| Unsupported timeframe | Typed invalid-argument error | Select a supported timeframe |
| Provider exception | Translate once at MCP adapter boundary | Fix provider or submit later |
| Malformed tool payload | Reject during schema validation | Correct provider fixture or tool mapping |
| Concurrent calls | Read immutable fixtures safely | No user action |

## Acceptance criteria

- Each of AAPL, TSLA, and MSFT returns distinct realistic data.
- Unknown tickers fail deterministically.
- Every finance capability is reached through `FastMCP.Client.call_tool`.
- Agent-facing code imports no concrete mock fixture.
- In-memory transport can be replaced through configuration without changing executor code.
- Tool logs and metrics receive tool, ticker, status, and duration context.

## Testing strategy

Test providers directly, then call every tool through a FastMCP client session. Inject provider failures and malformed outputs. Verify determinism and concurrent reads.
