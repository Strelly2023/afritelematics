import { NOVACODEPRO_BUILD_INFO } from "./version.js";

const ALLOWED_ENVIRONMENTS = new Set([
  "local",
  "development",
  "test",
  "integration",
  "staging",
  "controlled-pilot",
  "public-pilot",
  "production",
  "disaster-recovery",
]);

function getBaseOrigin() {
  return globalThis.location?.origin || "http://localhost";
}

const DEFAULT_FRONTEND_RUNTIME_CONFIG = {
  environment: "production",
  region: "AU",
  releaseVersion: NOVACODEPRO_BUILD_INFO.version,
  buildCommit: NOVACODEPRO_BUILD_INFO.commit,
  apiBaseUrl: new URL(NOVACODEPRO_BUILD_INFO.api_base_url || "/v1", getBaseOrigin()).toString(),
  authBaseUrl: new URL("/v1", getBaseOrigin()).toString(),
  websocketUrl: "",
  enabledProducts: ["novacodepro", "solution-engineering"],
  defaultLocale: "en-AU",
  defaultTimezone: "Australia/Melbourne",
  maintenanceMode: false,
  supportUrl: "",
  statusUrl: "",
  source: "build-info",
};

function toStringOrEmpty(value) {
  return typeof value === "string" ? value.trim() : "";
}

function toBoolean(value) {
  return Boolean(value);
}

function toStringArray(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => String(item).trim()).filter(Boolean);
}

function requireString(value, field) {
  const normalized = toStringOrEmpty(value);
  if (!normalized) {
    throw new Error(`Frontend runtime config missing ${field}.`);
  }
  return normalized;
}

function optionalUrl(value, field) {
  const normalized = toStringOrEmpty(value);
  if (!normalized) {
    return "";
  }
  try {
    return new URL(normalized, getBaseOrigin()).toString();
  } catch {
    throw new Error(`Frontend runtime config field ${field} must be a valid URL.`);
  }
}

export function normalizeFrontendRuntimeConfig(input = {}) {
  const environment = requireString(input.environment ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.environment, "environment");
  if (!ALLOWED_ENVIRONMENTS.has(environment)) {
    throw new Error(`Frontend runtime config environment "${environment}" is not supported.`);
  }
  return {
    environment,
    region: requireString(input.region ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.region, "region"),
    releaseVersion: requireString(input.releaseVersion ?? input.release_version ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.releaseVersion, "releaseVersion"),
    buildCommit: requireString(input.buildCommit ?? input.build_commit ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.buildCommit, "buildCommit"),
    apiBaseUrl: optionalUrl(input.apiBaseUrl ?? input.api_base_url ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.apiBaseUrl, "apiBaseUrl"),
    authBaseUrl: optionalUrl(input.authBaseUrl ?? input.auth_base_url ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.authBaseUrl, "authBaseUrl"),
    websocketUrl: optionalUrl(input.websocketUrl ?? input.websocket_url ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.websocketUrl, "websocketUrl"),
    enabledProducts: toStringArray(input.enabledProducts ?? input.enabled_products ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.enabledProducts),
    defaultLocale: requireString(input.defaultLocale ?? input.default_locale ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.defaultLocale, "defaultLocale"),
    defaultTimezone: requireString(input.defaultTimezone ?? input.default_timezone ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.defaultTimezone, "defaultTimezone"),
    maintenanceMode: toBoolean(input.maintenanceMode ?? input.maintenance_mode ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.maintenanceMode),
    supportUrl: optionalUrl(input.supportUrl ?? input.support_url ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.supportUrl, "supportUrl"),
    statusUrl: optionalUrl(input.statusUrl ?? input.status_url ?? DEFAULT_FRONTEND_RUNTIME_CONFIG.statusUrl, "statusUrl"),
    source: toStringOrEmpty(input.source) || "runtime.json",
  };
}

export function createDefaultFrontendRuntimeConfig() {
  return { ...DEFAULT_FRONTEND_RUNTIME_CONFIG };
}

export async function loadFrontendRuntimeConfig({
  fetchImpl = globalThis.fetch,
  runtimeConfigUrl = "/config/runtime.json",
  signal,
} = {}) {
  if (typeof fetchImpl !== "function") {
    return createDefaultFrontendRuntimeConfig();
  }
  try {
    const response = await fetchImpl(runtimeConfigUrl, {
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        "x-requested-with": "fetch",
      },
      signal,
    });
    if (!response || !response.ok) {
      return createDefaultFrontendRuntimeConfig();
    }
    const payload = await response.json().catch(() => ({}));
    return normalizeFrontendRuntimeConfig(payload);
  } catch {
    return createDefaultFrontendRuntimeConfig();
  }
}
