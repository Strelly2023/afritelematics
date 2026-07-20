export type OperationsApiErrorShape = {
  code: string;
  message: string;
  status: number;
  details?: unknown;
};

export class OperationsApiError extends Error {
  code: string;
  status: number;
  details?: unknown;

  constructor(shape: OperationsApiErrorShape) {
    super(shape.message);
    this.name = "OperationsApiError";
    this.code = shape.code;
    this.status = shape.status;
    this.details = shape.details;
  }
}

export type OperationsApiOptions = {
  baseUrl: string;
  fetchImpl?: typeof fetch;
  credentials?: RequestCredentials;
  csrfToken?: string | null;
  authTokenProvider?: () => string | null;
  timeoutMs?: number;
  requestId?: () => string;
  traceId?: () => string;
  correlationId?: () => string;
};

export type RequestOptions = {
  signal?: AbortSignal;
  idempotencyKey?: string;
  requestId?: string;
  traceId?: string;
  correlationId?: string;
  csrfToken?: string | null;
};

export type OperationsApiClient = ReturnType<typeof createOperationsApi>;

type JsonRecord = Record<string, unknown>;

function buildId(prefix: string): string {
  const entropy =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Math.random().toString(16).slice(2)}-${Date.now().toString(16)}`;
  return `${prefix}_${entropy}`;
}

function resolveError(status: number, payload: unknown, fallbackCode: string): OperationsApiError {
  if (payload && typeof payload === "object") {
    const detail = payload as JsonRecord;
    const code =
      typeof detail.code === "string"
        ? detail.code
        : typeof detail.error === "string"
          ? detail.error
          : fallbackCode;
    const message =
      typeof detail.message === "string"
        ? detail.message
        : typeof detail.detail === "string"
          ? detail.detail
          : typeof detail.error === "string"
            ? detail.error
            : `Request failed with status ${status}`;
    return new OperationsApiError({ code, message, status, details: payload });
  }
  return new OperationsApiError({
    code: fallbackCode,
    message: typeof payload === "string" && payload ? payload : `Request failed with status ${status}`,
    status,
    details: payload,
  });
}

async function readJsonResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  const body = await response.text();
  if (contentType.includes("text/html") || body.trimStart().startsWith("<")) {
    throw new OperationsApiError({
      code: "html_response",
      message: `Unexpected HTML response from ${response.url || "operations API"}`,
      status: response.status,
      details: body.slice(0, 200),
    });
  }
  if (!body) {
    return null;
  }
  try {
    return JSON.parse(body) as unknown;
  } catch {
    throw new OperationsApiError({
      code: "invalid_json",
      message: `Invalid JSON from ${response.url || "operations API"}`,
      status: response.status,
      details: body.slice(0, 200),
    });
  }
}

function normalizePath(path: string): string {
  return path.startsWith("/") ? path : `/${path}`;
}

export function createOperationsApi(options: OperationsApiOptions) {
  const fetchImpl = options.fetchImpl ?? fetch.bind(globalThis);
  const baseUrl = options.baseUrl.replace(/\/$/, "");
  const credentials = options.credentials ?? "include";
  const timeoutMs = options.timeoutMs ?? 12_000;

  async function request<T>(
    path: string,
    init: RequestInit = {},
    requestOptions: RequestOptions = {},
  ): Promise<T> {
    const controller = new AbortController();
    const timeout = globalThis.setTimeout(
      () => controller.abort(new DOMException("timeout", "AbortError")),
      timeoutMs,
    );
    const { signal } = requestOptions;
    if (signal) {
      if (signal.aborted) {
        controller.abort(signal.reason);
      } else {
        signal.addEventListener("abort", () => controller.abort(signal.reason), { once: true });
      }
    }
    const headers = new Headers(init.headers || {});
    headers.set("Accept", "application/json");
    if (requestOptions.csrfToken ?? options.csrfToken) {
      headers.set("X-CSRF-Token", String(requestOptions.csrfToken ?? options.csrfToken));
    }
    const authToken = options.authTokenProvider?.();
    if (authToken) {
      headers.set("Authorization", `Bearer ${authToken}`);
    }
    const requestId = requestOptions.requestId || options.requestId?.() || buildId("req");
    const traceId = requestOptions.traceId || options.traceId?.() || buildId("trace");
    const correlationId = requestOptions.correlationId || options.correlationId?.() || buildId("corr");
    headers.set("X-Request-Id", requestId);
    headers.set("X-Trace-Id", traceId);
    headers.set("X-Correlation-Id", correlationId);
    if (requestOptions.idempotencyKey) {
      headers.set("Idempotency-Key", requestOptions.idempotencyKey);
    }
    const method = (init.method || "GET").toUpperCase();
    const isBodyAllowed = !["GET", "HEAD"].includes(method);
    const body =
      isBodyAllowed && init.body && typeof init.body === "string"
        ? init.body
        : init.body && isBodyAllowed
          ? init.body
          : undefined;
    if (body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    try {
      const response = await fetchImpl(`${baseUrl}${normalizePath(path)}`, {
        ...init,
        method,
        headers,
        body,
        credentials,
        signal: controller.signal,
      });
      const payload = await readJsonResponse(response);
      if (!response.ok) {
        throw resolveError(response.status, payload, `http_${response.status}`);
      }
      return payload as T;
    } catch (error) {
      if (error instanceof OperationsApiError) {
        throw error;
      }
      const reason = error instanceof Error ? error.message : "network_failure";
      throw new OperationsApiError({
        code: reason === "AbortError" ? "timeout" : "network_failure",
        message: reason === "AbortError" ? "Operations request timed out" : "Operations request failed",
        status: 0,
        details: error,
      });
    } finally {
      globalThis.clearTimeout(timeout);
    }
  }

  return {
    baseUrl,
    request,
    getOverview: (signal?: AbortSignal) => request<JsonRecord>("/overview", { method: "GET" }, { signal }),
    getDependencies: (signal?: AbortSignal) => request<JsonRecord>("/dependencies", { method: "GET" }, { signal }),
    getLiveMap: (signal?: AbortSignal) => request<JsonRecord>("/map", { method: "GET" }, { signal }),
    getLiveTrips: (signal?: AbortSignal) => request<JsonRecord>("/trips/live", { method: "GET" }, { signal }),
    getLiveDrivers: (signal?: AbortSignal) => request<JsonRecord>("/drivers/live", { method: "GET" }, { signal }),
    getDispatchQueue: (signal?: AbortSignal) => request<JsonRecord>("/dispatch/queue", { method: "GET" }, { signal }),
    getDispatchHealth: (signal?: AbortSignal) => request<JsonRecord>("/dispatch/health", { method: "GET" }, { signal }),
    getIncidents: (signal?: AbortSignal) => request<JsonRecord>("/incidents", { method: "GET" }, { signal }),
    getIncident: (incidentId: string, signal?: AbortSignal) => request<JsonRecord>(`/incidents/${incidentId}`, { method: "GET" }, { signal }),
    createIncident: (body: JsonRecord, idempotencyKey?: string, signal?: AbortSignal) =>
      request<JsonRecord>(
        "/incidents",
        { method: "POST", body: JSON.stringify(body) },
        { signal, idempotencyKey: idempotencyKey || buildId("incident") },
      ),
    transitionIncident: (incidentId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/incidents/${incidentId}/transition`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    assignIncident: (incidentId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/incidents/${incidentId}/assign`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    getSafetyCases: (signal?: AbortSignal) => request<JsonRecord>("/safety/cases", { method: "GET" }, { signal }),
    getSafetyCase: (caseId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/safety/cases/${caseId}`, { method: "GET" }, { signal }),
    assignSafetyCase: (caseId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/safety/cases/${caseId}/assign`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    escalateSafetyCase: (caseId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/safety/cases/${caseId}/escalate`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    resolveSafetyCase: (caseId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/safety/cases/${caseId}/resolve`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    getSafetyEvidence: (caseId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/safety/cases/${caseId}/evidence`, { method: "GET" }, { signal }),
    getSupportCases: (query: Record<string, string | undefined> = {}, signal?: AbortSignal) => {
      const params = new URLSearchParams();
      Object.entries(query).forEach(([key, value]) => {
        if (value) params.set(key, value);
      });
      const suffix = params.toString() ? `?${params.toString()}` : "";
      return request<JsonRecord>(`/support/cases${suffix}`, { method: "GET" }, { signal });
    },
    getSupportCase: (caseId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/support/cases/${caseId}`, { method: "GET" }, { signal }),
    createSupportCase: (body: JsonRecord, idempotencyKey?: string, signal?: AbortSignal) =>
      request<JsonRecord>(
        "/support/cases",
        { method: "POST", body: JSON.stringify(body) },
        { signal, idempotencyKey: idempotencyKey || buildId("support") },
      ),
    patchSupportCase: (caseId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/support/cases/${caseId}`, { method: "PATCH", body: JSON.stringify(body) }, { signal }),
    assignSupportCase: (caseId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/support/cases/${caseId}/assign`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    escalateSupportCase: (caseId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/support/cases/${caseId}/escalate`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    resolveSupportCase: (caseId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/support/cases/${caseId}/resolve`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    getSupportTimeline: (caseId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/support/cases/${caseId}/timeline`, { method: "GET" }, { signal }),
    getSupportEvidence: (caseId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/support/cases/${caseId}/evidence`, { method: "GET" }, { signal }),
    getRefunds: (signal?: AbortSignal) => request<JsonRecord>("/refunds", { method: "GET" }, { signal }),
    getRefund: (refundId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/refunds/${refundId}`, { method: "GET" }, { signal }),
    createRefund: (body: JsonRecord, idempotencyKey?: string, signal?: AbortSignal) =>
      request<JsonRecord>(
        "/refunds",
        { method: "POST", body: JSON.stringify(body) },
        { signal, idempotencyKey: idempotencyKey || buildId("refund") },
      ),
    evaluateRefund: (refundId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/refunds/${refundId}/evaluate`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    requestRefundApproval: (refundId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/refunds/${refundId}/approval-requests`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    approveRefund: (refundId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/refunds/${refundId}/approve`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    executeRefund: (refundId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/refunds/${refundId}/execute`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    getPaymentInvestigations: (signal?: AbortSignal) => request<JsonRecord>("/payments/investigations", { method: "GET" }, { signal }),
    getPaymentInvestigation: (investigationId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/payments/investigations/${investigationId}`, { method: "GET" }, { signal }),
    createPaymentInvestigation: (body: JsonRecord, idempotencyKey?: string, signal?: AbortSignal) =>
      request<JsonRecord>(
        "/payments/investigations",
        { method: "POST", body: JSON.stringify(body) },
        { signal, idempotencyKey: idempotencyKey || buildId("investigation") },
      ),
    getDisputes: (signal?: AbortSignal) => request<JsonRecord>("/disputes", { method: "GET" }, { signal }),
    getDispute: (disputeId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/disputes/${disputeId}`, { method: "GET" }, { signal }),
    createDispute: (body: JsonRecord, idempotencyKey?: string, signal?: AbortSignal) =>
      request<JsonRecord>(
        "/disputes",
        { method: "POST", body: JSON.stringify(body) },
        { signal, idempotencyKey: idempotencyKey || buildId("dispute") },
      ),
    assignDispute: (disputeId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/disputes/${disputeId}/assign`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    requestDisputeEvidence: (disputeId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/disputes/${disputeId}/request-evidence`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    decideDispute: (disputeId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/disputes/${disputeId}/decide`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    appealDispute: (disputeId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/disputes/${disputeId}/appeal`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    getActions: (signal?: AbortSignal) => request<JsonRecord>("/actions", { method: "GET" }, { signal }),
    getAction: (actionId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/actions/${actionId}`, { method: "GET" }, { signal }),
    createAction: (body: JsonRecord, idempotencyKey?: string, signal?: AbortSignal) =>
      request<JsonRecord>(
        "/actions",
        { method: "POST", body: JSON.stringify(body) },
        { signal, idempotencyKey: idempotencyKey || buildId("action") },
      ),
    rejectAction: (actionId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/actions/${actionId}/reject`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    cancelAction: (actionId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/actions/${actionId}/cancel`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    evaluateAction: (actionId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/actions/${actionId}/evaluate`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    approveAction: (actionId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/actions/${actionId}/approve`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    executeAction: (actionId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/actions/${actionId}/execute`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    verifyAction: (actionId: string, body: JsonRecord, signal?: AbortSignal) =>
      request<JsonRecord>(`/actions/${actionId}/verify`, { method: "POST", body: JSON.stringify(body) }, { signal }),
    getEvidence: (signal?: AbortSignal) => request<JsonRecord>("/evidence", { method: "GET" }, { signal }),
    getIncidentEvidence: (incidentId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/incidents/${incidentId}/evidence`, { method: "GET" }, { signal }),
    getCaseEvidence: (caseId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/cases/${caseId}/evidence`, { method: "GET" }, { signal }),
    getActionEvidence: (actionId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/actions/${actionId}/evidence`, { method: "GET" }, { signal }),
    getRefundEvidence: (refundId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/refunds/${refundId}/evidence`, { method: "GET" }, { signal }),
    getIncidentTimeline: (incidentId: string, signal?: AbortSignal) =>
      request<JsonRecord>(`/incidents/${incidentId}/timeline`, { method: "GET" }, { signal }),
  };
}
