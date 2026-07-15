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

export const DRIVER_ID =
  process.env.EXPO_PUBLIC_AFRIRIDE_DRIVER_ID || "";

export const REQUEST_TIMEOUT_MS = 8000;

export const LOCATION_SAMPLE_INTERVAL_MS = Number(
  process.env.EXPO_PUBLIC_AFRIRIDE_LOCATION_INTERVAL_MS || 5000,
);

export const NETWORK_SAMPLE_INTERVAL_MS = Number(
  process.env.EXPO_PUBLIC_AFRIRIDE_NETWORK_INTERVAL_MS || 5000,
);

export const PILOT_LATENCY_THRESHOLD_MS = Number(
  process.env.EXPO_PUBLIC_AFRIRIDE_LATENCY_THRESHOLD_MS || 500,
);

export const PILOT_GPS_ACCURACY_THRESHOLD_M = Number(
  process.env.EXPO_PUBLIC_AFRIRIDE_GPS_ACCURACY_THRESHOLD_M || 50,
);

export const PILOT_ROUTE_DEVIATION_THRESHOLD_M = Number(
  process.env.EXPO_PUBLIC_AFRIRIDE_ROUTE_DEVIATION_THRESHOLD_M || 250,
);

export const PILOT_SPEED_THRESHOLD_KPH = Number(
  process.env.EXPO_PUBLIC_AFRIRIDE_SPEED_THRESHOLD_KPH || 130,
);

export const USE_MOCK_API =
  process.env.EXPO_PUBLIC_AFRIRIDE_USE_MOCKS === "true";

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

export const APP_VERSION =
  process.env.EXPO_PUBLIC_AFRIRIDE_APP_VERSION || "2026.1.3";

export const RELEASE_CHANNEL =
  process.env.EXPO_PUBLIC_NOVARIDE_RELEASE_CHANNEL || "PUBLIC_PILOT";

export const RUNTIME_ENVIRONMENT =
  process.env.EXPO_PUBLIC_NOVARIDE_ENVIRONMENT || "PUBLIC_PILOT";

export const DEVICE_ID =
  process.env.EXPO_PUBLIC_AFRIRIDE_DEVICE_ID || "driver-test-device";

export const REGION_ID =
  process.env.EXPO_PUBLIC_AFRIRIDE_REGION_ID || "ug-kla";

export const APP_LOCALE =
  process.env.EXPO_PUBLIC_AFRIRIDE_LOCALE || "";
