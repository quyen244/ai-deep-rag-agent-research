# Feature 08 - Verification and documentation progress

Status: complete

## Before and after

Before this feature, the repository README described a retired tutorial layout, the top-level `analysis_result.json` was a stale legacy artifact with null result fields, and the dashboard browser test used a mock API rather than the implemented backend.

The repository now has one deterministic evidence command, an actual-backend browser path, a verified README and environment template, complete feature progress reports, reviewed screenshots, and this Definition of Done matrix.

## Representative evidence

`venv/bin/python -m scripts.capture_verification_evidence --output-dir artifacts/feature-08` produced one successful `Analyze AAPL and TSLA` run:

| Evidence | Result |
| --- | --- |
| [Persisted run](../artifacts/feature-08/434c96ce-09e3-4fa6-a511-2160fbaad2e6.json) | `succeeded`; 8 requested tasks; AAPL/TSLA comparison present |
| [Structured logs](../artifacts/feature-08/logs.jsonl) | 29 events with the same `run_id` and request ID across API, graph, MCP, executors, synthesis, and persistence |
| [Metrics](../artifacts/feature-08/metrics.json) | 1 submission and 1 success; 2 executor completions per domain; 2 calls for each per-ticker tool and 4 sector-data calls; 1 synthesis and 1 persistence save |
| [OpenAPI](../artifacts/feature-08/openapi.json) | analysis create/read, health, and metrics paths |
| [Summary](../artifacts/feature-08/summary.json) | captured run ID and evidence counts |

## Browser evidence

| Evidence | Result |
| --- | --- |
| [Desktop dashboard](../artifacts/feature-08/dashboard-desktop.png) | Real local AAPL/TSLA browser run with the execution status and executive brief above the fold |
| [Mobile dashboard](../artifacts/feature-08/dashboard-mobile.png) | Same real run at a 390px viewport; readable report hierarchy and horizontal tab access |

The Feature 07 visual hierarchy before/after captures remain under `artifacts/feature-07/`.

## Definition of Done

| Item | Evidence |
| --- | --- |
| MCP to executor to orchestrator to synthesizer to JSON boundary | `tests/integration/test_verification_evidence.py` and representative run artifact |
| Malformed request, unknown ticker, MCP, executor, synthesis, persistence, and serialization failure handling | API, executor, orchestration, MCP, and persistence test modules documented in the feature reports |
| Dashboard AAPL/TSLA request against FastAPI | `dashboard/e2e/dashboard.spec.ts` runs the real `src.api.app:app` server |
| Correlated logs, metrics, JSON, and screenshots | Feature 08 artifacts and Playwright captures |
| Verified setup, test, run, and architecture guidance | `README.md`, `.env.example`, and `features/ARCHITECTURE.md` |
| Every implemented feature reports evidence | `reports/01` through `reports/08` |
| Deferrals explicitly named | README limitations and the architecture contract |

## Verification commands

```text
venv/bin/python -m pytest
73 passed, 1 warning in 5.03s

venv/bin/python -m pip check
No broken requirements found.

venv/bin/python -m compileall -q src tests scripts
passed

dashboard: node node_modules/typescript/bin/tsc --noEmit
passed

dashboard: node node_modules/eslint/bin/eslint.js .
passed

dashboard: node node_modules/vitest/vitest.mjs run
3 test files passed, 9 tests passed

dashboard: npm run test:e2e
2 passed; actual FastAPI backend

dashboard: node node_modules/next/dist/bin/next build
passed
```

The automated paths use only deterministic local fixtures and do not require a live API key or network provider. The browser capture also reported zero console errors.

## Explicit limitations

The Validator is a no-op bypass; providers are deterministic fixtures; JSON files replace a database; there is no queue, authentication, production deployment, real-market validation, alpha generation, LLM-as-a-judge evaluation, or exporter stack. Optional OpenAI and LangSmith settings are configuration seams only; no live smoke test is claimed without a separately approved adapter.
