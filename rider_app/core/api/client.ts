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

type RequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
  headers?: Record<string, string>;
};

function toApiError(payload: unknown, fallback: string, status?: number): Error {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = String(payload.detail);
    if (status === 401 || status === 403 || /token|session|auth/i.test(detail)) {
      return new Error("Sign in again.");
    }
    return new Error(detail);
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
  assertSecureTransport(API_BASE_URL, TEST_MODE);

  try {
    const token = getAuthToken();
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
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
      throw toApiError(payload, "api_request_failed", response.status);
    }

    return payload as T;
  } finally {
    clearTimeout(timeout);
  }
}
