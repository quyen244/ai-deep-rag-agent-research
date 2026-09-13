# Orchestration and synthesis tasks

## Contract

- [x] Draft graph topology, lifecycle, and partial-failure rules.
- [x] Approve synchronous orchestration and Validator bypass seam.

## Implementation

- [x] Implement request normalizer and deterministic task planner.
- [x] Define graph state reducers for append-only task outcomes.
- [x] Implement concurrent executor fan-out and collection.
- [x] Add explicit no-op Validator seam with deferred-work documentation.
- [x] Implement structured synthesizer and comparison builder.
- [x] Replace message scraping and supervisor-controlled synthesis.
- [x] Remove obsolete tutorial graph after coverage exists.

## Verification

- [x] Verify one-ticker and multi-ticker successful flows.
- [x] Verify duplicate normalization, partial failure, total failure, and synthesis failure.
- [x] Verify JSON serialization without lossy string conversion.
- [x] Record evidence in `reports/04-orchestration-synthesis-progress.md`.
