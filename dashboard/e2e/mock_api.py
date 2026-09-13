"""Small FastAPI contract fixture for the dashboard browser test."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/analyses")
def create_analysis() -> dict[str, object]:
    run_id = "0f10c29e-6786-4af0-a844-333333333333"
    request = {
        "request_text": "Analyze AAPL and TSLA",
        "tickers": ["AAPL", "TSLA"],
        "domains": ["technical", "fundamental", "sentiment", "macro"],
        "timeframe": "1y",
        "focus_areas": [],
        "idempotency_key": None,
    }
    return {
        "run_id": run_id,
        "status": "succeeded",
        "request": request,
        "domain_outcomes": [
            {
                "ticker": "AAPL",
                "domain": "technical",
                "status": "succeeded",
                "summary": "Momentum is constructive in the observed range.",
                "signals": [{"name": "RSI", "direction": "neutral", "value": 55.2, "unit": "index", "rationale": "The observed value is not at an extreme."}],
                "opportunities": ["Constructive momentum"],
                "risks": ["Momentum can reverse"],
                "evidence": [],
                "data": {},
                "duration_ms": 80,
                "error": None,
            }
        ],
        "report": {
            "run_id": run_id,
            "status": "succeeded",
            "request": request,
            "executive_summary": "AAPL shows stronger profitability while TSLA remains more valuation sensitive.",
            "stocks": [
                {"ticker": "AAPL", "summary": "Cash generation remains a key strength.", "domains": {}, "opportunities": [], "risks": []},
                {"ticker": "TSLA", "summary": "Pricing pressure remains a material risk.", "domains": {}, "opportunities": [], "risks": []},
            ],
            "opportunities": ["AAPL services growth"],
            "risks": ["TSLA pricing pressure"],
            "comparison": {
                "summary": "AAPL has the lower observed price-to-earnings ratio.",
                "metrics": [{"label": "Price to earnings", "unit": "ratio", "preferred_ticker": "AAPL", "values": {"AAPL": 31.8, "TSLA": 68.4}}],
            },
            "evidence": [],
            "execution": {"requested_tasks": 8, "succeeded_tasks": 8, "failed_tasks": 0, "started_at": "2026-09-13T12:00:00Z", "completed_at": "2026-09-13T12:00:00Z", "duration_ms": 316, "model": "deterministic-test"},
            "generated_at": "2026-09-13T12:00:00Z",
            "disclaimer": "Mock data for interface verification only. Not investment advice.",
        },
        "errors": [],
        "created_at": "2026-09-13T12:00:00Z",
        "started_at": "2026-09-13T12:00:00Z",
        "completed_at": "2026-09-13T12:00:00Z",
    }
