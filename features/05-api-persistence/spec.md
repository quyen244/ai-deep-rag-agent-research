# FastAPI application and JSON persistence

Status: approved
Owner: backend API and service packages
Depends on: 01-foundation, 04-orchestration-synthesis, 06-observability
Consumed by: 07-nextjs-dashboard, 08-verification-documentation

## Problem

The only entrypoint uses hardcoded input, there is no HTTP contract, and the existing JSON artifact is not produced by a reliable persistence service.

## Goal

Expose the analysis application through versioned FastAPI endpoints and persist terminal run artifacts atomically as JSON.

## Scope

Included: application service, dependency wiring, analysis/lookup/health/metrics routes, CORS for configured local frontend origins, API error mapping, idempotency, and file repository.

Non-goals: authentication, database, asynchronous job queue, WebSockets, SSE, deletion UI, and remote object storage.

## Current behavior

`src/app.py` creates a hardcoded request and returns an in-memory graph result. The imported `json` module is unused and no API or dashboard integration exists.

## Desired behavior

FastAPI validates requests, creates a run context, invokes the application service synchronously, persists a terminal artifact, and returns the same structured schema consumed by Next.js.

## Architecture impact

API routes remain thin. The application service owns the transaction boundary from accepted request through persistence. The file repository owns paths, atomic writes, reads, and serialization.

## Interfaces and contracts

- `POST /api/v1/analyses`
- `GET /api/v1/analyses/{run_id}`
- `GET /api/v1/health`
- `GET /api/v1/metrics`
- `ResultRepository.save(report)` and `ResultRepository.get(run_id)`
- Optional `Idempotency-Key` header; identical key returns the existing terminal result.

## Edge cases and recovery

| Case | Behavior | Recovery |
|---|---|---|
| Validation failure | RFC-style structured 422 response, no artifact | Correct fields |
| Unknown run ID | Structured 404 response | Verify ID or start analysis |
| Duplicate idempotency key | Return prior result without executing graph | Use new key for fresh run |
| Concurrent writes | Unique run paths plus atomic rename | No user action |
| Persistence failure | Return safe 500 error and emit failure metric | Correct filesystem configuration |
| Frontend origin not allowed | Reject through configured CORS policy | Configure explicit local origin |

## Acceptance criteria

- API and stored JSON use the same report schema.
- Successful, partial, and failed terminal runs can be loaded by `run_id` when persistence succeeds.
- Writes never expose partially written JSON files.
- Malformed requests and unknown tickers return useful field/context errors.
- CORS allows only configured origins.
- OpenAPI documents public request and response schemas.
- No API response includes secrets or raw internal tracebacks.

## Testing strategy

Use FastAPI's test client with temporary output directories and fake application services. Cover validation, success, partial result, graph failure, persistence failure, retrieval, CORS, idempotency, and OpenAPI schema.
