# Feature 06 — Observability progress

Status: complete

## Delivered

- `src.observability` provides scoped `run_id`/`request_id` context, secret-safe JSON logging, bounded in-memory metrics, and provider-neutral event adapters.
- The FastAPI composition root injects one telemetry instance into the analysis service, LangGraph orchestrator, MCP client, executor runner, and JSON repository.
- Events include timestamp, level, event, run ID, request ID, agent, ticker, tool, operation, status, duration, and safe error category where applicable.
- `/api/v1/metrics` retains the Feature 05 counters and now adds bounded request, pipeline, agent, tool, synthesis, persistence, failure, and duration summaries.
- LangChain structured interpretation receives `RunnableConfig.metadata` and tags containing the exact active run and request IDs. It makes no direct LangSmith lookup or export request, so disabled or unavailable tracing cannot break mock analysis.

## Evidence

```text
venv/bin/python -m pytest tests/unit/test_observability.py tests/integration/test_observability_pipeline.py tests/unit/test_api_persistence.py
10 passed, 1 warning in 2.24s

venv/bin/python -m pytest
72 passed, 1 warning in 4.54s

venv/bin/python -m compileall -q src tests

venv/bin/python -m pip check
No broken requirements found.
```

The tests capture valid JSON events across successful, partial, and failed API-to-MCP runs; assert a single run ID at every meaningful boundary; verify bounded metric deltas and duration counts; verify secret redaction; exercise missing-context diagnostics; and verify exact LangChain trace metadata with tracing disabled.
