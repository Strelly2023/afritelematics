export const API_BASE_URL =
  process.env.EXPO_PUBLIC_AFRIRIDE_API_URL || "http://127.0.0.1:8000";

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

export const APP_VERSION =
  process.env.EXPO_PUBLIC_AFRIRIDE_APP_VERSION || "0.1";

export const DEVICE_ID =
  process.env.EXPO_PUBLIC_AFRIRIDE_DEVICE_ID || "driver-test-device";
