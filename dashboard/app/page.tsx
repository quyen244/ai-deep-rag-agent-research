import { DashboardClient } from "@/components/dashboard/dashboard-client";

export default function HomePage() {
  return (
    <div className="app-shell" data-theme="carbon">
      <a className="skip-link" href="#workspace">Skip to analysis workspace</a>
      <header className="masthead" aria-label="Application header">
        <div className="masthead__identity">
          <span className="crosshair" aria-hidden="true">+</span>
          <p className="eyebrow">Multi-agent financial analysis</p>
          <h1>Signal Ledger</h1>
        </div>
        <p className="masthead__revision">REV 07 / SYNCHRONOUS RESEARCH DESK</p>
      </header>
      <main id="workspace" className="workspace" tabIndex={-1}>
        <DashboardClient />
      </main>
      <footer className="site-footer">
        <span>STRUCTURED RESEARCH / LOCAL API CONTRACT</span>
        <span>NOT INVESTMENT ADVICE</span>
      </footer>
    </div>
  );
}
