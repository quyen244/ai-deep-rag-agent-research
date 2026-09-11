# Executor agents

Status: approved
Owner: backend agent package
Depends on: 01-foundation, 02-mcp-data-layer
Consumed by: 04-orchestration-synthesis

## Problem

Only three agents exist, their prompts return prose, and they do not write typed domain outcomes. There is no macro executor and current calculations omit required indicators and ratios.

## Goal

Provide four independently invocable executors that consume MCP data and return validated, concise domain outcomes per ticker.

## Scope

Included: technical, fundamental, sentiment, and macro executors; shared execution envelope; compact prompts; deterministic calculations where possible; Luna-based interpretation; partial failure support.

Non-goals: alpha signals, trade instructions, Validator behavior, real data providers, and cross-stock synthesis.

## Current behavior

Three `create_react_agent` factories use direct LangChain tools. Output is free-form Markdown embedded in messages. Tool usage and response shape are enforced only by prompts.

## Desired behavior

Each executor accepts `(run_context, ticker, normalized_request)`, calls only its allowed MCP methods, computes deterministic measures in ordinary Python, and optionally uses Luna for bounded interpretation into a structured schema.

## Architecture impact

Executors own domain interpretation but not routing, persistence, API behavior, or provider implementation. A shared runner standardizes timing, tracing, logging, error conversion, and output validation.

## Interfaces and contracts

- Technical: trend, RSI, MACD, SMA/EMA, Bollinger Bands, volume context, support, resistance, and interpretation.
- Fundamental: revenue and earnings trend, margins, P/E, P/B, EV/EBITDA, ROE, ROA, leverage, liquidity, and financial health.
- Sentiment: positive/neutral/negative label, score from -1 to 1, narratives, item evidence, and sentiment risks.
- Macro: GDP, CPI, rates, market and sector conditions, competitors, and company implications.
- Shared `DomainOutcome` status: `succeeded` or `failed`. The orchestrator derives overall partial status.

## Edge cases and recovery

| Case | Behavior | Recovery |
|---|---|---|
| Insufficient rows for an indicator | Return unavailable field plus evidence warning | Use a supported timeframe |
| Division denominator is zero | Return unavailable ratio, never substitute 1 | Inspect source fixture |
| MCP tool fails | Return a failed domain outcome with sanitized context | Submit a new run after correction |
| LLM output violates schema | One bounded structured-output retry, then fail the domain | Resubmit after service recovery |
| Agent invoked alone | Produce the same contract as graph invocation | No special action |

## Acceptance criteria

- Each executor runs independently for every supported ticker.
- Required domain fields are populated from MCP evidence or explicitly marked unavailable.
- Financial calculations are deterministic Python functions with unit tests.
- LLM interpretation uses structured output and cannot invent evidence fields.
- Failures include run, ticker, agent, operation, and error type without secrets.
- No executor imports another executor or a concrete provider.

## Testing strategy

Unit-test calculations and schema validation. Test each executor with a fake MCP client, then the real in-memory mock MCP client. Inject tool, calculation, and structured-output failures.
