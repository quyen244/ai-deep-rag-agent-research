# Observability tasks

## Contract

- [x] Draft logging, tracing, and metrics contracts.
- [x] Approve in-process JSON metrics and deferred external monitoring stack.

## Implementation

- [x] Add structured logging configuration and context propagation.
- [x] Add safe timing and boundary-event helpers.
- [x] Add bounded in-memory counters and duration aggregates.
- [x] Instrument request, graph, executor, MCP, synthesis, and persistence boundaries.
- [x] Propagate exact run metadata to LangSmith.
- [x] Remove print statements and latest-run lookup after coverage exists.

## Verification

- [x] Test success, failure, partial-result, and tracing-disabled events.
- [x] Verify all required correlation fields and metric deltas.
- [x] Verify secret redaction and valid JSON log output.
- [x] Record evidence in `reports/06-observability-progress.md`.
