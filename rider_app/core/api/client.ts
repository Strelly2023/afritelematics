import { API_BASE_URL, REQUEST_TIMEOUT_MS } from "../config/environment";
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

    return payload as T;
  } finally {
    clearTimeout(timeout);
  }
}
