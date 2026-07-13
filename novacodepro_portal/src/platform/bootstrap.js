const DEFAULT_TIMEOUT_MS = 8000;

function normalizeError(error, fallbackCode = "APPLICATION_ERROR") {
  if (error && typeof error === "object" && "code" in error) {
    return error;
  }
  return {
    code: fallbackCode,
    message: error instanceof Error ? error.message : String(error || fallbackCode),
  };
}

async function readJson(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    throw {
      code: "MALFORMED_RESPONSE",
      message: "Bootstrap response was not valid JSON.",
    };
  }
}

export async function fetchBootstrap(baseUrl = "", { signal } = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  const onAbort = () => controller.abort(signal.reason);
  if (signal) {
    if (signal.aborted) {
      controller.abort(signal.reason);
    } else {
      signal.addEventListener("abort", onAbort, { once: true });
    }
  }

  try {
    const response = await fetch(`${baseUrl}/v1/novacodepro/session/bootstrap`, {
      credentials: "include",
      signal: controller.signal,
      headers: {
        "x-requested-with": "fetch",
      },
    });
    const payload = await readJson(response);
    return { response, payload };
  } catch (error) {
    throw normalizeError(error, "API_UNAVAILABLE");
  } finally {
    window.clearTimeout(timeout);
    if (signal) {
      signal.removeEventListener("abort", onAbort);
    }
  }
}

export function normalizeBootstrapResponse(payload) {
  if (!payload || typeof payload !== "object") {
    throw { code: "MALFORMED_RESPONSE", message: "Empty bootstrap payload." };
  }
  const requireObject = (value, field) => {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw { code: "MALFORMED_RESPONSE", message: `Bootstrap payload is missing ${field}.` };
    }
    return value;
  };
  const requireString = (value, field) => {
    if (typeof value !== "string" || !value.trim()) {
      throw { code: "MALFORMED_RESPONSE", message: `Bootstrap payload is missing ${field}.` };
    }
    return value.trim();
  };
  const authenticated = Boolean(payload.authenticated);
  const organization = requireObject(payload.organization, "organization");
  const tenant = requireObject(payload.tenant, "tenant");
  const workspace = requireObject(payload.workspace, "workspace");
  const user = requireObject(payload.user, "user");
  const roles = Array.isArray(payload.roles) ? payload.roles : [];
  const permissions = Array.isArray(payload.permissions) ? payload.permissions : [];
  return {
    authenticated,
    user: {
      id: requireString(user.id ?? user.user_id ?? user.username, "user.id"),
      username: requireString(user.username ?? user.id ?? user.user_id, "user.username"),
      email: typeof user.email === "string" ? user.email : "",
      display_name: typeof user.display_name === "string" ? user.display_name : "",
      status: typeof user.status === "string" ? user.status : "ACTIVE",
      email_verified: Boolean(user.email_verified),
      active_role: typeof user.active_role === "string" ? user.active_role : roles[0] || "PLATFORM_ADMIN",
      role_label: typeof user.role_label === "string" ? user.role_label : "",
    },
    organization,
    tenant,
    workspace,
    roles,
    permissions,
    features: payload.features ?? {},
    default_route: payload.default_route || "/novacodepro/dashboard",
    bootstrap_state: payload.bootstrap_state || (authenticated ? "READY" : "UNAUTHENTICATED"),
  };
}
