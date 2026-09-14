# Feature 03 executor agents progress

Status: complete  
Date: 2026-09-13

## Outcome

Four independently invocable, typed executors now produce a validated
`DomainOutcome` for one `(run_context, ticker, normalized_request)` task:

- Technical: OHLCV-only trend, RSI, compact MACD, SMA/EMA, Bollinger Bands,
  volume context, support, and resistance.
- Fundamental: deterministic statement-based margins, ROE, ROA, leverage,
  free-cash-flow margin, supplied P/E, and sector P/E comparison.
- Sentiment: deterministic mean article score, label, item counts, topics,
  headlines, and negative-news risk.
- Macro: US GDP, CPI, policy and Treasury rates, labor data, sector condition,
  competitors, and deterministic company implications.

`None` fields include an `unavailable` reason when the MCP data does not
support a responsible calculation. This applies to multi-period revenue and
earnings trends, P/B, EV/EBITDA, and current ratio with the present fixture.
No zero denominator is substituted with a fabricated value.

## Boundaries

- `src/executors/context.py` defines the narrow typed MCP protocol and stable
  run context. Executors depend on that protocol, never a provider or another
  executor.
- `src/executors/runner.py` owns duration measurement, outcome validation,
  non-fatal execution observation, and sanitised failure envelopes. All failed
  outcomes carry run ID, ticker, agent, operation, and error type.
- `src/executors/interpreter.py` supplies optional Luna structured narration.
  It receives compact calculated facts and allowed evidence IDs, accepts no
  model-authored data fields, validates citations, and permits exactly one
  schema retry.
- Evidence records preserve the originating MCP method and timestamp; optional
  model narration adds a model evidence item with its cited source IDs.
- The legacy ReAct factories and direct LangChain tool lists were removed.
  The old supervisor import is retained only as an explicit Feature 04
  migration message, so it no longer imports undeclared legacy dependencies.

## Verification evidence

Command:

```text
venv/bin/python -m pytest
```

Result:

```text
50 passed in 3.30s
```

The executor coverage includes pure technical, fundamental, and sentiment
calculations; unavailable compact-series and zero-denominator behavior; each
executor's MCP allowlist; all four executors for AAPL, TSLA, and MSFT; tool,
calculation, and structured-output failures; a successful schema retry and
failure after the retry bound; and all domains through the real in-memory
FastMCP client.

Additional checks passed:

```text
venv/bin/python -m compileall -q src tests
venv/bin/python -m pip check
git diff --check
```
