const DEFAULT_TIMEOUT_MS = 10000;

function normalizePath(baseUrl, path) {
  const base = String(baseUrl || "").replace(/\/+$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}

async function readPayload(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

function createRequestError(response, payload) {
  const detail = payload?.detail || payload?.error || {};
  const code = typeof detail === "object" && detail !== null ? detail.code || detail.detail || detail.message : detail || response.statusText;
  const message = typeof detail === "object" && detail !== null ? detail.message || detail.code || response.statusText : String(detail || response.statusText);
  return { code: code || `HTTP_${response.status}`, message, status: response.status, retryable: response.status >= 500, details: detail };
}

function normalizeError(error, fallbackCode = "NCP006A_REQUEST_FAILED") {
  if (error && typeof error === "object" && error.code) {
    return error;
  }
  return {
    code: fallbackCode,
    message: error instanceof Error ? error.message : String(error || fallbackCode),
  };
}

export function createNovaCodeProNcp006aApi({ baseUrl = "", fetchImpl = fetch } = {}) {
  async function request(path, { method = "GET", body, headers = {}, signal } = {}) {
    const controller = new AbortController();
    const timeoutHandle = globalThis.setTimeout(() => controller.abort("timeout"), DEFAULT_TIMEOUT_MS);
    const onAbort = () => controller.abort(signal.reason);
    if (signal) {
      if (signal.aborted) controller.abort(signal.reason);
      else signal.addEventListener("abort", onAbort, { once: true });
    }
    try {
      const response = await fetchImpl(normalizePath(baseUrl, path), {
        method,
        credentials: "include",
        signal: controller.signal,
        headers: {
          "content-type": "application/json",
          ...headers,
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const payload = await readPayload(response);
      if (!response.ok) {
        throw createRequestError(response, payload);
      }
      return payload;
    } catch (error) {
      throw normalizeError(error);
    } finally {
      globalThis.clearTimeout(timeoutHandle);
      if (signal) signal.removeEventListener("abort", onAbort);
    }
  }

  const api = {
    request,
    listWorkspaces: (signal) => request("/v1/novacodepro/architecture/workspaces", { signal }).then((body) => body?.workspaces || []),
    createWorkspace: (payload) => request("/v1/novacodepro/architecture/workspaces", { method: "POST", body: payload }),
    getWorkspace: (workspaceId, signal) => request(`/v1/novacodepro/architecture/workspaces/${encodeURIComponent(workspaceId)}`, { signal }),
    updateWorkspace: (workspaceId, payload) => request(`/v1/novacodepro/architecture/workspaces/${encodeURIComponent(workspaceId)}`, { method: "PATCH", body: payload }),
    selectWorkspace: (workspaceId) => request(`/v1/novacodepro/architecture/workspaces/${encodeURIComponent(workspaceId)}/select`, { method: "POST", body: {} }),
    listModels: (workspaceId, signal) => request(`/v1/novacodepro/architecture/models${workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : ""}`, { signal }).then((body) => body?.models || []),
    createModel: (payload) => request("/v1/novacodepro/architecture/models", { method: "POST", body: payload }),
    getModel: (modelId, signal) => request(`/v1/novacodepro/architecture/models/${encodeURIComponent(modelId)}`, { signal }),
    updateModel: (modelId, payload) => request(`/v1/novacodepro/architecture/models/${encodeURIComponent(modelId)}`, { method: "PATCH", body: payload }),
    archiveModel: (modelId) => request(`/v1/novacodepro/architecture/models/${encodeURIComponent(modelId)}/archive`, { method: "POST", body: {} }),
    listModelVersions: (modelId, signal) => request(`/v1/novacodepro/architecture/models/${encodeURIComponent(modelId)}/versions`, { signal }).then((body) => body?.versions || []),
    getModelVersion: (modelId, versionId, signal) => request(`/v1/novacodepro/architecture/models/${encodeURIComponent(modelId)}/versions/${encodeURIComponent(versionId)}`, { signal }),
    draftFromAIExecution: (executionId, payload) => request(`/v1/novacodepro/architecture/models/from-ai-execution/${encodeURIComponent(executionId)}`, { method: "POST", body: payload }),
    listComponents: (modelId, signal) => request(`/v1/novacodepro/architecture/components?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.components || []),
    createComponent: (payload) => request("/v1/novacodepro/architecture/components", { method: "POST", body: payload }),
    updateComponent: (componentId, payload) => request(`/v1/novacodepro/architecture/components/${encodeURIComponent(componentId)}`, { method: "PATCH", body: payload }),
    listInterfaces: (modelId, signal) => request(`/v1/novacodepro/architecture/interfaces?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.interfaces || []),
    createInterface: (payload) => request("/v1/novacodepro/architecture/interfaces", { method: "POST", body: payload }),
    updateInterface: (interfaceId, payload) => request(`/v1/novacodepro/architecture/interfaces/${encodeURIComponent(interfaceId)}`, { method: "PATCH", body: payload }),
    listData: (modelId, signal) => request(`/v1/novacodepro/architecture/data?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.data || []),
    createData: (payload) => request("/v1/novacodepro/architecture/data", { method: "POST", body: payload }),
    updateData: (dataId, payload) => request(`/v1/novacodepro/architecture/data/${encodeURIComponent(dataId)}`, { method: "PATCH", body: payload }),
    listSecurity: (modelId, signal) => request(`/v1/novacodepro/architecture/security?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.security || []),
    createSecurity: (payload) => request("/v1/novacodepro/architecture/security", { method: "POST", body: payload }),
    updateSecurity: (securityId, payload) => request(`/v1/novacodepro/architecture/security/${encodeURIComponent(securityId)}`, { method: "PATCH", body: payload }),
    listDeployments: (modelId, signal) => request(`/v1/novacodepro/architecture/deployments?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.deployments || []),
    createDeployment: (payload) => request("/v1/novacodepro/architecture/deployments", { method: "POST", body: payload }),
    updateDeployment: (deploymentId, payload) => request(`/v1/novacodepro/architecture/deployments/${encodeURIComponent(deploymentId)}`, { method: "PATCH", body: payload }),
    listReviews: (modelId, signal) => request(`/v1/novacodepro/architecture/reviews?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.reviews || []),
    createReview: (payload) => request("/v1/novacodepro/architecture/reviews", { method: "POST", body: payload }),
    completeReview: (reviewId, payload) => request(`/v1/novacodepro/architecture/reviews/${encodeURIComponent(reviewId)}/complete`, { method: "POST", body: payload }),
    listApprovals: (modelId, signal) => request(`/v1/novacodepro/architecture/approvals?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.approvals || []),
    requestApproval: (payload) => request("/v1/novacodepro/architecture/approvals", { method: "POST", body: payload }),
    approveApproval: (approvalId, payload) => request(`/v1/novacodepro/architecture/approvals/${encodeURIComponent(approvalId)}/approve`, { method: "POST", body: payload }),
    rejectApproval: (approvalId, payload) => request(`/v1/novacodepro/architecture/approvals/${encodeURIComponent(approvalId)}/reject`, { method: "POST", body: payload }),
    requestApprovalChanges: (approvalId, payload) => request(`/v1/novacodepro/architecture/approvals/${encodeURIComponent(approvalId)}/request-changes`, { method: "POST", body: payload }),
    listBaselines: (modelId, signal) => request(`/v1/novacodepro/architecture/baselines?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.baselines || []),
    createBaseline: (payload) => request("/v1/novacodepro/architecture/baselines", { method: "POST", body: payload }),
    approveBaseline: (modelId, baselineId, payload) => request(`/v1/novacodepro/architecture/baselines/${encodeURIComponent(baselineId)}/approve?model_id=${encodeURIComponent(modelId)}`, { method: "POST", body: payload }),
    activateBaseline: (modelId, baselineId) => request(`/v1/novacodepro/architecture/baselines/${encodeURIComponent(baselineId)}/activate?model_id=${encodeURIComponent(modelId)}`, { method: "POST", body: {} }),
    supersedeBaseline: (modelId, baselineId) => request(`/v1/novacodepro/architecture/baselines/${encodeURIComponent(baselineId)}/supersede?model_id=${encodeURIComponent(modelId)}`, { method: "POST", body: {} }),
    listValidationResults: (modelId, signal) => request(`/v1/novacodepro/architecture/validation?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.validation_results || []),
    validateModel: (modelId, payload) => request(`/v1/novacodepro/architecture/validation?model_id=${encodeURIComponent(modelId)}`, { method: "POST", body: payload }),
    listFitnessFunctions: (modelId, signal) => request(`/v1/novacodepro/architecture/fitness?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.fitness || []),
    evaluateFitness: (modelId) => request(`/v1/novacodepro/architecture/fitness?model_id=${encodeURIComponent(modelId)}`, { method: "POST", body: {} }),
    listDiagrams: (modelId, signal) => request(`/v1/novacodepro/architecture/diagrams?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.diagrams || []),
    createDiagram: (modelId, payload) => request(`/v1/novacodepro/architecture/diagrams?model_id=${encodeURIComponent(modelId)}`, { method: "POST", body: payload }),
    listImpact: (modelId, signal) => request(`/v1/novacodepro/architecture/impact?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.impact || []),
    calculateImpact: (modelId) => request(`/v1/novacodepro/architecture/impact?model_id=${encodeURIComponent(modelId)}`, { method: "POST", body: {} }),
    listTraceabilityLinks: (modelId, signal) => request(`/v1/novacodepro/architecture/traceability/links?model_id=${encodeURIComponent(modelId)}`, { signal }).then((body) => body?.links || []),
    calculateTraceabilityCoverage: (modelId, signal) => request(`/v1/novacodepro/architecture/traceability/coverage?model_id=${encodeURIComponent(modelId)}`, { signal }),
  };

  return api;
}
