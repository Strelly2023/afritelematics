import {
  clearSession,
  getMemoryToken,
  persistSession,
  requireBiometricUnlock,
  restoreSession,
} from "../../../afriride_system/mobile/shared/secureSession";

export async function setAuthToken(token: string | null): Promise<void> {
  await persistSession(token, { app: "rider" });
}

export async function setAuthSession(
  token: string | null,
  metadata: Record<string, unknown> = {},
): Promise<void> {
  await persistSession(token, { app: "rider", ...metadata });
}

export function getAuthToken(): string | null {
  return getMemoryToken();
}

export { clearSession, requireBiometricUnlock, restoreSession };
