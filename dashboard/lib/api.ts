import type { AnalysisRequest, ApiErrorEnvelope, RunState } from "@/lib/contracts";

const defaultApiBaseUrl = "http://localhost:8000";

export class ApiClientError extends Error {
  readonly code: string;
  readonly fields: ApiErrorEnvelope["error"]["fields"];
  readonly status: number | null;

  constructor({
    code,
    message,
    fields = [],
    status = null,
  }: {
    code: string;
    message: string;
    fields?: ApiErrorEnvelope["error"]["fields"];
    status?: number | null;
  }) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.fields = fields;
    this.status = status;
  }
}

function apiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? defaultApiBaseUrl).replace(/\/$/, "");
}

function isApiErrorEnvelope(payload: unknown): payload is ApiErrorEnvelope {
  if (!payload || typeof payload !== "object" || !("error" in payload)) {
    return false;
  }
  const error = payload.error;
  return Boolean(error && typeof error === "object" && "code" in error && "message" in error);
}

export async function submitAnalysis(
  request: AnalysisRequest,
  requestInit: RequestInit = {},
): Promise<RunState> {
  const { headers, ...rest } = requestInit;
  const requestHeaders = new Headers(headers);
  requestHeaders.set("Content-Type", "application/json");
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}/api/v1/analyses`, {
      ...rest,
      method: "POST",
      headers: requestHeaders,
      body: JSON.stringify(request),
    });
  } catch {
    throw new ApiClientError({
      code: "offline",
      message: "The analysis service is unavailable. Start the FastAPI server, then retry.",
    });
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    if (isApiErrorEnvelope(payload)) {
      throw new ApiClientError({
        code: payload.error.code,
        message: payload.error.message,
        fields: payload.error.fields,
        status: response.status,
      });
    }
    throw new ApiClientError({
      code: "server_error",
      message: "The analysis service returned an unexpected response. Retry the request.",
      status: response.status,
    });
  }

  if (!payload || typeof payload !== "object" || !("run_id" in payload) || !("status" in payload)) {
    throw new ApiClientError({
      code: "invalid_response",
      message: "The analysis response did not match the published API contract.",
      status: response.status,
    });
  }
  return payload as RunState;
}

export function recoveryMessage(error: ApiClientError): string {
  const stableMessages: Record<string, string> = {
    offline: "The analysis service is unavailable. Start the FastAPI server, then retry.",
    request_validation_error: "Check the request fields and submit a supported ticker.",
    persistence_error: "The analysis completed but could not be saved. Retry the request.",
    internal_error: "The analysis service could not complete this request. Retry once it is available.",
    server_error: "The analysis service returned an unexpected response. Retry the request.",
  };
  return stableMessages[error.code] ?? error.message;
}
