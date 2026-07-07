export type NovaIDSession = Readonly<{ subject: string; roles: readonly string[]; expiresAt: string }>;
export const hasRole = (session: NovaIDSession, role: string) => session.roles.includes(role);
export const novaIDLogin = (subject: string, roles: readonly string[]): NovaIDSession => ({
  subject,
  roles,
  expiresAt: new Date(Date.now() + 3_600_000).toISOString(),
});
