import React, { useEffect, useMemo, useState } from "react";

import { getOperationsSection, operationsSections } from "./operationsModel.js";

const h = React.createElement;

function remoteState(status = "loading", data = null, error = null, updatedAt = null) {
  return { status, data, error, updatedAt };
}

function sectionFromPayload(payload) {
  const items = Array.isArray(payload?.items) ? payload.items : Array.isArray(payload) ? payload : [];
  const status = items.length ? "success" : "empty";
  return remoteState(status, payload, null, payload?.generated_at || payload?.observed_at || null);
}

function isStale(updatedAt) {
  if (!updatedAt) return false;
  const parsed = Date.parse(updatedAt);
  if (Number.isNaN(parsed)) return false;
  return Date.now() - parsed > 5 * 60 * 1000;
}

function toDisplayError(error) {
  if (!error) return "The section could not be loaded.";
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  return "The section could not be loaded.";
}

function MetricCard({ label, value, tone = "default" }) {
  return h(
    "article",
    { className: `metric-card metric-card-${tone}`, "aria-label": label },
    h("p", { className: "metric-label" }, label),
    h("p", { className: "metric-value" }, value),
  );
}

function StatusChip({ status, message }) {
  return h(
    "span",
    { className: `status-chip status-${String(status).toLowerCase()}` },
    `${message || status}`,
  );
}

function DependencyCard({ dependency }) {
  return h(
    "article",
    { className: "dependency-card", "aria-label": dependency.name },
    h("div", { className: "dependency-head" }, h("strong", null, dependency.name), h(StatusChip, { status: dependency.status, message: dependency.status })),
    h("p", { className: "muted" }, dependency.message || dependency.degraded_reason || "No live probe available."),
    h(
      "dl",
      { className: "dependency-meta" },
      h("div", null, h("dt", null, "Observed"), h("dd", null, dependency.observed_at || "unknown")),
      h("div", null, h("dt", null, "Source"), h("dd", null, dependency.source || "unknown")),
      h("div", null, h("dt", null, "Latency"), h("dd", null, dependency.latency_ms == null ? "unknown" : `${dependency.latency_ms} ms`)),
    ),
  );
}

function EmptyState({ title, detail, actionLabel, onAction, disabled }) {
  return h(
    "div",
    { className: "state-panel empty-state", role: "status", "aria-live": "polite" },
    h("strong", null, title),
    h("p", null, detail),
    actionLabel
      ? h(
          "button",
          { type: "button", className: "action-button primary", onClick: onAction, disabled },
          actionLabel,
        )
      : null,
  );
}

function LoadingState({ label }) {
  return h(
    "div",
    { className: "state-panel loading-state", role: "status", "aria-live": "polite" },
    h("strong", null, `Loading ${label}`),
    h("p", null, "Fetching live backend data."),
  );
}

function ErrorState({ error, onRetry, disabled }) {
  return h(
    "div",
    { className: "state-panel error-state", role: "alert" },
    h("strong", null, "Unable to load data"),
    h("p", null, toDisplayError(error)),
    h(
      "button",
      { type: "button", className: "action-button primary", onClick: onRetry, disabled },
      "Retry",
    ),
  );
}

function RestrictedState({ label, detail }) {
  return h(
    "div",
    { className: "state-panel restricted-state", role: "status" },
    h("strong", null, label),
    h("p", null, detail),
  );
}

function StaleDataNotice({ updatedAt }) {
  if (!isStale(updatedAt)) return null;
  return h(
    "p",
    { className: "stale-notice", role: "status", "aria-live": "polite" },
    `Data is stale. Last updated ${updatedAt}.`,
  );
}

function DataSection({ title, summary, state, children, footer, updatedAt }) {
  if (!state || state.status === "loading") {
    return h(LoadingState, { label: title });
  }
  if (state.status === "unauthorized" || state.status === "forbidden" || state.status === "restricted") {
    return h(RestrictedState, {
      label: `${title} unavailable`,
      detail: summary || "This section requires an authorized operator session.",
    });
  }
  if (state.status === "error" || state.status === "offline") {
    return h(ErrorState, { error: state.error, onRetry: state.onRetry || (() => {}), disabled: !state.onRetry });
  }
  if (state.status === "empty") {
    return h(EmptyState, { title: `${title} is empty`, detail: summary || "No records were returned from the backend." });
  }
  return h(
    "section",
    { className: "section-body", "aria-label": title },
    h("div", { className: "section-copy" }, h("p", { className: "eyebrow" }, title), h("p", { className: "section-summary" }, summary)),
    h(StaleDataNotice, { updatedAt }),
    children,
    footer ? h("div", { className: "section-footer" }, footer) : null,
  );
}

function RecordCard({ title, subtitle, details, actions }) {
  return h(
    "article",
    { className: "record-card" },
    h("div", { className: "record-head" }, h("h3", null, title), subtitle ? h("p", { className: "record-subtitle" }, subtitle) : null),
    details ? h("dl", { className: "record-details" }, details) : null,
    actions && actions.length
      ? h("div", { className: "record-actions" }, actions.map((action) => h("button", { key: action.label, type: "button", className: action.className || "action-button", onClick: action.onClick, disabled: action.disabled }, action.label)))
      : null,
  );
}

function splitText(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function defaultDrafts() {
  return {
    incident: { title: "Operational incident", severity: "SEV3", description: "" },
    support: { case_type: "booking_problem", trip_id: "", rider_id: "", driver_id: "", payment_id: "", receipt_id: "", phone: "", email: "" },
    refund: { amount: "25", currency: "AUD", payment_id: "", receipt_id: "", trip_id: "", support_case_id: "", reason: "" },
    action: { action_type: "manual_dispatch", target_id: "", reason: "", risk_level: "medium", approval_required: true, approval_reference: "" },
    investigation: { payment_id: "", reason: "" },
  };
}

function createInitialWorkspace(initialWorkspace) {
  if (initialWorkspace) {
    return initialWorkspace;
  }
  return {
    overview: remoteState("loading"),
    dependencies: remoteState("loading"),
    map: remoteState("loading"),
    trips: remoteState("loading"),
    drivers: remoteState("loading"),
    dispatch: remoteState("loading"),
    incidents: remoteState("loading"),
    safety: remoteState("loading"),
    support: remoteState("loading"),
    refunds: remoteState("loading"),
    investigations: remoteState("loading"),
    disputes: remoteState("loading"),
    actions: remoteState("loading"),
    evidence: remoteState("loading"),
  };
}

async function settledState(promise) {
  try {
    const payload = await promise;
    return sectionFromPayload(payload);
  } catch (error) {
    const status = error && typeof error === "object" && "code" in error && (error.code === "forbidden" || error.code === "unauthorized" || error.code === "restricted") ? error.code : "error";
    return remoteState(status, null, error, null);
  }
}

export function ResilienceAvailabilityWindow({ api, config, initialWorkspace }) {
  const [activeView, setActiveView] = useState("overview");
  const [workspace, setWorkspace] = useState(() => createInitialWorkspace(initialWorkspace));
  const [drafts, setDrafts] = useState(() => defaultDrafts());
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");

  const activeSection = useMemo(() => getOperationsSection(activeView), [activeView]);

  async function refresh() {
    if (!api || initialWorkspace) {
      return;
    }
    setBusy(true);
    setNotice("Refreshing live operations data.");
    const entries = await Promise.all([
      settledState(api.getOverview()),
      settledState(api.getDependencies()),
      settledState(api.getLiveMap()),
      settledState(api.getLiveTrips()),
      settledState(api.getLiveDrivers()),
      settledState(api.getDispatchQueue()),
      settledState(api.getDispatchHealth()),
      settledState(api.getIncidents()),
      settledState(api.getSafetyCases()),
      settledState(api.getSupportCases()),
      settledState(api.getRefunds()),
      settledState(api.getPaymentInvestigations()),
      settledState(api.getDisputes()),
      settledState(api.getActions()),
      settledState(api.getEvidence()),
    ]);
    setWorkspace({
      overview: entries[0],
      dependencies: entries[1],
      map: entries[2],
      trips: entries[3],
      drivers: entries[4],
      dispatch: { ...entries[5], health: entries[6].data, status: entries[5].status },
      incidents: entries[7],
      safety: entries[8],
      support: entries[9],
      refunds: entries[10],
      investigations: entries[11],
      disputes: entries[12],
      actions: entries[13],
      evidence: entries[14],
    });
    setBusy(false);
  }

  useEffect(() => {
    if (!initialWorkspace && api) {
      refresh();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, initialWorkspace]);

  const handleCreateIncident = async () => {
    if (!api || !config?.productionActionsEnabled) return;
    await api.createIncident(
      {
        title: drafts.incident.title,
        severity: drafts.incident.severity,
        description: drafts.incident.description,
      },
      `incident-${drafts.incident.title}-${drafts.incident.severity}`,
    );
    await refresh();
  };

  const handleCreateSupport = async () => {
    if (!api || !config?.productionActionsEnabled) return;
    await api.createSupportCase(
      {
        ...drafts.support,
      },
      `support-${drafts.support.case_type}-${drafts.support.trip_id || drafts.support.rider_id || "case"}`,
    );
    await refresh();
  };

  const handleCreateRefund = async () => {
    if (!api || !config?.productionActionsEnabled) return;
    await api.createRefund(
      {
        ...drafts.refund,
      },
      `refund-${drafts.refund.payment_id || drafts.refund.trip_id || drafts.refund.amount}`,
    );
    await refresh();
  };

  const handleCreateAction = async () => {
    if (!api || !config?.productionActionsEnabled) return;
    await api.createAction(
      {
        ...drafts.action,
      },
      `action-${drafts.action.action_type}-${drafts.action.target_id}`,
    );
    await refresh();
  };

  const handleCreateInvestigation = async () => {
    if (!api || !config?.productionActionsEnabled) return;
    await api.createPaymentInvestigation(
      {
        ...drafts.investigation,
      },
    );
    await refresh();
  };

  const updateDraft = (section, key, value) =>
    setDrafts((current) => ({
      ...current,
      [section]: {
        ...current[section],
        [key]: value,
      },
    }));

  const sectionState = workspace[activeView] || remoteState("loading");
  const overview = workspace.overview?.data || {};
  const dependencies = workspace.dependencies?.data?.dependencies || workspace.overview?.data?.dependencies || [];
  const summary = overview.summary || {};

  const renderActions = () => {
    const disabled = !api || busy;
    return h(
      "div",
      { className: "toolbar" },
      h(
        "button",
        { type: "button", className: "action-button primary", onClick: refresh, disabled },
        busy ? "Refreshing…" : "Refresh live data",
      ),
      h(
        "button",
        {
          type: "button",
          className: "action-button",
          onClick: () => setNotice(`Production actions ${config?.productionActionsEnabled ? "enabled" : "disabled by runtime config"}.`),
          disabled: false,
        },
        "Show runtime posture",
      ),
    );
  };

  const renderOverview = () =>
    h(
      DataSection,
      {
        title: "Overview",
        summary: "Live operational counts and dependency posture from the backend.",
        state: workspace.overview,
        updatedAt: workspace.overview?.updatedAt || overview.generated_at,
      },
      h(
        "div",
        { className: "metric-grid" },
        h(MetricCard, { label: "Active trips", value: summary.active_trips ?? "0" }),
        h(MetricCard, { label: "Online drivers", value: summary.drivers_online ?? "0" }),
        h(MetricCard, { label: "Available drivers", value: summary.drivers_available ?? "0" }),
        h(MetricCard, { label: "Open incidents", value: summary.open_incidents ?? "0" }),
        h(MetricCard, { label: "Safety cases", value: summary.open_safety_cases ?? "0" }),
        h(MetricCard, { label: "Support cases", value: summary.open_support_cases ?? "0" }),
      ),
      h(
        "div",
        { className: "panel-subgrid" },
        h(
          "section",
          { className: "subpanel" },
          h("h3", null, "Dependency health"),
          h(
            "div",
            { className: "dependency-grid" },
            dependencies.length
              ? dependencies.map((dependency) => h(DependencyCard, { key: dependency.name, dependency }))
              : h(EmptyState, { title: "No dependency data", detail: "The backend did not return dependency health records." }),
          ),
        ),
        h(
          "section",
          { className: "subpanel" },
          h("h3", null, "Recent activity"),
          h(
            "ul",
            { className: "activity-list" },
            (overview.recent_activity || []).length
              ? (overview.recent_activity || []).map((item, index) =>
                  h(
                    "li",
                    { key: `${item.subject_id}-${item.event_type}-${index}` },
                    h("strong", null, item.event_type),
                    h("span", null, item.message || item.subject_id),
                  ),
                )
              : h("li", null, "No recent activity was returned."),
          ),
        ),
      ),
      renderActions(),
    );

  const renderListSection = (state, items, kind) => {
    const disabled = !api || busy;
    const actionable = disabled || !config?.productionActionsEnabled;
    const dataItems = Array.isArray(items) ? items : [];
    const summaryText =
      kind === "map"
        ? "Map layers stay honest about location precision. If exact positions are unavailable, the portal says so."
        : getOperationsSection(kind).summary;
    const loadingLabel = getOperationsSection(kind).label;

    return h(
      DataSection,
      {
        title: getOperationsSection(kind).label,
        summary: summaryText,
        state,
        updatedAt: state?.updatedAt || state?.data?.generated_at || state?.data?.observed_at,
      },
      kind === "map"
        ? h(
            "div",
            { className: "map-summary" },
            h(
              "div",
              { className: "map-canvas", role: "img", "aria-label": "Operational map unavailable. Showing text summary instead." },
              h("strong", null, "Map provider unavailable"),
              h("p", null, "This workspace is connected to live data, but a map provider is not configured in this environment."),
            ),
            h(
              "div",
              { className: "queue-grid" },
              dataItems.length
                ? dataItems.map((item) =>
                    h(
                      RecordCard,
                      {
                        key: item.trip_id,
                        title: `${item.trip_id} · ${item.status}`,
                        subtitle: `${item.region} / ${item.service_area}`,
                        details: h(
                          React.Fragment,
                          null,
                          h("div", null, h("dt", null, "Driver"), h("dd", null, item.driver_id || "unassigned")),
                          h("div", null, h("dt", null, "Rider"), h("dd", null, item.rider_id || "unknown")),
                          h("div", null, h("dt", null, "Current location"), h("dd", null, item.current_location ? JSON.stringify(item.current_location) : "unknown")),
                          h("div", null, h("dt", null, "Safety"), h("dd", null, item.safety_status || "unknown")),
                        ),
                      },
                    ),
                  )
                : h(EmptyState, {
                    title: "No active trips",
                    detail: "The backend did not return any live trips for the current tenant and region.",
                    actionLabel: "Refresh",
                    onAction: refresh,
                    disabled,
                  }),
            ),
          )
        : h(
            "div",
            { className: "queue-grid" },
            dataItems.length
              ? dataItems.map((item) => renderRecord(kind, item, disabled))
              : h(EmptyState, {
                  title: `${loadingLabel} are empty`,
                  detail: state?.status === "empty" ? "No records were returned." : "No records are available for this section.",
                  actionLabel: kind === "incidents" ? "Create incident" : undefined,
                  onAction: kind === "incidents" ? handleCreateIncident : undefined,
                  disabled,
                }),
          ),
      renderCreateForm(kind, disabled),
    );
  };

  function renderRecord(kind, item, disabled) {
    if (kind === "trips") {
      return h(
        RecordCard,
        {
          key: item.trip_id,
          title: `${item.trip_id} · ${item.status}`,
          subtitle: `${item.region} / ${item.service_area}`,
          details: h(
            React.Fragment,
            null,
            h("div", null, h("dt", null, "Driver"), h("dd", null, item.driver_id || "unassigned")),
            h("div", null, h("dt", null, "Rider"), h("dd", null, item.rider_id || "unknown")),
            h("div", null, h("dt", null, "Pickup"), h("dd", null, item.pickup ? item.pickup.label || JSON.stringify(item.pickup) : "unknown")),
            h("div", null, h("dt", null, "Destination"), h("dd", null, item.destination ? item.destination.label || JSON.stringify(item.destination) : "unknown")),
          ),
        },
      );
    }
    if (kind === "drivers") {
      return h(RecordCard, {
        key: item.driver_id,
        title: `${item.driver_id} · ${item.status}`,
        subtitle: item.driver_name || "Live driver",
        details: h(
          React.Fragment,
          null,
          h("div", null, h("dt", null, "Vehicle"), h("dd", null, item.vehicle_id || "unassigned")),
          h("div", null, h("dt", null, "Region"), h("dd", null, item.region || "unknown")),
          h("div", null, h("dt", null, "Dispatchable"), h("dd", null, item.dispatchable ? "Yes" : "No")),
          h("div", null, h("dt", null, "Location"), h("dd", null, item.location_precision || "unknown")),
        ),
      });
    }
    if (kind === "dispatch") {
      return h(RecordCard, {
        key: item.offer_id,
        title: `${item.offer_id} · ${item.state}`,
        subtitle: item.trip_id,
        details: h(
          React.Fragment,
          null,
          h("div", null, h("dt", null, "Driver"), h("dd", null, item.driver_id || "unknown")),
          h("div", null, h("dt", null, "Earnings"), h("dd", null, item.estimated_earnings?.amount ? `${item.estimated_earnings.amount} ${item.estimated_earnings.currency}` : "unknown")),
          h("div", null, h("dt", null, "Dispatchable"), h("dd", null, item.dispatchable ? "Yes" : "No")),
        ),
      });
    }
    if (kind === "incidents") {
      const nextTransition =
        item.current_state === "detected"
          ? "declared"
          : item.current_state === "declared"
            ? "investigating"
            : item.current_state === "investigating"
              ? "mitigating"
              : item.current_state === "mitigating"
                ? "resolved"
                : item.current_state === "resolved"
                  ? "closed"
                  : null;
      return h(RecordCard, {
        key: item.incident_id,
        title: `${item.title} · ${item.severity}`,
        subtitle: item.current_state,
        details: h(
          React.Fragment,
          null,
          h("div", null, h("dt", null, "Assigned"), h("dd", null, item.assigned_to || "unassigned")),
          h("div", null, h("dt", null, "Commander"), h("dd", null, item.commander || "unassigned")),
          h("div", null, h("dt", null, "Trip links"), h("dd", null, (item.affected_trips || []).length ? item.affected_trips.join(", ") : "none")),
        ),
        actions: [
          {
            label: "Assign",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.assignIncident(item.incident_id, { assigned_to: item.assigned_to || "incident-commander" });
              await refresh();
            },
          },
          ...(nextTransition
            ? [
                {
                  label: `Move to ${nextTransition}`,
                  className: "action-button",
                  disabled: actionable,
                  onClick: async () => {
                    if (!api || actionable) return;
                    await api.transitionIncident(item.incident_id, { status: nextTransition });
                    await refresh();
                  },
                },
              ]
            : []),
        ],
      });
    }
    if (kind === "safety") {
      return h(RecordCard, {
        key: item.case_id,
        title: `${item.case_id} · ${item.severity}`,
        subtitle: item.current_state,
        details: h(
          React.Fragment,
          null,
          h("div", null, h("dt", null, "Trip"), h("dd", null, item.linked_trip_id || "unknown")),
          h("div", null, h("dt", null, "Driver"), h("dd", null, item.linked_driver_id || "unknown")),
          h("div", null, h("dt", null, "Assignee"), h("dd", null, item.assigned_to || "unassigned")),
        ),
        actions: [
          {
            label: "Assign",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.assignSafetyCase(item.case_id, { assigned_to: item.assigned_to || "safety-reviewer" });
              await refresh();
            },
          },
          {
            label: "Escalate",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.escalateSafetyCase(item.case_id, { reason: "operator review" });
              await refresh();
            },
          },
        ],
      });
    }
    if (kind === "support") {
      return h(RecordCard, {
        key: item.case_id,
        title: `${item.case_type} · ${item.current_state}`,
        subtitle: item.case_id,
        details: h(
          React.Fragment,
          null,
          h("div", null, h("dt", null, "Trip"), h("dd", null, item.trip_id || "unknown")),
          h("div", null, h("dt", null, "Rider"), h("dd", null, item.rider_id || "unknown")),
          h("div", null, h("dt", null, "Driver"), h("dd", null, item.driver_id || "unknown")),
        ),
        actions: [
          {
            label: "Assign",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.assignSupportCase(item.case_id, { assigned_to: item.assigned_to || "support-agent" });
              await refresh();
            },
          },
          {
            label: "Resolve",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.resolveSupportCase(item.case_id, { resolution: "reviewed" });
              await refresh();
            },
          },
        ],
      });
    }
    if (kind === "refunds") {
      return h(RecordCard, {
        key: item.refund_id,
        title: `${item.refund_id} · ${item.current_state}`,
        subtitle: `${item.amount} ${item.currency}`,
        details: h(
          React.Fragment,
          null,
          h("div", null, h("dt", null, "Payment"), h("dd", null, item.payment_id || "unknown")),
          h("div", null, h("dt", null, "Requester"), h("dd", null, item.requester_id || "unknown")),
          h("div", null, h("dt", null, "Approval"), h("dd", null, item.approval_required ? "Required" : "Not required")),
        ),
        actions: [
          {
            label: "Evaluate",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.evaluateRefund(item.refund_id, { approval_required: item.approval_required });
              await refresh();
            },
          },
          {
            label: "Approve",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.approveRefund(item.refund_id, { approval_reference: "ops-review" });
              await refresh();
            },
          },
          {
            label: "Execute",
            className: "action-button",
            disabled: actionable || !config?.refundExecutionEnabled,
            onClick: async () => {
              if (!api || actionable || !config?.refundExecutionEnabled) return;
              await api.executeRefund(item.refund_id, { provider_reference: "sandbox-confirmed" });
              await refresh();
            },
          },
        ],
      });
    }
    if (kind === "payments") {
      return h(RecordCard, {
        key: item.investigation_id,
        title: `${item.investigation_id} · ${item.current_state}`,
        subtitle: item.payment_id,
        details: h(
          React.Fragment,
          null,
          h("div", null, h("dt", null, "Reason"), h("dd", null, item.reason || "unknown")),
          h("div", null, h("dt", null, "Assignee"), h("dd", null, item.assigned_to || "unassigned")),
        ),
      });
    }
    if (kind === "disputes") {
      return h(RecordCard, {
        key: item.dispute_id,
        title: `${item.dispute_id} · ${item.current_state}`,
        subtitle: item.policy_version,
        details: h(
          React.Fragment,
          null,
          h("div", null, h("dt", null, "Trip"), h("dd", null, item.trip_id || "unknown")),
          h("div", null, h("dt", null, "Appeal"), h("dd", null, item.appeal_state || "none")),
        ),
      });
    }
    if (kind === "actions") {
      return h(RecordCard, {
        key: item.action_id,
        title: `${item.action_type} · ${item.current_state}`,
        subtitle: item.target_id,
        details: h(
          React.Fragment,
          null,
          h("div", null, h("dt", null, "Requester"), h("dd", null, item.requested_by || "unknown")),
          h("div", null, h("dt", null, "Approver"), h("dd", null, item.approved_by || "unassigned")),
          h("div", null, h("dt", null, "Risk"), h("dd", null, item.risk_level || "medium")),
        ),
        actions: [
          {
            label: "Evaluate",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.evaluateAction(item.action_id, { risk_level: item.risk_level });
              await refresh();
            },
          },
          {
            label: "Approve",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.approveAction(item.action_id, { approval_reference: "ops-review" });
              await refresh();
            },
          },
          {
            label: "Execute",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.executeAction(item.action_id, { adapter: "allowlisted_adapter" });
              await refresh();
            },
          },
          {
            label: "Verify",
            className: "action-button",
            disabled: actionable,
            onClick: async () => {
              if (!api || actionable) return;
              await api.verifyAction(item.action_id, { result: "verified" });
              await refresh();
            },
          },
        ],
      });
    }
    if (kind === "evidence") {
      return h(RecordCard, {
        key: item.evidence_id,
        title: `${item.evidence_id} · ${item.evidence_type}`,
        subtitle: item.subject_id,
        details: h(
          React.Fragment,
          null,
          h("div", null, h("dt", null, "Integrity"), h("dd", null, item.integrity_status || "unknown")),
          h("div", null, h("dt", null, "Verification"), h("dd", null, item.verification_status || "unknown")),
        ),
      });
    }
    return h("div", null);
  }

  function renderCreateForm(kind, disabled) {
    if (kind === "incidents") {
      return h(
        "form",
        {
          className: "create-form",
          onSubmit: async (event) => {
            event.preventDefault();
            await handleCreateIncident();
          },
        },
        h("h3", null, "Create incident"),
        h("label", null, h("span", null, "Title"), h("input", { value: drafts.incident.title, onChange: (event) => updateDraft("incident", "title", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("label", null, h("span", null, "Severity"), h("select", { value: drafts.incident.severity, onChange: (event) => updateDraft("incident", "severity", event.target.value), disabled: disabled || !config?.productionActionsEnabled }, ["SEV0", "SEV1", "SEV2", "SEV3", "SEV4"].map((value) => h("option", { key: value, value }, value)))),
        h("label", null, h("span", null, "Description"), h("textarea", { value: drafts.incident.description, onChange: (event) => updateDraft("incident", "description", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h(
          "button",
          { type: "submit", className: "action-button primary", disabled: disabled || !config?.productionActionsEnabled },
          config?.productionActionsEnabled ? "Create incident" : "Actions disabled",
        ),
      );
    }
    if (kind === "support") {
      return h(
        "form",
        {
          className: "create-form",
          onSubmit: async (event) => {
            event.preventDefault();
            await handleCreateSupport();
          },
        },
        h("h3", null, "Create support case"),
        h("label", null, h("span", null, "Case type"), h("input", { value: drafts.support.case_type, onChange: (event) => updateDraft("support", "case_type", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("label", null, h("span", null, "Trip ID"), h("input", { value: drafts.support.trip_id, onChange: (event) => updateDraft("support", "trip_id", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("label", null, h("span", null, "Payment ID"), h("input", { value: drafts.support.payment_id, onChange: (event) => updateDraft("support", "payment_id", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("button", { type: "submit", className: "action-button primary", disabled: disabled || !config?.productionActionsEnabled }, config?.productionActionsEnabled ? "Create support case" : "Actions disabled"),
      );
    }
    if (kind === "refunds") {
      return h(
        "form",
        {
          className: "create-form",
          onSubmit: async (event) => {
            event.preventDefault();
            await handleCreateRefund();
          },
        },
        h("h3", null, "Request refund"),
        h("label", null, h("span", null, "Amount"), h("input", { value: drafts.refund.amount, onChange: (event) => updateDraft("refund", "amount", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("label", null, h("span", null, "Currency"), h("input", { value: drafts.refund.currency, onChange: (event) => updateDraft("refund", "currency", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("label", null, h("span", null, "Payment ID"), h("input", { value: drafts.refund.payment_id, onChange: (event) => updateDraft("refund", "payment_id", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("button", { type: "submit", className: "action-button primary", disabled: disabled || !config?.productionActionsEnabled }, config?.productionActionsEnabled ? "Create refund" : "Actions disabled"),
      );
    }
    if (kind === "payments") {
      return h(
        "form",
        {
          className: "create-form",
          onSubmit: async (event) => {
            event.preventDefault();
            await handleCreateInvestigation();
          },
        },
        h("h3", null, "Open payment investigation"),
        h("label", null, h("span", null, "Payment ID"), h("input", { value: drafts.investigation.payment_id, onChange: (event) => updateDraft("investigation", "payment_id", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("label", null, h("span", null, "Reason"), h("input", { value: drafts.investigation.reason, onChange: (event) => updateDraft("investigation", "reason", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("button", { type: "submit", className: "action-button primary", disabled: disabled || !config?.productionActionsEnabled }, config?.productionActionsEnabled ? "Open investigation" : "Actions disabled"),
      );
    }
    if (kind === "actions") {
      return h(
        "form",
        {
          className: "create-form",
          onSubmit: async (event) => {
            event.preventDefault();
            await handleCreateAction();
          },
        },
        h("h3", null, "Request operational action"),
        h("label", null, h("span", null, "Action type"), h("input", { value: drafts.action.action_type, onChange: (event) => updateDraft("action", "action_type", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("label", null, h("span", null, "Target"), h("input", { value: drafts.action.target_id, onChange: (event) => updateDraft("action", "target_id", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("label", null, h("span", null, "Reason"), h("input", { value: drafts.action.reason, onChange: (event) => updateDraft("action", "reason", event.target.value), disabled: disabled || !config?.productionActionsEnabled })),
        h("button", { type: "submit", className: "action-button primary", disabled: disabled || !config?.productionActionsEnabled }, config?.productionActionsEnabled ? "Request action" : "Actions disabled"),
      );
    }
    return null;
  }

  const sectionBody =
    activeView === "overview"
      ? renderOverview()
      : renderListSection(
          sectionState,
          (sectionState?.data?.items || sectionState?.data?.dependencies || sectionState?.data?.recent_activity || []),
          activeView,
        );

  return h(
    "main",
    { className: "operations-shell", "aria-labelledby": "resilience-title" },
    h("a", { className: "skip-link", href: "#operations-content" }, "Skip to content"),
    h(
      "header",
      { className: "page-header" },
      h(
        "div",
        null,
        h("p", { className: "eyebrow" }, "NovaRide operations"),
        h("h1", { id: "resilience-title" }, "Operations workspace"),
        h("p", { className: "lede" }, "Observe, investigate, decide, request, approve, execute, and verify governed mobility operations from one place."),
      ),
      h(
        "div",
        { className: "header-summary", "aria-label": "Runtime posture" },
        h("span", null, config?.baseUrl || "/api/v1/novaride/operations"),
        h("span", null, config?.refundExecutionEnabled ? "Refund execution enabled" : "Refund execution disabled"),
        h("span", null, config?.productionActionsEnabled ? "Production actions enabled" : "Production actions disabled"),
      ),
    ),
    notice ? h("p", { className: "notice", role: "status", "aria-live": "polite" }, notice) : null,
    h(
      "nav",
      { "aria-label": "Operations sections", className: "section-tabs" },
      operationsSections.map((section) =>
        h(
          "button",
          {
            key: section.key,
            type: "button",
            className: activeView === section.key ? "tab active" : "tab",
            "aria-pressed": activeView === section.key,
            onClick: () => setActiveView(section.key),
          },
          section.label,
        ),
      ),
    ),
    h(
      "section",
      { id: "operations-content", className: "panel" },
      h(
        "div",
        { className: "section-heading" },
        h(
          "div",
          null,
          h("p", { className: "eyebrow" }, "Focused view"),
          h("h2", null, activeSection.label),
        ),
        h("p", { className: "section-summary" }, activeSection.summary),
      ),
      sectionBody,
    ),
    h(
      "section",
      { className: "panel panel-dense", "aria-labelledby": "system-title" },
      h(
        "div",
        { className: "section-heading" },
        h("div", null, h("p", { className: "eyebrow" }, "System posture"), h("h2", { id: "system-title" }, "Authoritative backend state")),
        h("p", { className: "section-summary" }, "All displayed data comes from the backend. If a dependency cannot be probed, the portal shows unknown instead of a green claim."),
      ),
      h("div", { className: "metric-grid" }, h(MetricCard, { label: "Supported views", value: operationsSections.length }), h(MetricCard, { label: "Live sections", value: Object.values(workspace).filter((item) => item && item.status === "success").length }), h(MetricCard, { label: "Loading sections", value: Object.values(workspace).filter((item) => item && item.status === "loading").length })),
      h(
        "div",
        { className: "footer-links" },
        h("span", null, "Role-specific navigation"),
        h("span", null, "Accessible controls"),
        h("span", null, "Request and trace IDs"),
        h("span", null, "Evidence-preserving workflows"),
      ),
    ),
  );
}
