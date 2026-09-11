# End-to-end verification and documentation

Status: approved
Owner: repository quality and documentation
Depends on: 01-foundation, 02-mcp-data-layer, 03-executor-agents, 04-orchestration-synthesis, 05-api-persistence, 06-observability, 07-nextjs-dashboard
Consumed by: maintainers and users

## Problem

There is no deterministic test suite, setup guide, verified progress reporting, or reproducible evidence that the architecture works end to end.

## Goal

Prove the complete dashboard-to-provider path, document local operation, and report limitations without overstating unverified behavior.

## Scope

Included: Python and frontend test commands, representative AAPL/TSLA run, JSON evidence, structured log and metric evidence, browser screenshots, README, architecture update, progress reports, and final report.

Non-goals: load testing, penetration testing, real-market validation, financial model validation against live sources, and production deployment.

## Current behavior

The only test-like files execute external calls at import time. The README is stale and the existing JSON artifact has null result fields.

## Desired behavior

One documented command set installs, configures, tests, and runs both processes. CI-friendly tests use no network. A browser-driven scenario verifies the actual API, graph, executors, MCP, providers, synthesis, persistence, and dashboard.

## Architecture impact

Verification crosses every boundary but owns no business behavior. Test fixtures and fakes live outside production modules. Progress reports link claims to commands, artifacts, logs, metrics, or screenshots.

## Evidence contract

- Python unit and integration test summary.
- Frontend unit/component test summary.
- API OpenAPI and contract evidence.
- Sample `run_id.json` for `Analyze AAPL and TSLA`.
- Structured logs showing one correlated run.
- Metrics snapshot showing expected counter deltas.
- Desktop and mobile dashboard screenshots.
- Final status table mapping Definition of Done items to evidence.

## Edge cases and recovery

| Case | Behavior | Recovery |
|---|---|---|
| Live API key unavailable in CI | Use deterministic fake model for automated tests | Run optional live smoke test locally |
| Browser tooling unavailable | Record limitation and verify components plus API contract | Capture screenshots when tooling is available |
| Flaky timing assertion | Assert concurrency/order-independent outcomes, not exact milliseconds | Fix deterministic test boundary |
| Documentation command fails | Do not mark documentation acceptance complete | Correct and rerun from clean environment |

## Acceptance criteria

- The required MCP to executor to orchestrator to synthesizer to JSON boundary test passes.
- Malformed request, unknown ticker, MCP failure, executor failure, synthesis failure, persistence failure, and JSON serialization tests pass.
- The Next.js dashboard completes an AAPL/TSLA request against FastAPI.
- Logs, metrics, JSON output, and screenshots are captured as concrete evidence.
- README setup succeeds from declared dependencies and environment example.
- Every implemented feature has an evidence-backed progress report.
- Validator, real providers, database, and alpha generation are explicitly documented as deferred.

## Testing strategy

Run the repository's complete backend and frontend test suites, then start both local processes and drive the representative request through a browser. Verify persisted artifacts and observability output for the same run ID.
