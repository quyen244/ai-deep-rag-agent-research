# FastAPI and persistence tasks

## Contract

- [x] Draft API, idempotency, and persistence contracts.
- [ ] Approve synchronous API execution for the bounded mock MVP.

## Implementation

- [ ] Add application service and dependency wiring.
- [ ] Implement atomic JSON result repository.
- [ ] Implement analysis, result, health, and metrics routes.
- [ ] Add structured exception handlers and safe API envelopes.
- [ ] Add explicit CORS configuration for the Next.js origin.
- [ ] Add idempotency-key handling without a database.

## Verification

- [ ] Run API contract and persistence tests with temporary directories.
- [ ] Verify OpenAPI schema and frontend-consumable JSON.
- [ ] Verify malformed request, unknown run, duplicate request, and write failure behavior.
- [ ] Record evidence in `reports/05-api-persistence-progress.md`.
