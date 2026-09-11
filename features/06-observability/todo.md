# Observability tasks

## Contract

- [x] Draft logging, tracing, and metrics contracts.
- [ ] Approve in-process JSON metrics and deferred external monitoring stack.

## Implementation

- [ ] Add structured logging configuration and context propagation.
- [ ] Add safe timing and boundary-event helpers.
- [ ] Add bounded in-memory counters and duration aggregates.
- [ ] Instrument request, graph, executor, MCP, synthesis, and persistence boundaries.
- [ ] Propagate exact run metadata to LangSmith.
- [ ] Remove print statements and latest-run lookup after coverage exists.

## Verification

- [ ] Test success, failure, partial-result, and tracing-disabled events.
- [ ] Verify all required correlation fields and metric deltas.
- [ ] Verify secret redaction and valid JSON log output.
- [ ] Record evidence in `reports/06-observability-progress.md`.
