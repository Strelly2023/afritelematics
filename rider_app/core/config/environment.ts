const DEFAULT_API_BASE_URL = "https://api.afritechnology.com";
const RUNTIME_ENVIRONMENT_VALUE =
  process.env.EXPO_PUBLIC_NOVARIDE_ENVIRONMENT || "development";
const RELEASE_CHANNEL_VALUE =
  process.env.EXPO_PUBLIC_NOVARIDE_RELEASE_CHANNEL || "PUBLIC_PILOT";
const IS_PRODUCTION =
  RUNTIME_ENVIRONMENT_VALUE.toLowerCase() === "production" ||
  RELEASE_CHANNEL_VALUE.toUpperCase() === "PRODUCTION";
export type RuntimeMode = "production" | "pilot" | "test";

export const RUNTIME_MODE: RuntimeMode = IS_PRODUCTION
  ? "production"
  : process.env.EXPO_PUBLIC_AFRIRIDE_TEST_MODE === "false"
    ? "pilot"
    : "test";

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
  !IS_PRODUCTION && process.env.EXPO_PUBLIC_AFRIRIDE_USE_MOCKS === "true";

export const TEST_MODE =
  process.env.EXPO_PUBLIC_AFRIRIDE_TEST_MODE !== "false";

export type AttestationPolicy = "strict" | "public_pilot_fallback" | "public_pilot_degraded";

function normalizeAttestationPolicy(value: string | undefined): AttestationPolicy {
  if (
    value === "strict" ||
    value === "public_pilot_fallback" ||
    value === "public_pilot_degraded"
  ) {
    return value;
  }
  return TEST_MODE ? "public_pilot_fallback" : "strict";
}

export const ATTESTATION_POLICY = normalizeAttestationPolicy(
  process.env.EXPO_PUBLIC_NOVARIDE_ATTESTATION_POLICY,
);

if (IS_PRODUCTION && (TEST_MODE || USE_MOCK_API || ATTESTATION_POLICY !== "strict")) {
  throw new Error(
    "NovaRide production configuration forbids test mode, mock APIs, and degraded attestation.",
  );
}

export const APP_VERSION =
  process.env.EXPO_PUBLIC_AFRIRIDE_APP_VERSION || "2026.1.4";

export const RELEASE_CHANNEL =
  RELEASE_CHANNEL_VALUE;

export const RUNTIME_ENVIRONMENT =
  RUNTIME_ENVIRONMENT_VALUE;

export const DEVICE_ID =
  process.env.EXPO_PUBLIC_AFRIRIDE_DEVICE_ID || "rider-test-device";

export const REGION_ID =
  process.env.EXPO_PUBLIC_AFRIRIDE_REGION_ID || "ug-kla";

export const APP_LOCALE =
  process.env.EXPO_PUBLIC_AFRIRIDE_LOCALE || "";
