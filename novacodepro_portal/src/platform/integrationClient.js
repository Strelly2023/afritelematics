const DEFAULT_TIMEOUT_MS = 12000;

function randomId(prefix) {
  const token = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);
  return `${prefix}-${token}`;
}

function normalizePath(baseUrl, path) {
  const root = String(baseUrl || "").replace(/\/$/, "");
  return `${root}${path.startsWith("/") ? path : `/${path}`}`;
}

function buildHeaders({ session, correlationId, idempotencyKey, purpose } = {}) {
  const headers = {
    accept: "application/json",
    "x-requested-with": "fetch",
  };
  if (correlationId) {
    headers["x-correlation-id"] = correlationId;
  }
  if (idempotencyKey) {
    headers["x-idempotency-key"] = idempotencyKey;
  }
  if (purpose) {
    headers["x-purpose"] = purpose;
  }
  const tenantId = session?.tenant_id || session?.tenant || session?.organization || "";
  const organizationId = session?.organization_id || session?.organization || tenantId || "";
  if (tenantId) {
    headers["x-tenant-id"] = String(tenantId);
  }
  if (organizationId) {
    headers["x-organization-id"] = String(organizationId);
  }
  if (session?.active_role) {
    headers["x-role"] = String(session.active_role);
  }
  return headers;
}

export function buildIntegrationCacheKey({ productCode, tenantId, resource, resourceId, version = "v1", locale = "" }) {
  return [productCode, tenantId, resource, resourceId, version, locale].filter(Boolean).join(":");
}

async function readPayload(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function normalizeError(error, fallbackCode = "APPLICATION_ERROR") {
  if (error && typeof error === "object" && "code" in error) {
    return error;
  }
  return {
    code: fallbackCode,
    message: error instanceof Error ? error.message : String(error || fallbackCode),
  };
}

function createClientError(response, payload, fallbackCode = "APPLICATION_ERROR") {
  const detail = payload?.detail ?? payload ?? {};
  const code = String(detail.code || response.statusText || fallbackCode).toUpperCase();
  return {
    status: response.status,
    code,
    message: detail.message || detail.error || detail.detail || response.statusText || fallbackCode,
    detail,
  };
}

export function createNovaTechIntegrationClient({ baseUrl = "", session = {}, timeoutMs = DEFAULT_TIMEOUT_MS, fetchImpl = globalThis.fetch } = {}) {
  async function request(path, { method = "GET", body, retrySafe = false, parse = "json", correlationId, idempotencyKey, purpose } = {}) {
    const target = normalizePath(baseUrl, path);
    const controller = new AbortController();
    const timer = globalThis.setTimeout(() => controller.abort(), timeoutMs);
    const headers = buildHeaders({
      session,
      correlationId: correlationId || randomId("corr"),
      idempotencyKey,
      purpose,
    });
    if (body !== undefined && body !== null && method !== "GET") {
      headers["content-type"] = "application/json";
    }
    const execute = async () => {
      const response = await fetchImpl(target, {
        method,
        credentials: "include",
        headers,
        signal: controller.signal,
        body: body === undefined || body === null ? undefined : JSON.stringify(body),
      });
      const payload = await readPayload(response);
      if (!response.ok) {
        throw createClientError(response, payload);
      }
      if (parse === "text") {
        return payload ?? "";
      }
      return payload ?? {};
    };

    try {
      try {
        return await execute();
      } catch (error) {
        if (!retrySafe || controller.signal.aborted) {
          throw error;
        }
        return await execute();
      }
    } catch (error) {
      throw normalizeError(error);
    } finally {
      globalThis.clearTimeout(timer);
    }
  }

  return {
    request,
    safeGet: (path) => request(path, { retrySafe: true }),
    mutation: (path, body, options = {}) =>
      request(path, {
        method: options.method || "POST",
        body,
        retrySafe: false,
        idempotencyKey: options.idempotencyKey || randomId("ncp"),
        correlationId: options.correlationId || randomId("corr"),
        purpose: options.purpose,
      }),
    createQueryKey: (namespace, parts = []) => [namespace, ...parts.map((part) => String(part))].join(":"),
    createIdempotencyKey: () => randomId("ncp"),
    createCorrelationId: () => randomId("corr"),
  };
}
