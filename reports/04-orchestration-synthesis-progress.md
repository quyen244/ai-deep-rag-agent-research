# Feature 04 orchestration and synthesis progress

Status: complete  
Date: 2026-09-13

## Outcome

Feature 04 now provides a deterministic, typed LangGraph workflow:

```text
normalize request -> plan unique tasks -> concurrent executor fan-out
-> collect append-only outcomes -> Validator bypass -> structured synthesis
```

`AnalysisOrchestrator.run()` accepts an `AnalysisRequest` and run UUID, then
returns a serializable `RunState`. The graph uses an `asyncio.gather` task
fan-out node, an allowed equivalent to Send-based fan-out, so every planned
`(run_id, ticker, domain)` invocation starts independently before collection.

## Implemented boundaries

- `src/orchestration/normalization.py` implements explicit-field precedence,
  text parsing for AAPL/TSLA/MSFT, domain parsing, de-duplication, and supported
  ticker validation.
- `src/orchestration/planner.py` creates one validated `TaskSpec` for every
  requested ticker/domain pair and rejects duplicate identities.
- `src/orchestration/contracts.py` defines serializable `GraphState` and an
  append-only outcome reducer that rejects a duplicate `(ticker, domain)`.
- `src/orchestration/graph.py` owns graph sequencing, concurrent dispatch,
  per-task containment for unexpected executor exceptions, total-failure
  behavior, and the explicit no-op Validator seam.
- `src/orchestration/synthesis.py` builds `AnalysisReport`, per-ticker sections,
  opportunities, risks, de-duplicated evidence, execution metadata, disclaimer,
  and structured comparison metrics. Failed or unavailable domains become
  `null` comparison cells rather than fabricated values.
- The structured-synthesis wrapper validates outputs and allows exactly one
  schema retry. A second invalid output produces a failed run with retained
  domain outcomes and no fabricated report.
- The old tutorial graph, state, node, message scraping, and import-time
  OpenRouter wrapper were replaced with lightweight Feature 04 compatibility
  exports.

## Verification evidence

Command:

```text
venv/bin/python -m pytest
```

Result:

```text
61 passed in 6.54s
```

Feature coverage includes text parsing and explicit-field precedence, default
eight-task planning for AAPL and TSLA, duplicate task/outcome rejection,
observable eight-way concurrency, Validator bypass behavior, two-ticker
comparison, partial and total executor failures, bounded synthesis retries,
synthesis failure artifacts, JSON round-tripping, and an end-to-end execution
through the actual in-memory Finance MCP client.

Additional checks passed:

```text
venv/bin/python -m compileall -q src tests
venv/bin/python -m pip check
git diff --check
```
