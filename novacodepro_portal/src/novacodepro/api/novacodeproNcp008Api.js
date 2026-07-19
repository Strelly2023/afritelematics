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

function normalizeError(error, fallbackCode = "NCP008_REQUEST_FAILED") {
  if (error && typeof error === "object" && error.code) return error;
  return { code: fallbackCode, message: error instanceof Error ? error.message : String(error || fallbackCode) };
}

export function createNovaCodeProNcp008Api({ baseUrl = "", fetchImpl = fetch } = {}) {
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

  const workspaces = collection("/api/v1/operations/workspaces", "workspaces");
  const environments = collection("/api/v1/operations/environments", "environments");
  const services = collection("/api/v1/operations/services", "services");
  const deployments = collection("/api/v1/operations/deployments", "deployments");
  const alerts = collection("/api/v1/operations/alerts", "alerts");
  const incidents = collection("/api/v1/operations/incidents", "incidents");
  const actions = collection("/api/v1/operations/actions", "actions");
  const slos = collection("/api/v1/operations/slos", "slos");
  const recoveryPlans = collection("/api/v1/operations/recovery-plans", "recovery_plans");
  const reviews = collection("/api/v1/operations/post-incident-reviews", "post_incident_reviews");

  return {
    request,
    overview: () => request("/api/v1/operations/overview"),
    activity: () => request("/api/v1/operations/activity"),
    risk: () => request("/api/v1/operations/risk"),
    readiness: () => request("/api/v1/operations/readiness"),
    listWorkspaces: workspaces.list,
    createWorkspace: workspaces.create,
    getWorkspace: workspaces.get,
    updateWorkspace: workspaces.update,
    selectWorkspace: (workspaceId) => request(`/api/v1/operations/workspaces/${encodeURIComponent(workspaceId)}/select`, { method: "POST", body: {} }),
    archiveWorkspace: (workspaceId) => request(`/api/v1/operations/workspaces/${encodeURIComponent(workspaceId)}/archive`, { method: "POST", body: {} }),
    getWorkspaceSummary: (workspaceId, signal) => request(`/api/v1/operations/workspaces/${encodeURIComponent(workspaceId)}/summary`, { signal }),
    listEnvironments: environments.list,
    createEnvironment: environments.create,
    getEnvironment: environments.get,
    updateEnvironment: environments.update,
    transitionEnvironment: (environmentId, payload) => request(`/api/v1/operations/environments/${encodeURIComponent(environmentId)}/transition`, { method: "POST", body: payload }),
    freezeEnvironment: (environmentId) => request(`/api/v1/operations/environments/${encodeURIComponent(environmentId)}/freeze`, { method: "POST", body: {} }),
    unfreezeEnvironment: (environmentId) => request(`/api/v1/operations/environments/${encodeURIComponent(environmentId)}/unfreeze`, { method: "POST", body: {} }),
    listServices: services.list,
    createService: services.create,
    getService: services.get,
    updateService: services.update,
    getServiceHealth: (serviceId, signal) => request(`/api/v1/operations/services/${encodeURIComponent(serviceId)}/health`, { signal }),
    getServiceDependencies: (serviceId, signal) => request(`/api/v1/operations/services/${encodeURIComponent(serviceId)}/dependencies`, { signal }),
    getServiceDeployments: (serviceId, signal) => request(`/api/v1/operations/services/${encodeURIComponent(serviceId)}/deployments`, { signal }).then((body) => body?.deployments || []),
    getServiceMetrics: (serviceId, signal) => request(`/api/v1/operations/services/${encodeURIComponent(serviceId)}/metrics`, { signal }),
    getServiceLogs: (serviceId, signal) => request(`/api/v1/operations/services/${encodeURIComponent(serviceId)}/logs`, { signal }),
    getServiceTraces: (serviceId, signal) => request(`/api/v1/operations/services/${encodeURIComponent(serviceId)}/traces`, { signal }),
    listDeployments: deployments.list,
    getDeployment: deployments.get,
    getDeploymentEvidence: (deploymentId, signal) => request(`/api/v1/operations/deployments/${encodeURIComponent(deploymentId)}/evidence`, { signal }).then((body) => body?.evidence || []),
    requestDeploymentRollback: (deploymentId, payload) => request(`/api/v1/operations/deployments/${encodeURIComponent(deploymentId)}/rollback-requests`, { method: "POST", body: payload }),
    getDeploymentVerification: (deploymentId, signal) => request(`/api/v1/operations/deployments/${encodeURIComponent(deploymentId)}/verification`, { signal }),
    listAlerts: alerts.list,
    createAlert: alerts.create,
    getAlert: alerts.get,
    updateAlert: alerts.update,
    acknowledgeAlert: (alertId, payload) => request(`/api/v1/operations/alerts/${encodeURIComponent(alertId)}/acknowledge`, { method: "POST", body: payload }),
    resolveAlert: (alertId, payload) => request(`/api/v1/operations/alerts/${encodeURIComponent(alertId)}/resolve`, { method: "POST", body: payload }),
    alertToIncident: (alertId, payload) => request(`/api/v1/operations/alerts/${encodeURIComponent(alertId)}/incident`, { method: "POST", body: payload }),
    listIncidents: incidents.list,
    createIncident: incidents.create,
    getIncident: incidents.get,
    updateIncident: incidents.update,
    transitionIncident: (incidentId, payload) => request(`/api/v1/operations/incidents/${encodeURIComponent(incidentId)}/transition`, { method: "POST", body: payload }),
    addIncidentTimelineEvent: (incidentId, payload) => request(`/api/v1/operations/incidents/${encodeURIComponent(incidentId)}/timeline`, { method: "POST", body: payload }),
    getIncidentTimeline: (incidentId, signal) => request(`/api/v1/operations/incidents/${encodeURIComponent(incidentId)}/timeline`, { signal }).then((body) => body?.timeline || []),
    getIncidentEvidence: (incidentId, signal) => request(`/api/v1/operations/incidents/${encodeURIComponent(incidentId)}/evidence`, { signal }).then((body) => body?.evidence || []),
    createIncidentReview: (incidentId, payload) => request(`/api/v1/operations/incidents/${encodeURIComponent(incidentId)}/post-incident-reviews`, { method: "POST", body: payload }),
    listActions: actions.list,
    createAction: actions.create,
    getAction: actions.get,
    evaluateAction: (actionId, payload) => request(`/api/v1/operations/actions/${encodeURIComponent(actionId)}/evaluate`, { method: "POST", body: payload }),
    requestActionApproval: (actionId) => request(`/api/v1/operations/actions/${encodeURIComponent(actionId)}/approval-requests`, { method: "POST", body: {} }),
    approveAction: (actionId, payload) => request(`/api/v1/operations/actions/${encodeURIComponent(actionId)}/approve`, { method: "POST", body: payload }),
    rejectAction: (actionId, payload) => request(`/api/v1/operations/actions/${encodeURIComponent(actionId)}/reject`, { method: "POST", body: payload }),
    executeAction: (actionId) => request(`/api/v1/operations/actions/${encodeURIComponent(actionId)}/execute`, { method: "POST", body: {} }),
    verifyAction: (actionId) => request(`/api/v1/operations/actions/${encodeURIComponent(actionId)}/verify`, { method: "POST", body: {} }),
    cancelAction: (actionId) => request(`/api/v1/operations/actions/${encodeURIComponent(actionId)}/cancel`, { method: "POST", body: {} }),
    rollbackAction: (actionId) => request(`/api/v1/operations/actions/${encodeURIComponent(actionId)}/rollback`, { method: "POST", body: {} }),
    getActionEvidence: (actionId, signal) => request(`/api/v1/operations/actions/${encodeURIComponent(actionId)}/evidence`, { signal }).then((body) => body?.evidence || []),
    listSlos: slos.list,
    createSlo: slos.create,
    getSlo: slos.get,
    updateSlo: slos.update,
    evaluateSlo: (sloId) => request(`/api/v1/operations/slos/${encodeURIComponent(sloId)}/evaluate`, { method: "POST", body: {} }),
    getSloHistory: (sloId, signal) => request(`/api/v1/operations/slos/${encodeURIComponent(sloId)}/history`, { signal }).then((body) => body?.measurements || []),
    listRecoveryPlans: recoveryPlans.list,
    createRecoveryPlan: recoveryPlans.create,
    getRecoveryPlan: recoveryPlans.get,
    updateRecoveryPlan: recoveryPlans.update,
    validateRecoveryPlan: (planId) => request(`/api/v1/operations/recovery-plans/${encodeURIComponent(planId)}/validate`, { method: "POST", body: {} }),
    executeRecoveryPlan: (planId) => request(`/api/v1/operations/recovery-plans/${encodeURIComponent(planId)}/execute`, { method: "POST", body: {} }),
    listPostIncidentReviews: reviews.list,
    getPostIncidentReview: reviews.get,
    updatePostIncidentReview: reviews.update,
    publishPostIncidentReview: (reviewId) => request(`/api/v1/operations/post-incident-reviews/${encodeURIComponent(reviewId)}/publish`, { method: "POST", body: {} }),
    getHealthOverview: (signal) => request("/api/v1/operations/health", { signal }),
    getEnvironmentHealth: (environmentId, signal) => request(`/api/v1/operations/environments/${encodeURIComponent(environmentId)}/health`, { signal }),
    getEnvironmentRisk: (environmentId, signal) => request(`/api/v1/operations/environments/${encodeURIComponent(environmentId)}/risk`, { signal }),
    listHealthChecks: (signal) => request("/api/v1/operations/health/checks", { signal }).then((body) => body?.checks || []),
    createHealthCheck: (payload) => request("/api/v1/operations/health/checks", { method: "POST", body: payload }),
    executeHealthCheck: (checkId) => request(`/api/v1/operations/health/checks/${encodeURIComponent(checkId)}/execute`, { method: "POST", body: {} }),
    listHealthCheckExecutions: (checkId, signal) => request(`/api/v1/operations/health/checks/${encodeURIComponent(checkId)}/executions`, { signal }).then((body) => body?.executions || []),
    createHealthSnapshot: (payload) => request("/api/v1/operations/health/snapshots", { method: "POST", body: payload }),
    getHealthSnapshot: (snapshotId, signal) => request(`/api/v1/operations/health/snapshots/${encodeURIComponent(snapshotId)}`, { signal }),
    queryMetrics: (payload) => request("/api/v1/operations/telemetry/metrics/query", { method: "POST", body: payload }),
    queryLogs: (payload) => request("/api/v1/operations/telemetry/logs/query", { method: "POST", body: payload }),
    queryTraces: (payload) => request("/api/v1/operations/telemetry/traces/query", { method: "POST", body: payload }),
    getServiceOverview: (serviceId, signal) => request(`/api/v1/operations/telemetry/services/${encodeURIComponent(serviceId)}/overview`, { signal }),
    getTelemetryCorrelation: (correlationId, signal) => request(`/api/v1/operations/telemetry/correlations/${encodeURIComponent(correlationId)}`, { signal }),
  };
}
