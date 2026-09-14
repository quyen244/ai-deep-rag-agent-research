import type { RunState } from "@/lib/contracts";

export const successfulRun: RunState = {
  run_id: "0f10c29e-6786-4af0-a844-111111111111",
  status: "succeeded",
  request: {
    request_text: "Analyze AAPL and TSLA",
    tickers: ["AAPL", "TSLA"],
    domains: ["technical", "fundamental", "sentiment", "macro"],
    timeframe: "1y",
    focus_areas: [],
    idempotency_key: null,
  },
  domain_outcomes: [
    {
      ticker: "AAPL", domain: "technical", status: "succeeded", summary: "Momentum is constructive within the observed range.", duration_ms: 82,
      signals: [{ name: "RSI", direction: "neutral", value: 55.2, unit: "index", rationale: "The observed value is not at an extreme." }],
      opportunities: ["Constructive momentum"], risks: ["Momentum can reverse"], evidence: [{ evidence_id: "aapl-bars", title: "AAPL observed price bars", source: "Deterministic market fixture", source_type: "mock", observed_at: "2026-09-01T00:00:00Z", reference: null, details: {} }], data: {}, error: null,
    },
    {
      ticker: "TSLA", domain: "technical", status: "succeeded", summary: "Volatility remains elevated relative to the comparison set.", duration_ms: 76,
      signals: [{ name: "RSI", direction: "negative", value: 43.1, unit: "index", rationale: "The observed range shows weaker momentum." }],
      opportunities: ["Recovering price range"], risks: ["High observed volatility"], evidence: [], data: {}, error: null,
    },
  ],
  report: {
    run_id: "0f10c29e-6786-4af0-a844-111111111111",
    status: "succeeded",
    request: {
      request_text: "Analyze AAPL and TSLA", tickers: ["AAPL", "TSLA"], domains: ["technical", "fundamental", "sentiment", "macro"], timeframe: "1y", focus_areas: [], idempotency_key: null,
    },
    executive_summary: "AAPL has the stronger profitability profile while TSLA carries greater valuation and volatility sensitivity.",
    stocks: [
      { ticker: "AAPL", summary: "Cash generation and operating margin remain the primary strengths.", domains: {}, opportunities: ["Services growth"], risks: ["Valuation sensitivity"] },
      { ticker: "TSLA", summary: "Balance-sheet resilience is offset by competitive pricing pressure.", domains: {}, opportunities: ["Energy storage"], risks: ["Margin pressure"] },
    ],
    opportunities: ["AAPL services revenue", "TSLA energy storage"],
    risks: ["AAPL valuation sensitivity", "TSLA automotive pricing pressure"],
    comparison: {
      summary: "AAPL has the lower observed price-to-earnings ratio and the higher observed return on equity.",
      metrics: [
        { label: "Price to earnings", unit: "ratio", preferred_ticker: "AAPL", values: { AAPL: 31.8, TSLA: 68.4 } },
        { label: "Return on equity", unit: "percent", preferred_ticker: "AAPL", values: { AAPL: 142.3, TSLA: 9.5 } },
        { label: "Data availability", unit: null, preferred_ticker: null, values: { AAPL: true, TSLA: null } },
      ],
    },
    evidence: [{ evidence_id: "macro-us", title: "US macro conditions", source: "Deterministic macro fixture", source_type: "mock", observed_at: "2026-09-01T00:00:00Z", reference: "https://example.test/macro", details: {} }],
    execution: { requested_tasks: 8, succeeded_tasks: 8, failed_tasks: 0, started_at: "2026-09-13T12:00:00Z", completed_at: "2026-09-13T12:00:00Z", duration_ms: 316, model: "deterministic-test" },
    generated_at: "2026-09-13T12:00:00Z",
    disclaimer: "Deterministic fixture data for interface verification only. Not investment advice.",
  },
  errors: [],
  created_at: "2026-09-13T12:00:00Z",
  started_at: "2026-09-13T12:00:00Z",
  completed_at: "2026-09-13T12:00:00Z",
};

export const partialRun: RunState = {
  ...successfulRun,
  run_id: "0f10c29e-6786-4af0-a844-222222222222",
  status: "partial",
  report: successfulRun.report ? { ...successfulRun.report, run_id: "0f10c29e-6786-4af0-a844-222222222222", status: "partial", execution: { ...successfulRun.report.execution, requested_tasks: 8, succeeded_tasks: 7, failed_tasks: 1 } } : null,
  domain_outcomes: [
    ...successfulRun.domain_outcomes,
    { ticker: "TSLA", domain: "fundamental", status: "failed", summary: "", signals: [], opportunities: [], risks: [], evidence: [], data: {}, duration_ms: 31, error: { code: "provider_unavailable", message: "Fundamental data source was unavailable.", retryable: true, context: {} } },
  ],
};
