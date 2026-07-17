export function getMemoryToken(app?: string): string | null;
export function persistSession(
  token: string | null,
  metadata?: Record<string, unknown>,
  app?: string,
): Promise<void>;
export function restoreSession(app?: string): Promise<{ token: string | null; metadata: Record<string, unknown> | null }>;
export function requireBiometricUnlock(reason?: string): Promise<{ success: boolean; reason: string | null }>;
export function clearSession(app?: string): Promise<void>;
export function requestSecurityHeaders(method: string): Record<string, string>;
export function assertSecureTransport(apiBaseUrl: string, testMode: boolean): void;
