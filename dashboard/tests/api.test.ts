import { afterEach, describe, expect, it, vi } from "vitest";
import { submitAnalysis } from "@/lib/api";
import { successfulRun } from "@/tests/fixtures";

describe("FastAPI client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("posts the published request envelope and returns a run state", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(successfulRun), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await submitAnalysis({ request_text: "Analyze AAPL and TSLA", domains: ["technical"] });

    expect(result.run_id).toBe(successfulRun.run_id);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/analyses",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ request_text: "Analyze AAPL and TSLA", domains: ["technical"] }) }),
    );
  });

  it("maps a stable error envelope without parsing message text", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { code: "request_validation_error", message: "Contract rejected", context: {}, fields: [] } }), { status: 422 })));

    await expect(submitAnalysis({ tickers: ["BAD"] })).rejects.toMatchObject({ code: "request_validation_error", status: 422 });
  });

  it("maps a connection failure to the offline recovery code", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network unavailable")));

    await expect(submitAnalysis({ tickers: ["AAPL"] })).rejects.toMatchObject({ code: "offline", status: null });
  });
});
