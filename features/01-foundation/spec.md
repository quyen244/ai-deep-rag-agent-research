# Foundation and typed contracts

Status: approved
Owner: backend application
Depends on: none
Consumed by: all backend features and the generated frontend API types

## Problem

Configuration is an import-time class with OpenRouter defaults, workflow state is loosely typed, and errors have no stable contract.

## Goal

Create a small validated foundation for configuration, requests, graph state, results, errors, and dependency wiring.

## Scope

Included: Pydantic settings and schemas, OpenAI model factory, exception taxonomy, package metadata, dependency pinning, output-path configuration, and shared clocks/ID helpers.

Non-goals: orchestration logic, MCP implementations, dashboard code, authentication, and Validator behavior.

## Current behavior

`src/config.py` reads misspelled OpenRouter variables and prints during import. `AgentState` mixes messages, results, validation placeholders, and a Markdown report without runtime validation.

## Desired behavior

Startup validates required settings without exposing values. The default model is `gpt-5.6-luna`. Every cross-layer object is serializable and validated. Exceptions carry safe context including `run_id`, ticker, agent, tool, and operation where applicable.

## Architecture impact

This feature becomes the dependency root. Higher layers may depend on its contracts; it must not import agents, graph, MCP, API, or persistence modules.

## Interfaces and contracts

- `Settings`: `openai_api_key`, `openai_model`, LangSmith fields, output directory, log level, MCP transport.
- `AnalysisRequest`, `NormalizedRequest`, `RunState`, `DomainOutcome`, `EvidenceItem`, `AnalysisReport`, `ErrorDetail`.
- `ConfigurationError`, `MCPToolError`, `AgentExecutionError`, `OrchestratorError`, `SynthesisError`, `PersistenceError`.
- `ModelFactory.create()` returns a LangChain-compatible OpenAI chat model.

## Edge cases and recovery

| Case | Behavior | Recovery |
|---|---|---|
| Missing API key during live pipeline startup | Raise `ConfigurationError`; health reports not-ready | Add key and restart |
| Invalid output directory | Fail startup with safe path context | Correct configured path |
| Unknown enum value | Return a field-level validation error | Correct request |
| Exception contains secret-like values | Redact before log or API serialization | Inspect internal chained exception locally |

## Acceptance criteria

- Importing configuration has no console side effects.
- A missing `OPENAI_API_KEY` produces a typed error without revealing secrets.
- Every public schema round-trips through JSON.
- The model factory uses the OpenAI endpoint and configured Luna model, not OpenRouter.
- All exception categories serialize to the same safe error envelope.
- The project declares supported Python and pinned direct dependencies, including FastMCP.

## Testing strategy

Unit-test settings precedence, missing/invalid configuration, schema validation, JSON round-trips, error redaction, and model-factory arguments without making a live API request.
