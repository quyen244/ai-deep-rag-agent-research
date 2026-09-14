# Logging, tracing, and metrics

Status: approved
Owner: backend observability package
Depends on: 01-foundation
Consumed by: 02-mcp-data-layer, 03-executor-agents, 04-orchestration-synthesis, 05-api-persistence

## Problem

The repository uses print statements, does not propagate a stable run ID, and queries the latest LangSmith run instead of correlating the actual execution. No application metrics exist.

## Goal

Make failures and latency attributable to a request, ticker, agent, tool, and operation with minimal local infrastructure.

## Scope

Included: structured JSON logging, context propagation, duration helpers, in-process metric registry, JSON metrics endpoint data, and LangSmith trace metadata.

Non-goals: Prometheus/Grafana deployment, OpenTelemetry collector, distributed tracing backend, alerting, and LLM-as-a-judge.

## Current behavior

Tools and graph construction print human-readable lines. One broad exception catches LangSmith lookup failure. There are no counters or duration measurements.

## Desired behavior

One run ID is created at request acceptance and appears in every meaningful boundary event. Metrics count requests, agents, tools, failures, and durations. LangSmith receives the same run metadata.

## Architecture impact

Observability is infrastructure injected into services, not a separate microservice. Business code records named boundary events through small interfaces and does not depend on a specific logging backend.

## Interfaces and contracts

- `RunContext(run_id, request_id, trace_metadata)` propagated explicitly or through a scoped context variable.
- Log event fields: timestamp, level, event, run ID, agent, ticker, tool, operation, status, duration milliseconds, and error type.
- Metric names match the product brief and use bounded label values only.
- `/api/v1/metrics` returns a documented JSON snapshot.

## Edge cases and recovery

| Case | Behavior | Recovery |
|---|---|---|
| LangSmith disabled | Pipeline runs with local logs and metrics | Enable environment settings if desired |
| LangSmith unavailable | Do not fail analysis; log one trace-export warning | Retry on later request |
| Missing run context in boundary event | Generate programming-error event in tests | Fix caller propagation |
| Exception has sensitive content | Redact and retain safe error category | Inspect local cause securely |
| Process restart | In-memory metrics reset by design | Use logs for historical inspection |

## Acceptance criteria

- Every request, agent execution, MCP call, synthesis, and pipeline completion event includes the same `run_id`.
- Required counters and duration summaries update on success and failure.
- Logs are valid JSON and contain no secrets.
- LangSmith metadata references the exact run rather than a latest-run query.
- Disabling or losing LangSmith does not break deterministic mock analysis.
- No Prometheus, Grafana, or OpenTelemetry service is introduced.

## Testing strategy

Capture logs and metric snapshots around successful, partial, and failed runs. Assert correlation fields, counter deltas, durations, redaction, and graceful tracing degradation.
