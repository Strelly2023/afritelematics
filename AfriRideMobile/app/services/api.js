import { assertBackendConfirmed } from "../constants/authority";

const API_BASE_URL =
  process.env.EXPO_PUBLIC_AFRIRIDE_API_URL || "https://afriride-api.onrender.com";
const API_TOKEN = process.env.EXPO_PUBLIC_AFRIRIDE_API_TOKEN || null;

export async function apiRequest(endpoint, methodOrOptions = "GET", body = null, token = null) {
  const options =
    typeof methodOrOptions === "string"
      ? { method: methodOrOptions, body, token }
      : methodOrOptions;
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...((options.token || API_TOKEN) ? { Authorization: `Bearer ${options.token || API_TOKEN}` } : {}),
      ...(options.headers || {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload?.error?.message || payload?.detail || "API request failed");
  }
  return assertBackendConfirmed(payload);
}
