import {
  clearSession,
  getMemoryToken,
  persistSession,
  requireBiometricUnlock,
  restoreSession,
} from "../../../afriride_system/mobile/shared/secureSession";

const APP_NAME = "rider";

export async function setAuthToken(token: string | null): Promise<void> {
  await persistSession(token, { app: APP_NAME }, APP_NAME);
}

export async function setAuthSession(
  token: string | null,
  metadata: Record<string, unknown> = {},
): Promise<void> {
  await persistSession(token, { app: APP_NAME, ...metadata }, APP_NAME);
}

export function getAuthToken(): string | null {
  return getMemoryToken(APP_NAME);
}

export async function clearAppSession(): Promise<void> {
  await clearSession(APP_NAME);
}

export async function restoreAppSession() {
  return restoreSession(APP_NAME);
}

export { requireBiometricUnlock };
