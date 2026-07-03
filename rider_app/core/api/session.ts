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

export function getAuthToken(): string | null {
  return getMemoryToken();
}

export { clearSession, requireBiometricUnlock, restoreSession };
