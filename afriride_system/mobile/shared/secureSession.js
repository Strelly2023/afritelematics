import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const TOKEN_KEY = "afriride.auth.token.v2";
const SESSION_KEY = "afriride.auth.session.v2";
let memoryToken = null;

export function getMemoryToken() {
  return memoryToken;
}

export async function persistSession(token, metadata = {}) {
  memoryToken = token && token.trim() ? token.trim() : null;
  if (!memoryToken) {
    await Promise.all([
      SecureStore.deleteItemAsync(TOKEN_KEY),
      SecureStore.deleteItemAsync(SESSION_KEY),
    ]);
    return;
  }
  await SecureStore.setItemAsync(TOKEN_KEY, memoryToken, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });
  await SecureStore.setItemAsync(
    SESSION_KEY,
    JSON.stringify({ ...metadata, storedAt: new Date().toISOString() }),
    { keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY },
  );
}

export async function restoreSession() {
  memoryToken = await SecureStore.getItemAsync(TOKEN_KEY);
  const raw = await SecureStore.getItemAsync(SESSION_KEY);
  return {
    token: memoryToken,
    metadata: raw ? JSON.parse(raw) : null,
  };
}

export async function requireBiometricUnlock(reason = "Unlock AfriRide") {
  const supported = await SecureStore.canUseBiometricAuthentication();
  if (!supported) return { success: false, reason: "biometrics_unavailable" };
  const markerKey = "afriride.biometric.unlock.v1";
  await SecureStore.setItemAsync(markerKey, "enabled", {
    requireAuthentication: true,
    authenticationPrompt: reason,
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });
  const result = await SecureStore.getItemAsync(markerKey, {
    requireAuthentication: true,
    authenticationPrompt: reason,
  });
  return { success: result === "enabled", reason: result ? null : "authentication_failed" };
}

export async function clearSession() {
  return persistSession(null);
}

export function requestSecurityHeaders(method) {
  if (method === "GET") return {};
  const random =
    globalThis.crypto?.randomUUID?.() ||
    `${Date.now()}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
  return {
    "X-Request-Timestamp": String(Date.now() / 1000),
    "X-Request-Nonce": `${Platform.OS}-${random}`,
  };
}

export function assertSecureTransport(apiBaseUrl, testMode) {
  const url = new URL(apiBaseUrl);
  if (!testMode && url.protocol !== "https:") {
    throw new Error("secure_transport_required");
  }
}
