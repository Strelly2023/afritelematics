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

function normalizeError(error, fallbackCode = "NCP007_REQUEST_FAILED") {
  if (error && typeof error === "object" && error.code) return error;
  return { code: fallbackCode, message: error instanceof Error ? error.message : String(error || fallbackCode) };
}

export function createNovaCodeProNcp007Api({ baseUrl = "", fetchImpl = fetch } = {}) {
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
      if (!response.ok) throw createRequestError(response, payload);
      return payload;
    } catch (error) {
      throw normalizeError(error);
    } finally {
      globalThis.clearTimeout(timeoutHandle);
      if (signal) signal.removeEventListener("abort", onAbort);
    }
  }

  const collection = (path, key) => ({
    list: (signal) => request(path, { signal }).then((body) => body?.[key] || []),
    create: (payload, idempotencyKey) =>
      request(path, {
        method: "POST",
        body: payload,
        headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
      }),
    get: (resourceId, signal) => request(`${path}/${encodeURIComponent(resourceId)}`, { signal }),
    update: (resourceId, payload) => request(`${path}/${encodeURIComponent(resourceId)}`, { method: "PATCH", body: payload }),
  });

  const workspaces = collection("/api/v1/development/workspaces", "workspaces");
  const sessions = collection("/api/v1/development/sessions", "sessions");
  const tasks = collection("/api/v1/development/tasks", "tasks");
  const changeSets = collection("/api/v1/development/change-sets", "change_sets");
  const approvals = collection("/api/v1/development/approvals", "approvals");

  return {
    request,
    listWorkspaces: (signal) => workspaces.list(signal),
    createWorkspace: (payload) => workspaces.create(payload),
    getWorkspace: workspaces.get,
    updateWorkspace: workspaces.update,
    archiveWorkspace: (workspaceId) => request(`/api/v1/development/workspaces/${encodeURIComponent(workspaceId)}/archive`, { method: "POST", body: {} }),
    restoreWorkspace: (workspaceId) => request(`/api/v1/development/workspaces/${encodeURIComponent(workspaceId)}/restore`, { method: "POST", body: {} }),
    getWorkspaceSummary: (workspaceId, signal) => request(`/api/v1/development/workspaces/${encodeURIComponent(workspaceId)}/summary`, { signal }),
    selectWorkspace: (workspaceId) => request(`/api/v1/development/workspaces/${encodeURIComponent(workspaceId)}/select`, { method: "POST", body: {} }),
    repositoryTree: (workspaceId, path = ".", signal) => request(`/api/v1/development/workspaces/${encodeURIComponent(workspaceId)}/repository/tree?path=${encodeURIComponent(path)}`, { signal }),
    repositoryFile: (workspaceId, path, signal) => request(`/api/v1/development/workspaces/${encodeURIComponent(workspaceId)}/repository/file?path=${encodeURIComponent(path)}`, { signal }),
    repositorySearch: (workspaceId, query, path = "", signal) => request(`/api/v1/development/workspaces/${encodeURIComponent(workspaceId)}/repository/search?query=${encodeURIComponent(query)}${path ? `&path=${encodeURIComponent(path)}` : ""}`, { signal }),
    repositoryStatus: (workspaceId, signal) => request(`/api/v1/development/workspaces/${encodeURIComponent(workspaceId)}/repository/status`, { signal }),
    repositoryDiff: (workspaceId, signal) => request(`/api/v1/development/workspaces/${encodeURIComponent(workspaceId)}/repository/diff`, { signal }),
    createSession: (workspaceId, payload) => sessions.create({ workspace_id: workspaceId, ...payload }),
    getSession: sessions.get,
    completeSession: (sessionId) => request(`/api/v1/development/sessions/${encodeURIComponent(sessionId)}/complete`, { method: "POST", body: {} }),
    cancelSession: (sessionId) => request(`/api/v1/development/sessions/${encodeURIComponent(sessionId)}/cancel`, { method: "POST", body: {} }),
    listSessionTasks: (sessionId, signal) => request(`/api/v1/development/sessions/${encodeURIComponent(sessionId)}/tasks`, { signal }).then((body) => body?.tasks || []),
    createTask: (sessionId, payload) => request(`/api/v1/development/sessions/${encodeURIComponent(sessionId)}/tasks`, { method: "POST", body: payload }),
    updateTask: tasks.update,
    generateTask: (taskId, payload, idempotencyKey) =>
      request(`/api/v1/development/tasks/${encodeURIComponent(taskId)}/generate`, {
        method: "POST",
        body: payload,
        headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
      }),
    getGenerationRequest: (requestId, signal) => request(`/api/v1/development/generation-requests/${encodeURIComponent(requestId)}`, { signal }),
    retryGenerationRequest: (requestId) => request(`/api/v1/development/generation-requests/${encodeURIComponent(requestId)}/retry`, { method: "POST", body: {} }),
    cancelGenerationRequest: (requestId) => request(`/api/v1/development/generation-requests/${encodeURIComponent(requestId)}/cancel`, { method: "POST", body: {} }),
    getChangeSet: changeSets.get,
    listChangeSetFiles: (changeSetId, signal) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/files`, { signal }).then((body) => body?.files || []),
    getChangeSetDiff: (changeSetId, signal) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/diff`, { signal }),
    dryRunChangeSet: (changeSetId) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/dry-run`, { method: "POST", body: {} }),
    applyChangeSet: (changeSetId) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/apply`, { method: "POST", body: {} }),
    revertChangeSet: (changeSetId) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/revert`, { method: "POST", body: {} }),
    rejectChangeSet: (changeSetId) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/reject`, { method: "POST", body: {} }),
    createValidation: (changeSetId, payload) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/validations`, { method: "POST", body: payload }),
    listValidationRuns: (changeSetId, signal) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/validations`, { signal }).then((body) => body?.validation_runs || []),
    getValidationRun: (validationRunId, signal) => request(`/api/v1/development/validation-runs/${encodeURIComponent(validationRunId)}`, { signal }),
    cancelValidationRun: (validationRunId) => request(`/api/v1/development/validation-runs/${encodeURIComponent(validationRunId)}/cancel`, { method: "POST", body: {} }),
    createReview: (changeSetId, payload) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/reviews`, { method: "POST", body: payload }),
    listReviews: (changeSetId, signal) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/reviews`, { signal }).then((body) => body?.reviews || []),
    addReviewComment: (reviewId, payload) => request(`/api/v1/development/reviews/${encodeURIComponent(reviewId)}/comments`, { method: "POST", body: payload }),
    updateReviewComment: (commentId, payload) => request(`/api/v1/development/review-comments/${encodeURIComponent(commentId)}`, { method: "PATCH", body: payload }),
    approveReview: (reviewId) => request(`/api/v1/development/reviews/${encodeURIComponent(reviewId)}/approve`, { method: "POST", body: {} }),
    requestReviewChanges: (reviewId) => request(`/api/v1/development/reviews/${encodeURIComponent(reviewId)}/request-changes`, { method: "POST", body: {} }),
    rejectReview: (reviewId) => request(`/api/v1/development/reviews/${encodeURIComponent(reviewId)}/reject`, { method: "POST", body: {} }),
    requestApproval: (changeSetId, payload) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/approval-requests`, { method: "POST", body: payload }),
    listApprovals: (changeSetId, signal) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/approvals`, { signal }).then((body) => body?.approvals || []),
    getApproval: (approvalId, signal) => request(`/api/v1/development/approvals/${encodeURIComponent(approvalId)}`, { signal }),
    approveApproval: (approvalId, payload) => request(`/api/v1/development/approvals/${encodeURIComponent(approvalId)}/approve`, { method: "POST", body: payload }),
    rejectApproval: (approvalId, payload) => request(`/api/v1/development/approvals/${encodeURIComponent(approvalId)}/reject`, { method: "POST", body: payload }),
    createCommitProposal: (changeSetId, payload) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/commit-proposals`, { method: "POST", body: payload }),
    getCommitProposal: (proposalId, signal) => request(`/api/v1/development/commit-proposals/${encodeURIComponent(proposalId)}`, { signal }),
    executeCommitProposal: (proposalId) => request(`/api/v1/development/commit-proposals/${encodeURIComponent(proposalId)}/execute`, { method: "POST", body: {} }),
    createPullRequestProposal: (changeSetId, payload) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/pull-request-proposals`, { method: "POST", body: payload }),
    executePullRequestProposal: (proposalId) => request(`/api/v1/development/pull-request-proposals/${encodeURIComponent(proposalId)}/execute`, { method: "POST", body: {} }),
    getTimeline: (sessionId, signal) => request(`/api/v1/development/sessions/${encodeURIComponent(sessionId)}/timeline`, { signal }).then((body) => body?.events || []),
    getEvidence: (changeSetId, signal) => request(`/api/v1/development/change-sets/${encodeURIComponent(changeSetId)}/evidence`, { signal }).then((body) => body?.evidence || []),
    executeCommand: (sessionId, payload) => request(`/api/v1/development/sessions/${encodeURIComponent(sessionId)}/commands`, { method: "POST", body: payload }),
    getCommandExecution: (executionId, signal) => request(`/api/v1/development/command-executions/${encodeURIComponent(executionId)}`, { signal }),
  };
}
