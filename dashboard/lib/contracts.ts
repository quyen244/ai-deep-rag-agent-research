export const domains = ["technical", "fundamental", "sentiment", "macro"] as const;
export type AnalysisDomain = (typeof domains)[number];

export const timeframes = ["1m", "3m", "6m", "1y", "5y"] as const;
export type Timeframe = (typeof timeframes)[number];

export type RunStatus = "queued" | "running" | "succeeded" | "partial" | "failed";
export type OutcomeStatus = "succeeded" | "failed";
export type SignalDirection = "positive" | "negative" | "neutral";
export type SourceType = "mock" | "model";

export interface AnalysisRequest {
  request_text?: string;
  tickers?: string[];
  domains?: AnalysisDomain[];
  timeframe?: Timeframe;
  focus_areas?: string[];
  idempotency_key?: string;
}

export interface NormalizedRequest {
  request_text: string | null;
  tickers: string[];
  domains: AnalysisDomain[];
  timeframe: Timeframe;
  focus_areas: string[];
  idempotency_key: string | null;
}

export interface ErrorDetail {
  code: string;
  message: string;
  retryable: boolean;
  context: Record<string, unknown>;
}

export interface EvidenceItem {
  evidence_id: string;
  title: string;
  source: string;
  source_type: SourceType;
  observed_at: string;
  reference: string | null;
  details: Record<string, unknown>;
}

export interface Signal {
  name: string;
  direction: SignalDirection;
  value: string | number | boolean | null;
  unit: string | null;
  rationale: string;
}

export interface DomainOutcome {
  ticker: string;
  domain: AnalysisDomain;
  status: OutcomeStatus;
  summary: string;
  signals: Signal[];
  opportunities: string[];
  risks: string[];
  evidence: EvidenceItem[];
  data: Record<string, unknown>;
  duration_ms: number;
  error: ErrorDetail | null;
}

export interface StockAnalysis {
  ticker: string;
  summary: string;
  domains: Partial<Record<AnalysisDomain, DomainOutcome>>;
  opportunities: string[];
  risks: string[];
}

export interface ComparisonMetric {
  label: string;
  values: Record<string, string | number | boolean | null>;
  unit: string | null;
  preferred_ticker: string | null;
}

export interface CrossStockComparison {
  summary: string;
  metrics: ComparisonMetric[];
}

export interface ExecutionMetadata {
  requested_tasks: number;
  succeeded_tasks: number;
  failed_tasks: number;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  model: string;
}

export interface AnalysisReport {
  run_id: string;
  status: RunStatus;
  request: NormalizedRequest;
  executive_summary: string;
  stocks: StockAnalysis[];
  opportunities: string[];
  risks: string[];
  comparison: CrossStockComparison | null;
  evidence: EvidenceItem[];
  execution: ExecutionMetadata;
  generated_at: string;
  disclaimer: string;
}

export interface RunState {
  run_id: string;
  status: RunStatus;
  request: NormalizedRequest;
  domain_outcomes: DomainOutcome[];
  report: AnalysisReport | null;
  errors: ErrorDetail[];
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface ApiFieldError {
  location: Array<string | number>;
  message: string;
  type: string;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    context: Record<string, unknown>;
    fields: ApiFieldError[];
  };
}
