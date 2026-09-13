"use client";

import { ArrowClockwise, CloudSlash, WarningCircle } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import { AnalysisComposer, type ComposerForm } from "@/components/dashboard/analysis-composer";
import { RawJsonDisclosure, ResultWorkspace } from "@/components/dashboard/result-workspace";
import { Button } from "@/components/ui/button";
import { ApiClientError, recoveryMessage, submitAnalysis } from "@/lib/api";
import { domains, type AnalysisDomain, type AnalysisRequest, type RunState } from "@/lib/contracts";

const initialForm: ComposerForm = {
  requestText: "",
  tickersText: "",
  domains: [...domains],
  timeframe: "1y",
  focusAreas: "",
};

function commaSeparated(value: string): string[] {
  return [...new Set(value.split(/[\s,]+/).map((item) => item.trim().toUpperCase()).filter(Boolean))];
}

function LoadingState({ elapsedSeconds }: { elapsedSeconds: number }) {
  return (
    <section className="state-panel" aria-labelledby="loading-title" aria-live="polite">
      <p className="section-kicker">Request in progress</p>
      <h2 id="loading-title">Analysis is running</h2>
      <p>The API request is still in progress. This workspace will update only after the complete response arrives.</p>
      <p className="telemetry">ELAPSED / {elapsedSeconds} S</p>
      <div className="skeleton-grid" aria-hidden="true"><div className="skeleton" /><div className="skeleton" /><div className="skeleton" /></div>
    </section>
  );
}

function EmptyState() {
  return (
    <section className="state-panel" aria-labelledby="empty-title">
      <p className="section-kicker">Awaiting input</p>
      <h2 id="empty-title">Start with a decision</h2>
      <p>Enter a research request, choose the relevant domains, and submit one bounded analysis run. Structured findings and source evidence will appear here.</p>
    </section>
  );
}

function ErrorState({ error, onRetry }: { error: ApiClientError; onRetry: () => void }) {
  return (
    <section className="state-panel" aria-labelledby="error-title" role="alert">
      <p className="section-kicker">Request unavailable</p>
      <h2 id="error-title">Analysis needs attention</h2>
      <p className="state-panel__error">{recoveryMessage(error)}</p>
      <p className="telemetry">ERROR CODE / {error.code}</p>
      <Button variant="primary" onClick={onRetry}><ArrowClockwise aria-hidden="true" size={17} /> Retry analysis</Button>
    </section>
  );
}

function FailedRunState({ result, onRetry }: { result: RunState; onRetry: () => void }) {
  const detail = result.errors[0];
  return (
    <section className="state-panel" aria-labelledby="failed-run-title" role="alert">
      <p className="section-kicker">Run did not complete</p>
      <h2 id="failed-run-title">Analysis needs attention</h2>
      <div className="failure-banner">
        <WarningCircle aria-hidden="true" size={20} />
        <p>{detail?.message ?? "The analysis service did not return a report for this run."}</p>
      </div>
      <p className="telemetry">RUN ID / {result.run_id}</p>
      <p className="telemetry">ERROR CODE / {detail?.code ?? "unknown"}</p>
      <Button variant="primary" onClick={onRetry}><ArrowClockwise aria-hidden="true" size={17} /> Retry analysis</Button>
    </section>
  );
}

export function DashboardClient() {
  const [form, setForm] = useState<ComposerForm>(initialForm);
  const [result, setResult] = useState<RunState | null>(null);
  const [error, setError] = useState<ApiClientError | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<"request" | "domains", string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [theme, setTheme] = useState<"carbon" | "light">("carbon");
  const requestInputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    document.querySelector<HTMLElement>(".app-shell")?.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    if (!isSubmitting) return;
    const startedAt = Date.now();
    setElapsedSeconds(0);
    const interval = window.setInterval(() => setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1_000)), 250);
    return () => window.clearInterval(interval);
  }, [isSubmitting]);

  function updateField(field: Exclude<keyof ComposerForm, "domains">, value: string): void {
    setForm((previous) => ({ ...previous, [field]: value }));
    setFieldErrors((previous) => ({ ...previous, request: undefined }));
    setError(null);
  }

  function updateDomains(nextDomains: AnalysisDomain[]): void {
    setForm((previous) => ({ ...previous, domains: nextDomains }));
    setFieldErrors((previous) => ({ ...previous, domains: undefined }));
  }

  async function runAnalysis(): Promise<void> {
    const requestText = form.requestText.trim();
    const tickers = commaSeparated(form.tickersText);
    const nextErrors: Partial<Record<"request" | "domains", string>> = {};
    if (!requestText && !tickers.length) nextErrors.request = "Enter a research request or at least one ticker.";
    if (!form.domains.length) nextErrors.domains = "Choose at least one analysis domain.";
    if (Object.keys(nextErrors).length) {
      setFieldErrors(nextErrors);
      if (nextErrors.request) requestInputRef.current?.focus();
      return;
    }

    const request: AnalysisRequest = {
      domains: form.domains,
      timeframe: form.timeframe,
      focus_areas: commaSeparated(form.focusAreas).map((value) => value.toLowerCase()),
    };
    if (requestText) request.request_text = requestText;
    if (tickers.length) request.tickers = tickers;

    setIsSubmitting(true);
    setResult(null);
    setError(null);
    setFieldErrors({});
    try {
      setResult(await submitAnalysis(request));
    } catch (caught) {
      const apiError = caught instanceof ApiClientError
        ? caught
        : new ApiClientError({ code: "server_error", message: "The analysis request could not be completed." });
      if (apiError.code === "request_validation_error") {
        setFieldErrors({ request: recoveryMessage(apiError) });
        requestInputRef.current?.focus();
      } else {
        setError(apiError);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  const showFailedRun = result?.status === "failed" || (result !== null && result.report === null);

  return (
    <>
      <AnalysisComposer
        form={form}
        errors={fieldErrors}
        isSubmitting={isSubmitting}
        elapsedSeconds={elapsedSeconds}
        theme={theme}
        requestInputRef={requestInputRef}
        onChange={updateField}
        onDomainsChange={updateDomains}
        onSubmit={() => void runAnalysis()}
        onThemeChange={setTheme}
      />
      {isSubmitting ? <LoadingState elapsedSeconds={elapsedSeconds} /> : null}
      {!isSubmitting && error ? <ErrorState error={error} onRetry={() => void runAnalysis()} /> : null}
      {!isSubmitting && showFailedRun && result ? <><FailedRunState result={result} onRetry={() => void runAnalysis()} /><RawJsonDisclosure result={result} /></> : null}
      {!isSubmitting && !error && !result ? <EmptyState /> : null}
      {!isSubmitting && result && !showFailedRun ? <ResultWorkspace result={result} /> : null}
      {error?.code === "offline" ? <p className="telemetry" style={{ padding: "0 1rem 1rem" }}><CloudSlash aria-hidden="true" size={14} /> BACKEND CONNECTION REQUIRED</p> : null}
    </>
  );
}
