const DEFAULT_TIMEOUT_MS = 10000;

function normalizeError(error, fallbackCode = "NCP003_REQUEST_FAILED") {
  if (error && typeof error === "object" && error.code) {
    return error;
  }
  if (error?.name === "AbortError") {
    return { code: "timeout", message: "The request timed out. Try again.", retryable: true };
  }
  if (error instanceof TypeError) {
    return { code: "network_unavailable", message: "NovaCodePro services cannot be reached right now.", retryable: true };
  }
  return { code: fallbackCode, message: error instanceof Error && error.message ? error.message : "NovaCodePro could not complete this request.", retryable: true };
}

async function readPayload(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

function normalizePath(baseUrl, path) {
  const base = String(baseUrl || "").replace(/\/+$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}

function createRequestError(response, payload) {
  const detail = payload?.detail || payload?.error || {};
  const code = typeof detail === "object" && detail !== null ? detail.code || detail.detail || detail.message : detail || response.statusText;
  const message = typeof detail === "object" && detail !== null ? detail.message || detail.code || response.statusText : String(detail || response.statusText);
  return {
    code: code || `HTTP_${response.status}`,
    message,
    status: response.status,
    retryable: response.status >= 500,
    details: detail,
  };
}

export function classifyNcp003RouteState(error) {
  if (!error) return "error";
  if (error.status === 401 || ["session_required", "session_expired", "token_revoked"].includes(error.code)) return "unauthorized";
  if (error.status === 403) return "forbidden";
  if (error.status === 409 && String(error.code).includes("workspace")) return "workspace_required";
  if (error.status === 404) return "not_found";
  if (["timeout", "network_unavailable", "service_unavailable"].includes(error.code) || error.status >= 500 || error.retryable) return "service_unavailable";
  return "error";
}

export function createNovaCodeProNcp003Api({ baseUrl = "", fetchImpl = fetch } = {}) {
  async function request(path, { method = "GET", body, headers = {}, signal } = {}) {
    const controller = new AbortController();
    const timeoutHandle = globalThis.setTimeout(() => controller.abort("timeout"), DEFAULT_TIMEOUT_MS);
    const onAbort = () => controller.abort(signal.reason);
    if (signal) {
      if (signal.aborted) {
        controller.abort(signal.reason);
      } else {
        signal.addEventListener("abort", onAbort, { once: true });
      }
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
      if (signal) {
        signal.removeEventListener("abort", onAbort);
      }
    }
  }

  const api = {
    request,
    listWorkspaces: (signal) => request("/v1/novacodepro/workspaces", { signal }).then((body) => body?.workspaces || []),
    createWorkspace: (payload) => request("/v1/novacodepro/workspaces", { method: "POST", body: payload }),
    getWorkspace: (workspaceId, signal) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}`, { signal }),
    updateWorkspace: (workspaceId, payload) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}`, { method: "PATCH", body: payload }),
    selectWorkspace: (workspaceId) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/select`, { method: "POST", body: {} }),
    listWorkspaceMembers: (workspaceId, signal) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/members`, { signal }).then((body) => body?.members || []),
    addWorkspaceMember: (workspaceId, payload) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/members`, { method: "POST", body: payload }),
    removeWorkspaceMember: (workspaceId, memberId) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/members/${encodeURIComponent(memberId)}`, { method: "DELETE" }),
    listWorkspaceActivity: (workspaceId, signal) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/activity`, { signal }).then((body) => body?.activity || []),
    listWorkspaceTasks: (workspaceId, signal) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/tasks`, { signal }).then((body) => body?.tasks || []),
    listWorkspaceApprovals: (workspaceId, signal) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/approvals`, { signal }).then((body) => body?.approvals || []),
    listWorkspaceFavorites: (workspaceId, signal) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/favorites`, { signal }).then((body) => body?.favorites || []),
    addWorkspaceFavorite: (workspaceId, payload) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/favorites`, { method: "POST", body: payload }),
    removeWorkspaceFavorite: (workspaceId, favoriteId) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/favorites/${encodeURIComponent(favoriteId)}`, { method: "DELETE" }),
    listWorkspaceNotifications: (workspaceId, signal) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/notifications`, { signal }).then((body) => body?.notifications || []),
    updateWorkspaceSettings: (workspaceId, payload) => request(`/v1/novacodepro/workspaces/${encodeURIComponent(workspaceId)}/settings`, { method: "PATCH", body: payload }),
    listProjects: (workspaceId, signal) => request(`/v1/novacodepro/projects${workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : ""}`, { signal }).then((body) => body?.projects || []),
    createProject: (payload, idempotencyKey) =>
      request("/v1/novacodepro/projects", {
        method: "POST",
        body: payload,
        headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
      }),
    getProject: (projectId, signal) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}`, { signal }),
    updateProject: (projectId, payload) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}`, { method: "PATCH", body: payload }),
    archiveProject: (projectId) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/archive`, { method: "POST", body: {} }),
    restoreProject: (projectId) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/restore`, { method: "POST", body: {} }),
    listProjectActivity: (projectId, signal) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/activity`, { signal }).then((body) => body?.activity || []),
    listProjectMembers: (projectId, signal) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/members`, { signal }).then((body) => body?.members || []),
    addProjectMember: (projectId, payload) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/members`, { method: "POST", body: payload }),
    removeProjectMember: (projectId, memberId) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(memberId)}`, { method: "DELETE" }),
    listProjectMilestones: (projectId, signal) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/milestones`, { signal }).then((body) => body?.milestones || []),
    createProjectMilestone: (projectId, payload) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/milestones`, { method: "POST", body: payload }),
    getProjectMilestone: (projectId, milestoneId, signal) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/milestones/${encodeURIComponent(milestoneId)}`, { signal }),
    updateProjectMilestone: (projectId, milestoneId, payload) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/milestones/${encodeURIComponent(milestoneId)}`, { method: "PATCH", body: payload }),
    deleteProjectMilestone: (projectId, milestoneId) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/milestones/${encodeURIComponent(milestoneId)}`, { method: "DELETE" }),
    listProjectWorkItems: (projectId, signal) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/work-items`, { signal }).then((body) => body?.work_items || []),
    createProjectWorkItem: (projectId, payload) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/work-items`, { method: "POST", body: payload }),
    getProjectWorkItem: (projectId, workItemId, signal) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/work-items/${encodeURIComponent(workItemId)}`, { signal }),
    updateProjectWorkItem: (projectId, workItemId, payload) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/work-items/${encodeURIComponent(workItemId)}`, { method: "PATCH", body: payload }),
    assignProjectWorkItem: (projectId, workItemId, payload) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/work-items/${encodeURIComponent(workItemId)}/assign`, { method: "POST", body: payload }),
    transitionProjectWorkItem: (projectId, workItemId, payload) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/work-items/${encodeURIComponent(workItemId)}/transition`, { method: "POST", body: payload }),
    deleteProjectWorkItem: (projectId, workItemId) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/work-items/${encodeURIComponent(workItemId)}`, { method: "DELETE" }),
    listProjectRisks: (projectId, signal) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/risks`, { signal }).then((body) => body?.risks || []),
    createProjectRisk: (projectId, payload) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/risks`, { method: "POST", body: payload }),
    updateProjectRisk: (projectId, riskId, payload) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/risks/${encodeURIComponent(riskId)}`, { method: "PATCH", body: payload }),
    getProjectRoadmap: (projectId, signal) => request(`/v1/novacodepro/projects/${encodeURIComponent(projectId)}/roadmap`, { signal }),
    listRequests: (workspaceId, signal) => request(`/v1/novacodepro/requests${workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : ""}`, { signal }).then((body) => body?.requests || []),
    createRequest: (payload, idempotencyKey) =>
      request("/v1/novacodepro/requests", {
        method: "POST",
        body: payload,
        headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
      }),
    getRequest: (requestId, signal) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}`, { signal }),
    updateRequest: (requestId, payload) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}`, { method: "PATCH", body: payload }),
    submitRequest: (requestId) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/submit`, { method: "POST", body: {} }),
    transitionRequest: (requestId, payload) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/transition`, { method: "POST", body: payload }),
    archiveRequest: (requestId) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/archive`, { method: "POST", body: {} }),
    getRequestHistory: (requestId, signal) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/history`, { signal }).then((body) => body?.history || []),
    listRequestAssignments: (requestId, signal) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/assignments`, { signal }).then((body) => body?.assignments || []),
    addRequestAssignment: (requestId, payload) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/assignments`, { method: "POST", body: payload }),
    removeRequestAssignment: (requestId, assignmentId) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/assignments/${encodeURIComponent(assignmentId)}`, { method: "DELETE" }),
    listRequestComments: (requestId, signal) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/comments`, { signal }).then((body) => body?.comments || []),
    addRequestComment: (requestId, payload) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/comments`, { method: "POST", body: payload }),
    updateRequestComment: (requestId, commentId, payload) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/comments/${encodeURIComponent(commentId)}`, { method: "PATCH", body: payload }),
    deleteRequestComment: (requestId, commentId) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/comments/${encodeURIComponent(commentId)}`, { method: "DELETE" }),
    listRequestAttachments: (requestId, signal) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/attachments`, { signal }).then((body) => body?.attachments || []),
    addRequestAttachment: (requestId, payload) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/attachments`, { method: "POST", body: payload }),
    getRequestAttachment: (requestId, attachmentId, signal) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/attachments/${encodeURIComponent(attachmentId)}`, { signal }),
    deleteRequestAttachment: (requestId, attachmentId) => request(`/v1/novacodepro/requests/${encodeURIComponent(requestId)}/attachments/${encodeURIComponent(attachmentId)}`, { method: "DELETE" }),
    listNotifications: (signal) => request("/v1/novacodepro/notifications", { signal }).then((body) => body?.notifications || []),
    markNotificationRead: (notificationId) => request(`/v1/novacodepro/notifications/${encodeURIComponent(notificationId)}/read`, { method: "PATCH", body: {} }),
    markAllNotificationsRead: () => request("/v1/novacodepro/notifications/read-all", { method: "POST", body: {} }),
  };

  return api;
}
