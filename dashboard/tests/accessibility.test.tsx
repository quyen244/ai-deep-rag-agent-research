import axe from "axe-core";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DashboardClient } from "@/components/dashboard/dashboard-client";

describe("dashboard accessibility", () => {
  it("has no serious static accessibility violations", async () => {
    const { container } = render(<div className="app-shell" data-theme="carbon"><DashboardClient /></div>);
    const result = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    const seriousViolations = result.violations.filter((violation) => ["serious", "critical"].includes(violation.impact ?? ""));

    expect(seriousViolations).toEqual([]);
  });
});
