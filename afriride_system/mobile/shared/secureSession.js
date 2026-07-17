import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const TOKEN_PREFIX = "afriride.auth.token.v2";
const SESSION_PREFIX = "afriride.auth.session.v2";
const memoryTokens = new Map();

function normalizeAppName(app = "shared") {
  return String(app || "shared").trim().toLowerCase().replace(/[^a-z0-9_-]/g, "-");
}

function tokenKey(app) {
  return `${TOKEN_PREFIX}.${normalizeAppName(app)}`;
}

function sessionKey(app) {
  return `${SESSION_PREFIX}.${normalizeAppName(app)}`;
}

function setMemoryToken(app, token) {
  const key = normalizeAppName(app);
  if (token && token.trim()) {
    memoryTokens.set(key, token.trim());
    return;
  }
  memoryTokens.delete(key);
}

export function getMemoryToken(app = "shared") {
  return memoryTokens.get(normalizeAppName(app)) || null;
}

export async function persistSession(token, metadata = {}, app = metadata?.app || "shared") {
  const normalizedApp = normalizeAppName(app);
  const safeToken = token && token.trim() ? token.trim() : null;
  setMemoryToken(normalizedApp, safeToken);
  if (!safeToken) {
    await Promise.all([
      SecureStore.deleteItemAsync(tokenKey(normalizedApp)),
      SecureStore.deleteItemAsync(sessionKey(normalizedApp)),
    ]);
    return;
  }
  await SecureStore.setItemAsync(tokenKey(normalizedApp), safeToken, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });
  await SecureStore.setItemAsync(
    sessionKey(normalizedApp),
    JSON.stringify({
      ...metadata,
      app: normalizedApp,
      storedAt: new Date().toISOString(),
    }),
    { keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY },
  );
}

export async function restoreSession(app = "shared") {
  const normalizedApp = normalizeAppName(app);
  const token = await SecureStore.getItemAsync(tokenKey(normalizedApp));
  setMemoryToken(normalizedApp, token);
  const raw = await SecureStore.getItemAsync(sessionKey(normalizedApp));
  if (!raw) {
    return {
      token: getMemoryToken(normalizedApp),
      metadata: null,
    };
  }

  try {
    return {
      token: getMemoryToken(normalizedApp),
      metadata: JSON.parse(raw),
    };
  } catch {
    await Promise.all([
      SecureStore.deleteItemAsync(tokenKey(normalizedApp)),
      SecureStore.deleteItemAsync(sessionKey(normalizedApp)),
    ]);
    setMemoryToken(normalizedApp, null);
    return {
      token: null,
      metadata: null,
    };
  }
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

export async function clearSession(app = "shared") {
  return persistSession(null, {}, app);
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
