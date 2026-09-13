# Orchestration and synthesis tasks

## Contract

- [x] Draft graph topology, lifecycle, and partial-failure rules.
- [ ] Approve synchronous orchestration and Validator bypass seam.

## Implementation

- [ ] Implement request normalizer and deterministic task planner.
- [ ] Define graph state reducers for append-only task outcomes.
- [ ] Implement concurrent executor fan-out and collection.
- [ ] Add explicit no-op Validator seam with deferred-work documentation.
- [ ] Implement structured synthesizer and comparison builder.
- [ ] Replace message scraping and supervisor-controlled synthesis.
- [ ] Remove obsolete tutorial graph after coverage exists.

## Verification

- [ ] Verify one-ticker and multi-ticker successful flows.
- [ ] Verify duplicate normalization, partial failure, total failure, and synthesis failure.
- [ ] Verify JSON serialization without lossy string conversion.
- [ ] Record evidence in `reports/04-orchestration-synthesis-progress.md`.
