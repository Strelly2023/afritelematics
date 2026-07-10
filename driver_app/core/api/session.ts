import {
  clearSession,
  getMemoryToken,
  persistSession,
  requireBiometricUnlock,
  restoreSession,
} from "../../../afriride_system/mobile/shared/secureSession";

export async function setAuthToken(token: string | null): Promise<void> {
  await persistSession(token, { app: "driver" });
}

export async function setAuthSession(
  token: string | null,
  metadata: Record<string, unknown> = {},
): Promise<void> {
  await persistSession(token, { app: "driver", ...metadata });
}

export function getAuthToken(): string | null {
  return getMemoryToken();
}

export { clearSession, requireBiometricUnlock, restoreSession };
