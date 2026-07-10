const DEFAULT_API_BASE_URL = "https://api.afritechnology.com";

function normalizeApiBaseUrl(value: string | undefined): string {
  const candidate = (value || DEFAULT_API_BASE_URL).trim();
  return candidate.replace(/\/+$/, "");
}

export const API_BASE_URL = normalizeApiBaseUrl(
  process.env.EXPO_PUBLIC_NOVARIDE_API_URL ||
    process.env.EXPO_PUBLIC_API_URL ||
    process.env.API_BASE_URL ||
    process.env.EXPO_PUBLIC_AFRIRIDE_API_URL,
);

export const API_HEALTH_PATH =
  process.env.EXPO_PUBLIC_NOVARIDE_HEALTH_PATH ||
  process.env.EXPO_PUBLIC_API_HEALTH_PATH ||
  "/health";

export const ORGANIZATION_ID =
  process.env.EXPO_PUBLIC_AFRIRIDE_ORGANIZATION_ID || "afritech-core";

export const REQUEST_TIMEOUT_MS = 8000;

export const USE_MOCK_API =
  process.env.EXPO_PUBLIC_AFRIRIDE_USE_MOCKS === "true";

export const TEST_MODE =
  process.env.EXPO_PUBLIC_AFRIRIDE_TEST_MODE !== "false";

export const APP_VERSION =
  process.env.EXPO_PUBLIC_AFRIRIDE_APP_VERSION || "2026.1.1";

export const RELEASE_CHANNEL =
  process.env.EXPO_PUBLIC_NOVARIDE_RELEASE_CHANNEL || "PUBLIC_PILOT";

export const RUNTIME_ENVIRONMENT =
  process.env.EXPO_PUBLIC_NOVARIDE_ENVIRONMENT || "PUBLIC_PILOT";

export const DEVICE_ID =
  process.env.EXPO_PUBLIC_AFRIRIDE_DEVICE_ID || "rider-test-device";

export const REGION_ID =
  process.env.EXPO_PUBLIC_AFRIRIDE_REGION_ID || "ug-kla";

export const APP_LOCALE =
  process.env.EXPO_PUBLIC_AFRIRIDE_LOCALE || "";
