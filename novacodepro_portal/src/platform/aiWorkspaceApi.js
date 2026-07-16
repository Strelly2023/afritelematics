const DEFAULT_TIMEOUT_MS = 8000;

function normalizePath(baseUrl, path) {
  const root = String(baseUrl || "").replace(/\/$/, "");
  return `${root}${path.startsWith("/") ? path : `/${path}`}`;
}

function randomId(prefix) {
  const token = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);
  return `${prefix}-${token}`;
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

export class NotConnectedError extends Error {
  constructor(message = "AI workspace backend is not connected.") {
    super(message);
    this.name = "NotConnectedError";
    this.code = "NOT_CONNECTED";
  }
}

function createNotConnected(method) {
  return () => {
    throw new NotConnectedError(`${method} is not connected.`);
  };
}

export function createAIWorkspaceClient({ baseUrl = "", session = {}, timeoutMs = DEFAULT_TIMEOUT_MS, connected = false } = {}) {
  async function request(path, { method = "GET", body, correlationId, idempotencyKey } = {}) {
    if (!connected || !baseUrl) {
      throw new NotConnectedError();
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(normalizePath(baseUrl, path), {
        method,
        credentials: "include",
        headers: {
          accept: "application/json",
          "content-type": body ? "application/json" : undefined,
          "x-requested-with": "fetch",
          "x-correlation-id": correlationId || randomId("corr"),
          "x-idempotency-key": idempotencyKey || randomId("ai"),
          "x-tenant-id": session?.tenant_id || session?.tenant || "",
          "x-organization-id": session?.organization_id || session?.organization || "",
          "x-role": session?.active_role || "",
        },
        signal: controller.signal,
        body: body ? JSON.stringify(body) : undefined,
      });
      const payload = await readPayload(response);
      if (!response.ok) {
        throw {
          status: response.status,
          code: String(payload?.detail?.code || response.statusText || "APPLICATION_ERROR").toUpperCase(),
          message: payload?.detail?.message || payload?.message || response.statusText || "Application error",
          detail: payload?.detail || payload,
        };
      }
      return payload ?? {};
    } finally {
      window.clearTimeout(timer);
    }
  }

  const safeGet = (path) => request(path);
  const mutation = (path, body) => request(path, { method: "POST", body });

  return {
    request,
    submitAIRequest: (payload) => mutation("/v1/novacodepro/ai/requests", payload),
    getAIRequest: (requestId) => safeGet(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}`),
    getPlan: (requestId) => safeGet(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/plan`),
    updateInterpretation: (requestId, payload) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/interpretation`, payload),
    listAgents: () => safeGet("/v1/novacodepro/ai/agents"),
    getAgentTask: (agentId) => safeGet(`/v1/novacodepro/ai/agents/${encodeURIComponent(agentId)}`),
    listArtifacts: (projectId) => safeGet(`/v1/novacodepro/ai/projects/${encodeURIComponent(projectId)}/artifacts`),
    getArtifact: (artifactId) => safeGet(`/v1/novacodepro/ai/artifacts/${encodeURIComponent(artifactId)}`),
    requestReview: (requestId, payload) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/review`, payload),
    submitReview: (requestId, payload) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/submit-review`, payload),
    requestApproval: (requestId, payload) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/approval`, payload),
    approve: (requestId, payload) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/approve`, payload),
    reject: (requestId, payload) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/reject`, payload),
    requestChanges: (requestId, payload) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/changes`, payload),
    execute: (requestId, payload) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/execute`, payload),
    cancelExecution: (requestId) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/cancel`, {}),
    retryExecution: (requestId) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/retry`, {}),
    verifyExecution: (requestId) => mutation(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/verify`, {}),
    getEvidence: (requestId) => safeGet(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/evidence`),
    saveKnowledge: (payload) => mutation("/v1/novacodepro/ai/knowledge", payload),
    listConversations: () => safeGet("/v1/novacodepro/ai/conversations"),
    getConversation: (conversationId) => safeGet(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}`),
    searchConversations: (query) => safeGet(`/v1/novacodepro/ai/conversations?query=${encodeURIComponent(query)}`),
    createNotConnected,
  };
}

export { DEFAULT_TIMEOUT_MS };
