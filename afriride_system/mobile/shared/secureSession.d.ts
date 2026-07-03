export function getMemoryToken(): string | null;
export function persistSession(token: string | null, metadata?: Record<string, unknown>): Promise<void>;
export function restoreSession(): Promise<{ token: string | null; metadata: Record<string, unknown> | null }>;
export function requireBiometricUnlock(reason?: string): Promise<{ success: boolean; reason: string | null }>;
export function clearSession(): Promise<void>;
export function requestSecurityHeaders(method: string): Record<string, string>;
export function assertSecureTransport(apiBaseUrl: string, testMode: boolean): void;
