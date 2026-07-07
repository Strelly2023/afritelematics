import { API_BASE_URL, REQUEST_TIMEOUT_MS, TEST_MODE } from "../config/environment";
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
    const response = await fetch(`${API_BASE_URL}${path}`, {
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
    const requestError =
      error instanceof Error && error.name === "AbortError"
        ? new Error(
            `request_timeout after ${REQUEST_TIMEOUT_MS}ms at ${API_BASE_URL}${path}`,
          )
        : error;
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
