# Multi-Agent Financial Analysis

A local, typed equity-research MVP. The dashboard sends one bounded analysis request to FastAPI. FastAPI runs a deterministic LangGraph workflow, fans out domain executors through a FastMCP client, synthesizes a structured report, persists an immutable JSON result, and returns that same contract to the dashboard.

The default system is deterministic and offline-friendly. It supports mock-data analysis for `AAPL`, `TSLA`, and `MSFT`; it is not investment advice and does not validate live-market data.

## What is included

- FastAPI API with typed request, result, error, health, and metrics contracts.
- Four concurrent analysis domains: technical, fundamental, sentiment, and macro.
- FastMCP client/server boundary backed by deterministic local provider fixtures.
- Atomic per-run JSON persistence, structured JSON logs, and in-process metrics.
- Next.js dashboard with request composition, evidence, comparison, raw JSON, responsive layouts, and Carbon/light themes.
- Deterministic backend, frontend, browser, and evidence-capture tests with no required API keys.

## Requirements

- Python 3.11 through 3.14.
- Node.js 20 or later and npm.
- Chromium for the browser test: `npx playwright install chromium` from `dashboard/`.

## Setup

Create and install the Python environment from the repository root:

```bash
python -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -e ".[dev]"
cp .env.example .env
```

On Windows, replace `venv/bin/python` with `venv\Scripts\python.exe`.

Install the dashboard dependencies:

```bash
cd dashboard
npm ci
cp .env.example .env.local
npx playwright install chromium
cd ..
```

The checked-in environment examples contain no secrets. The deterministic workflow needs no API key. `OPENAI_API_KEY` and LangSmith variables are optional configuration seams, not requirements for the verified MVP path.

## Run locally

Terminal 1 starts the API and stores new run artifacts under the ignored `outputs/` directory:

```bash
venv/bin/python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 starts the dashboard:

```bash
cd dashboard
npm run dev
```

Open `http://localhost:3000`, enter `Analyze AAPL and TSLA`, and select **Analyze**. The dashboard's default API URL is `http://localhost:8000`; set `NEXT_PUBLIC_API_BASE_URL` in `dashboard/.env.local` only when using another API origin.

## API

```bash
curl -X POST http://localhost:8000/api/v1/analyses \
  -H 'content-type: application/json' \
  -d '{"request_text":"Analyze AAPL and TSLA"}'
```

The returned `run_id` can be retrieved from `GET /api/v1/analyses/{run_id}`. Additional local endpoints are `GET /api/v1/health`, `GET /api/v1/metrics`, and `GET /openapi.json`.

## Verification and evidence

Run backend tests:

```bash
venv/bin/python -m pytest
venv/bin/python -m pip check
venv/bin/python -m compileall -q src tests scripts
```

Run frontend checks from `dashboard/`:

```bash
npm run typecheck
npm run lint
npm run test
npm run test:e2e
npm run build
```

`npm run test:e2e` starts the actual deterministic FastAPI application and Next.js dashboard. It verifies the browser path through FastAPI, LangGraph, executors, FastMCP, synthesis, and JSON persistence.

Generate inspectable evidence for the same representative API path:

```bash
venv/bin/python -m scripts.capture_verification_evidence --output-dir artifacts/feature-08
```

This writes a persisted `{run_id}.json`, `logs.jsonl`, `metrics.json`, `openapi.json`, and `summary.json`. Browser captures live in `artifacts/feature-08/`; the Feature 07 visual-review captures remain in `artifacts/feature-07/`.

## Architecture and operating boundaries

The full contract is documented in [features/ARCHITECTURE.md](features/ARCHITECTURE.md). The important local boundary is:

```text
Next.js dashboard -> FastAPI -> analysis service -> LangGraph executors
  -> FastMCP client -> deterministic mock provider -> synthesizer -> JSON repository
```

The dashboard calls only FastAPI. FastMCP remains an in-process protocol boundary for this MVP, but its client transport can later move to stdio or HTTP without changing executors.

## Explicit limitations and deferrals

- Validator behavior is an explicit no-op bypass seam.
- Financial, news, and macro inputs are deterministic fixtures, not live providers.
- There is no database, background queue, authentication, authorization, or production deployment configuration.
- There is no alpha generation, LLM-as-a-judge evaluation, load test, penetration test, or real-market accuracy validation.
- Prometheus, Grafana, OpenTelemetry exporters, and a LangSmith export workflow are not implemented.
- No live-provider or live-model smoke command is claimed. Configure optional credentials only when a separately approved adapter is added.

See [reports/08-verification-documentation-progress.md](reports/08-verification-documentation-progress.md) for the evidence matrix and final status.
