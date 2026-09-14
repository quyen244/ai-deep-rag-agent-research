# FastAPI and persistence tasks

## Contract

- [x] Draft API, idempotency, and persistence contracts.
- [x] Approve synchronous API execution for the bounded mock MVP.

## Implementation

- [x] Add application service and dependency wiring.
- [x] Implement atomic JSON result repository.
- [x] Implement analysis, result, health, and metrics routes.
- [x] Add structured exception handlers and safe API envelopes.
- [x] Add explicit CORS configuration for the Next.js origin.
- [x] Add idempotency-key handling without a database.

## Verification

- [x] Run API contract and persistence tests with temporary directories.
- [x] Verify OpenAPI schema and frontend-consumable JSON.
- [x] Verify malformed request, unknown run, duplicate request, and write failure behavior.
- [x] Record evidence in `reports/05-api-persistence-progress.md`.
