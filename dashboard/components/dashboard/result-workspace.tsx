"use client";

import { ArrowSquareOut, CheckCircle, CopySimple, DownloadSimple, WarningCircle } from "@phosphor-icons/react";
import { useState } from "react";
import { ComparisonTable } from "@/components/dashboard/comparison-table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { domains, type AnalysisDomain, type AnalysisReport, type EvidenceItem, type RunState } from "@/lib/contracts";
import { directionLabel, formatDate, formatDuration, formatMetric, statusLabel, titleCase } from "@/lib/format";

interface ResultWorkspaceProps {
  result: RunState;
}

function uniqueEvidence(report: AnalysisReport, outcomes: RunState["domain_outcomes"]): EvidenceItem[] {
  const byId = new Map<string, EvidenceItem>();
  [...report.evidence, ...outcomes.flatMap((outcome) => outcome.evidence)].forEach((item) => byId.set(item.evidence_id, item));
  return [...byId.values()];
}

function OverviewPanel({ report, result }: { report: AnalysisReport; result: RunState }) {
  return (
    <section className="result-section" aria-labelledby="overview-heading">
      <div className="section-heading">
        <div>
          <p className="section-kicker">02 / Executive readout</p>
          <h2 id="overview-heading">Research brief</h2>
        </div>
        <span className="telemetry">{report.request.tickers.join(" / ")} / {report.request.timeframe}</span>
      </div>
      <div className="overview-grid">
        <section className="overview-grid__summary" aria-labelledby="summary-heading">
          <p className="eyebrow" id="summary-heading">Executive summary</p>
          <p className="section-copy">{report.executive_summary}</p>
        </section>
        <section className="overview-grid__stocks" aria-labelledby="stocks-heading">
          <p className="eyebrow" id="stocks-heading">Company readouts</p>
          <ul className="stock-list">
            {report.stocks.map((stock) => (
              <li key={stock.ticker}>
                <h3><samp>{stock.ticker}</samp></h3>
                <p>{stock.summary}</p>
              </li>
            ))}
          </ul>
        </section>
        <section className="overview-grid__opportunities" aria-labelledby="opportunities-heading">
          <p className="eyebrow" id="opportunities-heading">Opportunities</p>
          <BulletList values={report.opportunities} type="opportunity" />
        </section>
        <section className="overview-grid__risks" aria-labelledby="risks-heading">
          <p className="eyebrow" id="risks-heading">Risks</p>
          <BulletList values={report.risks} type="risk" />
        </section>
        <section className="overview-grid__execution" aria-labelledby="execution-heading">
          <p className="eyebrow" id="execution-heading">Execution details</p>
          <dl className="metadata-grid">
            <div><dt>Requested tasks</dt><dd><data value={String(report.execution.requested_tasks)}>{report.execution.requested_tasks}</data></dd></div>
            <div><dt>Succeeded tasks</dt><dd><data value={String(report.execution.succeeded_tasks)}>{report.execution.succeeded_tasks}</data></dd></div>
            <div><dt>Failed tasks</dt><dd><data value={String(report.execution.failed_tasks)}>{report.execution.failed_tasks}</data></dd></div>
            <div><dt>Elapsed</dt><dd><data value={String(report.execution.duration_ms)}>{formatDuration(report.execution.duration_ms)}</data></dd></div>
            <div><dt>Started</dt><dd>{formatDate(report.execution.started_at)}</dd></div>
            <div><dt>Model</dt><dd><samp>{report.execution.model}</samp></dd></div>
            <div><dt>Generated</dt><dd>{formatDate(report.generated_at)}</dd></div>
            <div><dt>Run status</dt><dd>{statusLabel(result.status)}</dd></div>
          </dl>
        </section>
      </div>
      <p className="telemetry" style={{ marginTop: "1rem" }}>{report.disclaimer}</p>
    </section>
  );
}

function BulletList({ values, type }: { values: string[]; type: "opportunity" | "risk" }) {
  if (!values.length) return <p className="section-copy">No {type === "risk" ? "risks" : "opportunities"} were returned.</p>;
  return <ul className={type === "risk" ? "bullet-list bullet-list--risk" : "bullet-list"}>{values.map((value) => <li key={value}>{value}</li>)}</ul>;
}

function DomainPanel({ domain, result }: { domain: AnalysisDomain; result: RunState }) {
  const outcomes = result.domain_outcomes.filter((outcome) => outcome.domain === domain);
  return (
    <section className="result-section" aria-labelledby={`${domain}-heading`}>
      <div className="section-heading">
        <div>
          <p className="section-kicker">Domain analysis</p>
          <h2 id={`${domain}-heading`}>{titleCase(domain)}</h2>
        </div>
        <span className="telemetry">{outcomes.length} outcome{outcomes.length === 1 ? "" : "s"}</span>
      </div>
      {!outcomes.length ? <p className="section-copy">No {domain} outcome was returned for this run.</p> : null}
      {outcomes.map((outcome) => (
        <article className="domain-outcome" key={`${outcome.ticker}-${outcome.domain}`}>
          <div className="domain-outcome__header">
            <h3><samp>{outcome.ticker}</samp> / {titleCase(outcome.domain)}</h3>
            <span className="telemetry">{formatDuration(outcome.duration_ms)}</span>
          </div>
          {outcome.status === "failed" ? (
            <div className="unavailable" role="status">
              <WarningCircle aria-hidden="true" size={20} />
              <p><strong>Unavailable:</strong> {outcome.error?.message ?? "This analysis domain did not complete."}</p>
              <p className="telemetry">CODE / {outcome.error?.code ?? "unknown"}{outcome.error?.retryable ? " / RETRYABLE" : ""}</p>
            </div>
          ) : (
            <>
              <p className="domain-outcome__summary">{outcome.summary}</p>
              {outcome.signals.length ? (
                <ul className="signal-list" aria-label={`${outcome.ticker} ${domain} signals`}>
                  {outcome.signals.map((signal) => (
                    <li key={signal.name}>
                      <strong>{signal.name}</strong>
                      <data className="signal-value" data-direction={signal.direction} value={String(signal.value ?? "")}>{formatMetric(signal.value, signal.unit)} / {directionLabel(signal.direction)}</data>
                      <span>{signal.rationale}</span>
                    </li>
                  ))}
                </ul>
              ) : <p className="section-copy">No labeled signals were returned.</p>}
              <div className="overview-grid" style={{ marginTop: "1rem" }}>
                <section className="overview-grid__opportunities"><p className="eyebrow">Domain opportunities</p><BulletList values={outcome.opportunities} type="opportunity" /></section>
                <section className="overview-grid__risks"><p className="eyebrow">Domain risks</p><BulletList values={outcome.risks} type="risk" /></section>
              </div>
            </>
          )}
        </article>
      ))}
    </section>
  );
}

function EvidencePanel({ report, result }: { report: AnalysisReport; result: RunState }) {
  const evidence = uniqueEvidence(report, result.domain_outcomes);
  return (
    <section className="result-section" aria-labelledby="evidence-heading">
      <div className="section-heading">
        <div><p className="section-kicker">Source trail</p><h2 id="evidence-heading">Evidence</h2></div>
        <span className="telemetry">{evidence.length} item{evidence.length === 1 ? "" : "s"}</span>
      </div>
      {!evidence.length ? <p className="section-copy">No evidence items were returned for this run.</p> : null}
      <ul className="evidence-list">
        {evidence.map((item) => (
          <li key={item.evidence_id}>
            <div><p className="eyebrow">{item.source_type}</p><p>{formatDate(item.observed_at)}</p></div>
            <div><h3>{item.title}</h3><p>{item.source}</p></div>
            {item.reference ? <a className="evidence-link" href={item.reference} target="_blank" rel="noreferrer"><ArrowSquareOut aria-hidden="true" size={15} /> Open source</a> : <span className="telemetry">Reference unavailable</span>}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function RawJsonDisclosure({ result }: { result: RunState }) {
  const [copyState, setCopyState] = useState("Copy JSON");
  const json = JSON.stringify(result, null, 2);

  async function copyJson(): Promise<void> {
    try {
      await navigator.clipboard.writeText(json);
      setCopyState("Copied");
    } catch {
      setCopyState("Copy unavailable");
    }
  }

  function downloadJson(): void {
    const url = URL.createObjectURL(new Blob([json], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `analysis-${result.run_id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <details className="raw-json">
      <summary>Raw API JSON <span className="telemetry">Inspection only</span></summary>
      <div className="raw-json__body">
        <div className="raw-json__actions">
          <Button size="compact" onClick={() => void copyJson()}><CopySimple aria-hidden="true" size={16} /> {copyState}</Button>
          <Button size="compact" onClick={downloadJson}><DownloadSimple aria-hidden="true" size={16} /> Download JSON</Button>
        </div>
        <pre aria-label="Raw analysis JSON">{json}</pre>
      </div>
    </details>
  );
}

export function ResultWorkspace({ result }: ResultWorkspaceProps) {
  const report = result.report;
  if (!report) return null;
  const availableDomains = domains.filter((domain) => result.request.domains.includes(domain));

  return (
    <>
      {result.status === "partial" ? (
        <div className="partial-banner" role="status">
          <WarningCircle aria-hidden="true" size={20} />
          <p><strong>Partial result.</strong> Successful sections remain available. Review each unavailable domain before resubmitting.</p>
        </div>
      ) : null}
      <div className="result-topline">
        <div><p className="eyebrow">Run record</p><p className="run-id">RUN ID / <samp>{result.run_id}</samp></p></div>
        <span className="status-chip" data-status={result.status}><CheckCircle aria-hidden="true" size={15} /> {statusLabel(result.status)}</span>
      </div>
      <Tabs key={result.run_id} defaultValue="overview">
        <TabsList aria-label="Analysis views">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          {availableDomains.map((domain) => <TabsTrigger key={domain} value={domain}>{titleCase(domain)}</TabsTrigger>)}
          {report.comparison ? <TabsTrigger value="comparison">Comparison</TabsTrigger> : null}
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
        </TabsList>
        <TabsContent value="overview"><OverviewPanel report={report} result={result} /></TabsContent>
        {availableDomains.map((domain) => <TabsContent key={domain} value={domain}><DomainPanel domain={domain} result={result} /></TabsContent>)}
        {report.comparison ? (
          <TabsContent value="comparison">
            <section className="result-section" aria-labelledby="comparison-heading">
              <div className="section-heading"><div><p className="section-kicker">Cross-stock view</p><h2 id="comparison-heading">Comparison</h2></div><span className="telemetry">{report.request.tickers.length} tickers</span></div>
              <p className="comparison-summary">{report.comparison.summary}</p>
              <ComparisonTable metrics={report.comparison.metrics} tickers={report.request.tickers} />
            </section>
          </TabsContent>
        ) : null}
        <TabsContent value="evidence"><EvidencePanel report={report} result={result} /></TabsContent>
      </Tabs>
      <RawJsonDisclosure result={result} />
    </>
  );
}
