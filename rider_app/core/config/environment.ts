export const API_BASE_URL =
  process.env.EXPO_PUBLIC_AFRIRIDE_API_URL || "http://127.0.0.1:8000";

export const REQUEST_TIMEOUT_MS = 8000;

export const USE_MOCK_API =
  process.env.EXPO_PUBLIC_AFRIRIDE_USE_MOCKS === "true";

export const TEST_MODE =
  process.env.EXPO_PUBLIC_AFRIRIDE_TEST_MODE !== "false";

export const APP_VERSION =
  process.env.EXPO_PUBLIC_AFRIRIDE_APP_VERSION || "0.1";

export const DEVICE_ID =
  process.env.EXPO_PUBLIC_AFRIRIDE_DEVICE_ID || "rider-test-device";
