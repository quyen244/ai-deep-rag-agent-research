import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DashboardClient } from "@/components/dashboard/dashboard-client";
import { partialRun, successfulRun } from "@/tests/fixtures";

function renderDashboard() {
  return render(<div className="app-shell" data-theme="carbon"><DashboardClient /></div>);
}

describe("dashboard states", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("keeps the empty state and focuses the request field for invalid input", async () => {
    const user = userEvent.setup();
    renderDashboard();
    await user.click(screen.getByRole("button", { name: "Analyze" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Enter a research request or at least one ticker.");
    expect(screen.getByLabelText(/Research request/i)).toHaveFocus();
    expect(screen.getByText("Start with a decision")).toBeInTheDocument();
  });

  it("renders a submitted multi-ticker workspace and comparison", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(successfulRun), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    renderDashboard();

    await user.type(screen.getByLabelText(/Research request/i), "Analyze AAPL and TSLA");
    await user.click(screen.getByRole("button", { name: "Analyze" }));

    expect(await screen.findByRole("heading", { name: "Research brief" })).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Comparison" }));
    expect(screen.getByRole("table")).toHaveTextContent("Price to earnings");
    expect(screen.getAllByText("Preferred").length).toBeGreaterThan(0);
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toMatchObject({ request_text: "Analyze AAPL and TSLA" });
  });

  it("preserves successful sections and labels unavailable partial outcomes", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(partialRun), { status: 200 })));
    renderDashboard();

    await user.type(screen.getByLabelText(/Research request/i), "Analyze AAPL and TSLA");
    await user.click(screen.getByRole("button", { name: "Analyze" }));

    expect(await screen.findByText("Partial result.")).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Fundamental" }));
    expect(screen.getAllByText(/Fundamental data source was unavailable/i)[0]).toBeInTheDocument();
  });

  it("retains form input and offers a stable offline recovery action", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    renderDashboard();
    const request = screen.getByLabelText(/Research request/i);

    await user.type(request, "Analyze AAPL");
    await user.click(screen.getByRole("button", { name: "Analyze" }));

    expect(await screen.findByText(/analysis service is unavailable/i)).toBeInTheDocument();
    expect(request).toHaveValue("Analyze AAPL");
    expect(screen.getByRole("button", { name: /Retry analysis/i })).toBeInTheDocument();
  });

  it("switches to the light substrate without changing the active workspace", async () => {
    const user = userEvent.setup();
    renderDashboard();
    await user.click(screen.getByRole("button", { name: "Light" }));

    await waitFor(() => expect(document.querySelector(".app-shell")).toHaveAttribute("data-theme", "light"));
    fireEvent.click(screen.getByRole("button", { name: "Carbon" }));
    await waitFor(() => expect(document.querySelector(".app-shell")).toHaveAttribute("data-theme", "carbon"));
  });
});
