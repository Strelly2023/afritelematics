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

export type DriverApiErrorCode =
  | "dns_failure"
  | "connection_refused"
  | "network_unreachable"
  | "tls_failure"
  | "request_timeout"
  | "authentication_required"
  | "authorization_denied"
  | "endpoint_not_found"
  | "server_unavailable"
  | "invalid_content_type"
  | "invalid_response"
  | "request_cancelled"
  | "unknown_network_error";

export class DriverApiError extends Error {
  code: DriverApiErrorCode;
  endpoint: string;
  status?: number;
  requestId: string;
  durationMs: number;
  technicalDetails: string;

  constructor(args: {
    code: DriverApiErrorCode;
    message: string;
    endpoint: string;
    requestId: string;
    durationMs: number;
    status?: number;
    technicalDetails?: string;
  }) {
    super(args.message);
    this.name = "DriverApiError";
    this.code = args.code;
    this.endpoint = args.endpoint;
    this.requestId = args.requestId;
    this.durationMs = args.durationMs;
    this.status = args.status;
    this.technicalDetails = args.technicalDetails || "";
  }
}

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

function makeApiError(
  code: DriverApiErrorCode,
  endpoint: string,
  requestId: string,
  durationMs: number,
  message: string,
  technicalDetails?: string,
  status?: number,
): DriverApiError {
  return new DriverApiError({
    code,
    endpoint,
    requestId,
    durationMs,
    message,
    technicalDetails,
    status,
  });
}

export function toDriverFacingApiError(
  error: unknown,
  path: string,
  durationMs: number,
  requestId = "unknown",
): Error {
  if (error instanceof Error && error.name === "AbortError") {
    return makeApiError(
      "request_timeout",
      path,
      requestId,
      durationMs,
      "Connection unavailable. Request timed out. Try again.",
      `request_timeout after ${REQUEST_TIMEOUT_MS}ms endpoint=${path} api_host=${API_BASE_URL}`,
    );
  }

  if (isNetworkFailure(error)) {
    return makeApiError(
      "network_unreachable",
      path,
      requestId,
      durationMs,
      "Connection unavailable. Check your internet connection and try again.",
      `network_unreachable endpoint=${path} api_host=${API_BASE_URL}`,
    );
  }

  if (error instanceof Error) {
    return makeApiError(
      "unknown_network_error",
      path,
      requestId,
      durationMs,
      "Connection unavailable. Try again.",
      sanitizeErrorMessage(error.message),
    );
  }

  return makeApiError(
    "unknown_network_error",
    path,
    requestId,
    durationMs,
    "Connection unavailable. Try again.",
    "unknown_client_error",
  );
}

function toApiError(
  payload: unknown,
  fallback: string,
  status: number,
  endpoint: string,
  requestId: string,
  durationMs: number,
): Error {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = String(payload.detail);
    if (status === 401) {
      return makeApiError("authentication_required", endpoint, requestId, durationMs, "Sign in again.", detail, status);
    }
    if (status === 403) {
      return makeApiError("authorization_denied", endpoint, requestId, durationMs, "Access denied.", detail, status);
    }
    if (status === 404) {
      return makeApiError("endpoint_not_found", endpoint, requestId, durationMs, "Service endpoint not found.", detail, status);
    }
    if (status >= 500) {
      return makeApiError("server_unavailable", endpoint, requestId, durationMs, "Service unavailable. Try again later.", detail, status);
    }
    return makeApiError("invalid_response", endpoint, requestId, durationMs, "Unexpected response from the service.", detail, status);
  }
  return makeApiError(
    status >= 500 ? "server_unavailable" : "invalid_response",
    endpoint,
    requestId,
    durationMs,
    fallback,
    `status=${status}`,
    status,
  );
}

async function readResponsePayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  if (contentType && !/json/i.test(contentType)) {
    const body = await response.text();
    const preview = body.replace(/\s+/g, " ").slice(0, 160);
    throw new DriverApiError({
      code: "invalid_content_type",
      endpoint: response.url || "unknown",
      requestId: "unknown",
      durationMs: 0,
      message: "Unexpected response format from the service.",
      technicalDetails: `content_type=${contentType} body=${preview}`,
      status: response.status,
    });
  }
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
  const requestId = clientEvent.event_id;
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
      throw toApiError(
        payload,
        "Service unavailable. Try again later.",
        response.status,
        path,
        requestId,
        Date.now() - startedAt,
      );
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
    const requestError =
      error instanceof DriverApiError
        ? error
        : toDriverFacingApiError(error, path, Date.now() - startedAt, requestId);
    recordNetworkLatency(
      clientEvent.actor_id,
      path,
      method,
      0,
      Date.now() - startedAt,
      requestError instanceof DriverApiError
        ? `${requestError.code} ${requestError.technicalDetails}`.trim()
        : requestError instanceof Error
          ? requestError.message
          : "network_error",
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
