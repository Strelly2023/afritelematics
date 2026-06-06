import { API_BASE_URL, REQUEST_TIMEOUT_MS } from "../config/environment";
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

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...instrumentationHeaders(clientEvent),
        ...(options.headers || {}),
      },
      body:
        options.body === undefined
          ? undefined
          : JSON.stringify(withClientEvent(options.body, clientEvent)),
      signal: controller.signal,
    });

    const payload = await response.json();

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
    recordNetworkLatency(
      clientEvent.actor_id,
      path,
      method,
      0,
      Date.now() - startedAt,
      error instanceof Error ? error.message : "network_error",
    );
    throw error;
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
