import { ROUTES } from "../platform/routes.js";

const PUBLIC_AUTH_PATHS = new Set([
  ROUTES.login,
  "/novacodepro/forgot-password",
  "/novacodepro/reset-password",
  "/novacodepro/auth/callback",
  "/novacodepro/auth/help",
]);

export function isPublicAuthPath(pathname) {
  return PUBLIC_AUTH_PATHS.has(String(pathname || "").replace(/\/$/, ""));
}

export function resolveSafeReturnTo(value, fallback = ROUTES.dashboard) {
  if (typeof value !== "string" || !value.startsWith("/novacodepro/") || value.startsWith("//") || value.includes("\\")) {
    return fallback;
  }
  try {
    const parsed = new URL(value, "http://novacodepro.local");
    if (parsed.origin !== "http://novacodepro.local" || !parsed.pathname.startsWith("/novacodepro/") || isPublicAuthPath(parsed.pathname)) {
      return fallback;
    }
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return fallback;
  }
}
