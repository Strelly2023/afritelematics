import {
  API_BASE_URL,
  API_HEALTH_PATH,
  REQUEST_TIMEOUT_MS,
  TEST_MODE,
} from "../config/environment";
import { getAuthToken } from "./session";
import {
  assertSecureTransport,
  requestSecurityHeaders,
} from "../../../afriride_system/mobile/shared/secureSession";
import {
  buildClientEvent,
  instrumentationHeaders,
  withClientEvent,
} from "./testInstrumentation";
import { PILOT_LATENCY_THRESHOLD_MS } from "../config/environment";
import {
  capturePilotEvidence,
  latencyVerdict,
} from "../services/pilotEvidence.service";

type RequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
  headers?: Record<string, string>;
};

export type ConnectivityCheck = {
  label: string;
  status: "pass" | "fail";
  detail: string;
};

function buildRequestUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

function isNetworkFailure(error: unknown): boolean {
  return (
    error instanceof TypeError ||
    (error instanceof Error &&
      /Network request failed|Failed to fetch|Load failed|NetworkError|fetch failed/i.test(
        error.message,
      ))
  );
}

function sanitizeErrorMessage(message: string): string {
  return message.replace(/\s+/g, " ").slice(0, 180);
}

export function toDriverFacingApiError(
  error: unknown,
  path: string,
  durationMs: number,
): Error {
  if (error instanceof Error && error.name === "AbortError") {
    return new Error(
      `Unable to connect to the NovaRide service. Request timed out after ${REQUEST_TIMEOUT_MS}ms. Technical details: request_timeout after ${REQUEST_TIMEOUT_MS}ms endpoint=${path} api_host=${API_BASE_URL} duration_ms=${durationMs}`,
    );
  }

  if (isNetworkFailure(error)) {
    return new Error(
      `Unable to connect to the NovaRide service. Check the internet connection or try again later. Technical details: network_unreachable endpoint=${path} api_host=${API_BASE_URL} duration_ms=${durationMs}`,
    );
  }

  if (error instanceof Error) {
    return new Error(sanitizeErrorMessage(error.message));
  }

  return new Error("Unable to connect to the NovaRide service. Technical details: unknown_client_error");
}

function toApiError(payload: unknown, fallback: string): Error {
  if (payload && typeof payload === "object" && "detail" in payload) {
    return new Error(String(payload.detail));
  }
  return new Error(fallback);
}

async function readResponsePayload(response: Response): Promise<unknown> {
  const body = await response.text();
  if (!body) {
    return {};
  }
  try {
    return JSON.parse(body);
  } catch {
    const preview = body.replace(/\s+/g, " ").slice(0, 160);
    throw new Error(
      `non_json_response status=${response.status} content_type=${response.headers.get(
        "content-type",
      ) || "unknown"} body=${preview}`,
    );
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const method = options.method || "GET";
  const clientEvent = buildClientEvent({
    path,
    method,
    payload: options.body,
  });
  const startedAt = Date.now();
  assertSecureTransport(API_BASE_URL, TEST_MODE);

  try {
    const response = await fetch(buildRequestUrl(path), {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(getAuthToken() ? { Authorization: `Bearer ${getAuthToken()}` } : {}),
        ...requestSecurityHeaders(method),
        ...instrumentationHeaders(clientEvent),
        ...(options.headers || {}),
      },
      body:
        options.body === undefined
          ? undefined
          : JSON.stringify(withClientEvent(options.body, clientEvent)),
      signal: controller.signal,
    });

    const payload = await readResponsePayload(response);

    if (!response.ok) {
      throw toApiError(payload, "api_request_failed");
    }

    recordNetworkLatency(
      clientEvent.actor_id,
      path,
      method,
      response.status,
      Date.now() - startedAt,
    );

    return payload as T;
  } catch (error) {
    const requestError = toDriverFacingApiError(error, path, Date.now() - startedAt);
    recordNetworkLatency(
      clientEvent.actor_id,
      path,
      method,
      0,
      Date.now() - startedAt,
      requestError instanceof Error ? requestError.message : "network_error",
    );
    throw requestError;
  } finally {
    clearTimeout(timeout);
  }
}

export async function runApiConnectivityDiagnostics(): Promise<ConnectivityCheck[]> {
  const checks: ConnectivityCheck[] = [
    {
      label: "API host",
      status: /^https:\/\//i.test(API_BASE_URL) ? "pass" : "fail",
      detail: API_BASE_URL,
    },
  ];

  try {
    assertSecureTransport(API_BASE_URL, TEST_MODE);
    checks.push({
      label: "TLS policy",
      status: "pass",
      detail: TEST_MODE ? "test mode allows diagnostics" : "HTTPS required",
    });
  } catch (error) {
    checks.push({
      label: "TLS policy",
      status: "fail",
      detail: error instanceof Error ? error.message : "secure transport rejected",
    });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const startedAt = Date.now();
  try {
    const response = await fetch(buildRequestUrl(API_HEALTH_PATH), {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
    });
    checks.push({
      label: "Health endpoint",
      status: response.ok ? "pass" : "fail",
      detail: `${response.status} ${response.statusText || ""}`.trim(),
    });
  } catch (error) {
    checks.push({
      label: "Health endpoint",
      status: "fail",
      detail: toDriverFacingApiError(error, API_HEALTH_PATH, Date.now() - startedAt).message,
    });
  } finally {
    clearTimeout(timeout);
  }

  return checks;
}

function recordNetworkLatency(
  driverId: string,
  path: string,
  method: string,
  statusCode: number,
  latencyMs: number,
  error?: string,
) {
  void capturePilotEvidence(
    driverId || "unknown_driver",
    "network_latency_event",
    {
      path,
      method,
      status_code: statusCode,
      latency_ms: latencyMs,
      error: error || null,
    },
    { expected_max_latency_ms: PILOT_LATENCY_THRESHOLD_MS },
    error ? "violation" : latencyVerdict(latencyMs),
  ).catch(() => undefined);
}
