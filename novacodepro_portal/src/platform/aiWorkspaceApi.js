const DEFAULT_TIMEOUT_MS = 8000;

function normalizePath(baseUrl, path) {
  const root = String(baseUrl || "").replace(/\/$/, "");
  return `${root}${path.startsWith("/") ? path : `/${path}`}`;
}

function randomId(prefix) {
  const token = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);
  return `${prefix}-${token}`;
}

function buildQueryString(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : "";
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
      const headers = {
        accept: "application/json",
        "content-type": body ? "application/json" : undefined,
        "x-requested-with": "fetch",
        "x-correlation-id": correlationId || randomId("corr"),
        "x-idempotency-key": idempotencyKey || randomId("ai"),
        "x-tenant-id": session?.tenant_id || session?.tenant || "",
        "x-organization-id": session?.organization_id || session?.organization || "",
        "x-workspace-id": session?.workspace_id || session?.workspace?.id || "",
        "x-session-id": session?.session_id || session?.sid || "",
        "x-role": session?.active_role || "",
      };
      Object.keys(headers).forEach((key) => {
        if (headers[key] === undefined || headers[key] === null || headers[key] === "") {
          delete headers[key];
        }
      });
      const response = await fetch(normalizePath(baseUrl, path), {
        method,
        credentials: "include",
        headers,
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
  const post = (path, body, idempotencyKey) => request(path, { method: "POST", body, idempotencyKey });

  return {
    request,
    listExecutions: () => safeGet("/v1/novacodepro/ai/executions"),
    createExecution: (payload, idempotencyKey) => post("/v1/novacodepro/ai/executions", payload, idempotencyKey),
    getExecution: (executionId) => safeGet(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}`),
    analyseExecution: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/analyse`, {}),
    listClarifications: (executionId) => safeGet(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/clarifications`),
    answerClarification: (executionId, clarificationId, payload) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/clarifications/${encodeURIComponent(clarificationId)}/answer`, payload),
    completeClarifications: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/clarifications/complete`, {}),
    generateRequirements: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/generate-requirements`, {}),
    generatePlan: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/generate-plan`, {}),
    validatePlan: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/plan/validate`, {}),
    requestApproval: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/request-approval`, {}),
    listApprovals: () => safeGet("/v1/novacodepro/ai/approvals"),
    getApproval: (approvalId) => safeGet(`/v1/novacodepro/ai/approvals/${encodeURIComponent(approvalId)}`),
    approve: (approvalId, payload) => post(`/v1/novacodepro/ai/approvals/${encodeURIComponent(approvalId)}/approve`, payload),
    reject: (approvalId, payload) => post(`/v1/novacodepro/ai/approvals/${encodeURIComponent(approvalId)}/reject`, payload),
    requestChanges: (approvalId, payload) => post(`/v1/novacodepro/ai/approvals/${encodeURIComponent(approvalId)}/request-changes`, payload),
    execute: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/execute`, {}),
    verifyExecution: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/verify`, {}),
    cancelExecution: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/cancel`, {}),
    pauseExecution: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/pause`, {}),
    resumeExecution: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/resume`, {}),
    rollbackExecution: (executionId) => post(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/rollback`, {}),
    getTimeline: (executionId) => safeGet(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/timeline`),
    getEvidence: (executionId) => safeGet(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/evidence`),
    getReplay: (executionId) => safeGet(`/v1/novacodepro/ai/executions/${encodeURIComponent(executionId)}/replay`),
    listAgents: () => safeGet("/v1/novacodepro/ai/agents"),
    getAgent: (agentId) => safeGet(`/v1/novacodepro/ai/agents/${encodeURIComponent(agentId)}`),
    createAgent: (payload) => post("/v1/novacodepro/ai/agents", payload),
    updateAgent: (agentId, payload) => request(`/v1/novacodepro/ai/agents/${encodeURIComponent(agentId)}`, { method: "PATCH", body: payload }),
    addAgentVersion: (agentId, payload) => post(`/v1/novacodepro/ai/agents/${encodeURIComponent(agentId)}/versions`, payload),
    enableAgent: (agentId) => post(`/v1/novacodepro/ai/agents/${encodeURIComponent(agentId)}/enable`, {}),
    disableAgent: (agentId) => post(`/v1/novacodepro/ai/agents/${encodeURIComponent(agentId)}/disable`, {}),
    listTools: () => safeGet("/v1/novacodepro/ai/tools"),
    getTool: (toolId) => safeGet(`/v1/novacodepro/ai/tools/${encodeURIComponent(toolId)}`),
    enableTool: (toolId) => post(`/v1/novacodepro/ai/tools/${encodeURIComponent(toolId)}/enable`, {}),
    disableTool: (toolId) => post(`/v1/novacodepro/ai/tools/${encodeURIComponent(toolId)}/disable`, {}),
    listNotifications: () => safeGet("/v1/novacodepro/ai/notifications"),
    readNotification: (notificationId) => request(`/v1/novacodepro/ai/notifications/${encodeURIComponent(notificationId)}/read`, { method: "PATCH" }),
    readAllNotifications: () => post("/v1/novacodepro/ai/notifications/read-all", {}),
    submitAIRequest: (payload) => post("/v1/novacodepro/ai/requests", payload),
    getAIRequest: (requestId) => safeGet(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}`),
    getPlan: (requestId) => safeGet(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/plan`),
    updateInterpretation: (requestId, payload) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/interpretation`, payload),
    getAgentTask: (agentId) => safeGet(`/v1/novacodepro/ai/agents/${encodeURIComponent(agentId)}`),
    listArtifacts: (projectId) => safeGet(`/v1/novacodepro/ai/projects/${encodeURIComponent(projectId)}/artifacts`),
    getArtifact: (artifactId) => safeGet(`/v1/novacodepro/ai/artifacts/${encodeURIComponent(artifactId)}`),
    requestReview: (requestId, payload) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/review`, payload),
    submitReview: (requestId, payload) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/submit-review`, payload),
    requestApprovalLegacy: (requestId, payload) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/approval`, payload),
    approveLegacy: (requestId, payload) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/approve`, payload),
    rejectLegacy: (requestId, payload) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/reject`, payload),
    requestChangesLegacy: (requestId, payload) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/changes`, payload),
    executeLegacy: (requestId, payload) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/execute`, payload),
    cancelLegacy: (requestId) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/cancel`, {}),
    retryExecution: (requestId) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/retry`, {}),
    verifyLegacy: (requestId) => post(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/verify`, {}),
    getEvidenceLegacy: (requestId) => safeGet(`/v1/novacodepro/ai/requests/${encodeURIComponent(requestId)}/evidence`),
    saveKnowledge: (payload) => post("/v1/novacodepro/ai/knowledge", payload),
    listConversations: (filters = {}) => {
      const query = typeof filters === "string" ? { query: filters } : filters;
      return safeGet(`/v1/novacodepro/ai/conversations${buildQueryString(query)}`);
    },
    getConversation: (conversationId) => safeGet(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}`),
    searchConversations: (query) => safeGet(`/v1/novacodepro/ai/conversations${buildQueryString({ query })}`),
    createConversation: (payload, idempotencyKey) => post("/v1/novacodepro/ai/conversations", payload, idempotencyKey),
    updateConversation: (conversationId, payload) => request(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}`, { method: "PATCH", body: payload }),
    postConversationMessage: (conversationId, payload) =>
      post(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}/messages`, payload),
    getConversationContext: (conversationId) => safeGet(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}/context`),
    updateConversationContext: (conversationId, payload) =>
      request(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}/context`, { method: "PUT", body: payload }),
    getConversationArtifacts: (conversationId) => safeGet(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}/artifacts`),
    getConversationTraceability: (conversationId) => safeGet(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}/traceability`),
    archiveConversation: (conversationId) => post(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}/archive`, {}),
    restoreConversation: (conversationId) => post(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}/restore`, {}),
    deleteConversation: (conversationId) => request(`/v1/novacodepro/ai/conversations/${encodeURIComponent(conversationId)}`, { method: "DELETE" }),
    createNotConnected,
  };
}

export { DEFAULT_TIMEOUT_MS };
