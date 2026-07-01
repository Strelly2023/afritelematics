import { API_BASE_URL, REQUEST_TIMEOUT_MS } from "../config/environment";
import { getAuthToken } from "./session";
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

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(getAuthToken() ? { Authorization: `Bearer ${getAuthToken()}` } : {}),
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

    return payload as T;
  } finally {
    clearTimeout(timeout);
  }
}
