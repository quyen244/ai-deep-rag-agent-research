"use client";

import { SpinnerGap } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import { domains, type AnalysisDomain, type Timeframe } from "@/lib/contracts";
import { titleCase } from "@/lib/format";

export interface ComposerForm {
  requestText: string;
  tickersText: string;
  domains: AnalysisDomain[];
  timeframe: Timeframe;
  focusAreas: string;
}

interface AnalysisComposerProps {
  form: ComposerForm;
  errors: Partial<Record<"request" | "domains", string>>;
  isSubmitting: boolean;
  elapsedSeconds: number;
  theme: "carbon" | "light";
  requestInputRef: React.RefObject<HTMLTextAreaElement | null>;
  onChange: (field: Exclude<keyof ComposerForm, "domains">, value: string) => void;
  onDomainsChange: (domains: AnalysisDomain[]) => void;
  onSubmit: () => void;
  onThemeChange: (theme: "carbon" | "light") => void;
  isFollowUp?: boolean;
}

export function AnalysisComposer({
  form,
  errors,
  isSubmitting,
  elapsedSeconds,
  theme,
  requestInputRef,
  onChange,
  onDomainsChange,
  onSubmit,
  onThemeChange,
  isFollowUp = false,
}: AnalysisComposerProps) {
  function toggleDomain(domain: AnalysisDomain): void {
    onDomainsChange(form.domains.includes(domain) ? form.domains.filter((item) => item !== domain) : [...form.domains, domain]);
  }

  return (
    <section className="composer" aria-labelledby="composer-title">
      <div className="composer__header">
        <div>
          <p className="section-kicker">{isFollowUp ? "Next analysis" : "01 / Analysis composer"}</p>
          <h2 id="composer-title">{isFollowUp ? "Run another analysis" : "Open a research run"}</h2>
          <p className="composer__supported">Supported symbols: AAPL, TSLA, MSFT</p>
        </div>
        <div className="theme-switch" aria-label="Color theme">
          <button aria-pressed={theme === "carbon"} onClick={() => onThemeChange("carbon")}>Carbon</button>
          <button aria-pressed={theme === "light"} onClick={() => onThemeChange("light")}>Light</button>
        </div>
      </div>
      <form
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <div className="field-grid">
          <div className="field field--request">
            <label className="field-label" htmlFor="request-text">Research request <span className="field-label__hint">Required when ticker field is empty</span></label>
            <textarea
              ref={requestInputRef}
              id="request-text"
              className="textarea"
              value={form.requestText}
              onChange={(event) => onChange("requestText", event.target.value)}
              placeholder="Analyze AAPL and TSLA"
              aria-describedby={errors.request ? "request-error" : undefined}
              aria-invalid={Boolean(errors.request)}
            />
            {errors.request ? <p className="field-error" id="request-error" role="alert">{errors.request}</p> : null}
          </div>
          <div className="field field--tickers">
            <label className="field-label" htmlFor="ticker-list">Ticker override <span className="field-label__hint">Optional, comma separated</span></label>
            <input
              id="ticker-list"
              className="input"
              value={form.tickersText}
              onChange={(event) => onChange("tickersText", event.target.value)}
              placeholder="AAPL, TSLA"
            />
          </div>
          <fieldset className="field field--domain">
            <legend className="field-label">Research domains</legend>
            <div className="domain-controls" aria-describedby={errors.domains ? "domains-error" : undefined}>
              {domains.map((domain) => (
                <label className="domain-control" key={domain}>
                  <input checked={form.domains.includes(domain)} onChange={() => toggleDomain(domain)} type="checkbox" />
                  <span>{titleCase(domain)}</span>
                </label>
              ))}
            </div>
            {errors.domains ? <p className="field-error" id="domains-error" role="alert">{errors.domains}</p> : null}
          </fieldset>
          <div className="field field--timeframe">
            <label className="field-label" htmlFor="timeframe">Timeframe</label>
            <select id="timeframe" className="select" value={form.timeframe} onChange={(event) => onChange("timeframe", event.target.value)}>
              <option value="1m">1 month</option>
              <option value="3m">3 months</option>
              <option value="6m">6 months</option>
              <option value="1y">1 year</option>
              <option value="5y">5 years</option>
            </select>
          </div>
          <div className="field field--focus">
            <label className="field-label" htmlFor="focus-areas">Focus areas <span className="field-label__hint">Optional</span></label>
            <input
              id="focus-areas"
              className="input"
              value={form.focusAreas}
              onChange={(event) => onChange("focusAreas", event.target.value)}
              placeholder="valuation, momentum"
            />
          </div>
        </div>
        <div className="composer__actions">
          <div className="composer__actions-copy">
            <p className="action-kicker">Ready to analyze</p>
            <span className="elapsed" aria-live="polite">{isSubmitting ? `Analysis running: ${elapsedSeconds} s elapsed` : "One synchronous request per analysis"}</span>
          </div>
          <Button variant="primary" type="submit" disabled={isSubmitting}>
            {isSubmitting ? <SpinnerGap aria-hidden="true" size={17} /> : null}
            {isSubmitting ? "Running analysis" : "Analyze"}
          </Button>
        </div>
      </form>
    </section>
  );
}
