# Feature 04 - Orchestration and synthesis progress

Status: complete

## Delivered

- Replaced supervisor-directed routing with a typed LangGraph workflow: normalize, plan, concurrently execute, collect, bypass the deferred validator, and synthesize.
- Planned tasks are the cartesian product of the normalized tickers and selected domains. Each domain executor is independently invocable through a narrow context contract.
- The deterministic synthesizer creates a serializable report, per-stock summaries, opportunities, risks, deduplicated evidence, and cross-stock comparisons without inventing missing values.
- Partial runs preserve successful outcomes and mark unavailable comparison cells. Total executor or synthesis failure produces a failed terminal run without a fabricated report.

## Evidence

```text
venv/bin/python -m pytest tests/unit/test_orchestration.py tests/integration/test_orchestration_mcp.py
passed
```

The tests cover request normalization, unsupported tickers, deterministic planning, concurrent fan-out, two-ticker reports, partial executor failure, total executor failure, bounded synthesis retry/failure, comparison null handling, and a real in-memory MCP run. The Feature 08 representative artifact independently confirms the eight-task AAPL/TSLA path through this graph.
