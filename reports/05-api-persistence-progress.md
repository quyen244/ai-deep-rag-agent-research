# Feature 05 — API and persistence progress

Status: complete

## Delivered

- `src.api.app:app` exposes the versioned analysis, lookup, health, and metrics endpoints.
- `AnalysisService` owns request normalization, run creation, idempotency, terminal failure conversion, and the persistence transaction boundary.
- `FileResultRepository` stores immutable `RunState` artifacts as `{run_id}.json`, using a flushed temporary file followed by `os.replace`.
- The API response and stored artifact are the identical serialized `RunState` schema; this preserves successful, partial, and failed terminal runs.
- Errors use a safe `{ "error": { ... } }` envelope. Validation returns 422, unknown runs 404, and persistence failures 500 without raw tracebacks.
- CORS accepts only configured explicit origins, defaulting to `http://localhost:3000`.

## Evidence

```text
venv/bin/python -m pytest tests/unit/test_api_persistence.py tests/integration/test_api_mcp.py
6 passed, 1 warning in 2.14s

venv/bin/python -m pytest
67 passed, 1 warning in 5.92s

venv/bin/python -m compileall -q src/api src/persistence src/services tests/unit/test_api_persistence.py tests/integration/test_api_mcp.py

venv/bin/python -m pip check
No broken requirements found.
```

The API tests verify validation, unknown tickers, partial and failed terminal runs, retrieval, idempotency, atomic artifact shape, persistence failure safety, CORS, metrics, and OpenAPI. The integration test exercises the actual FastAPI-to-orchestrator-to-in-memory-MCP path.

## Runtime entry point

```text
uvicorn src.api.app:app --reload
```

Use `RESULT_OUTPUT_DIR` to select artifact storage and `CORS_ALLOWED_ORIGINS` as a JSON array of explicit browser origins.
