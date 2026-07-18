import React, { useEffect, useMemo, useState } from "react";

import { createNovaCodeProNcp008Api } from "./api/novacodeproNcp008Api.js";

const NAV_ITEMS = [
  { id: "overview", label: "Overview" },
  { id: "environments", label: "Environments" },
  { id: "services", label: "Services" },
  { id: "deployments", label: "Deployments" },
  { id: "alerts", label: "Alerts" },
  { id: "incidents", label: "Incidents" },
  { id: "actions", label: "Actions" },
  { id: "approvals", label: "Approvals" },
  { id: "observability", label: "Observability" },
  { id: "slos", label: "SLOs" },
  { id: "recovery", label: "Recovery" },
  { id: "reviews", label: "Post-Incident Reviews" },
  { id: "evidence", label: "Evidence" },
  { id: "activity", label: "Activity" },
];

function parseRoute(pathname) {
  const parts = String(pathname || "").replace(/\/+$/, "").split("/").filter(Boolean);
  if (parts[0] !== "novacodepro" || parts[1] !== "operations") {
    return { section: "overview" };
  }
  return { section: parts[2] || "overview" };
}

function StateBanner({ state, error }) {
  if (state === "ready") return null;
  const label = {
    loading: "Loading",
    error: "Error",
  }[state] || "Status";
  return (
    <div className={`state-banner ${state || "error"}`} role="status" aria-live="polite">
      <strong>{label}</strong>
      <span>{error?.message || error?.code || "Request in progress."}</span>
    </div>
  );
}

function Panel({ title, aside, children }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        {aside ? <div className="panel-aside">{aside}</div> : null}
      </div>
      {children}
    </section>
  );
}

function Badge({ label, value }) {
  return (
    <span className="context-chip">
      <strong>{label}</strong>
      <span>{value}</span>
    </span>
  );
}

function List({ items, empty, renderItem }) {
  if (!items.length) return <p className="empty-state">{empty}</p>;
  return <div className="stack">{items.map(renderItem)}</div>;
}

function TextField({ label, value, onChange, placeholder = "" }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input value={value} onChange={onChange} placeholder={placeholder} />
    </label>
  );
}

function TextArea({ label, value, onChange, placeholder = "", rows = 4 }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <textarea value={value} onChange={onChange} placeholder={placeholder} rows={rows} />
    </label>
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <select value={value} onChange={onChange}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function Actions({ children }) {
  return <div className="toolbar">{children}</div>;
}

function SectionTable({ rows }) {
  return (
    <div className="table-wrap">
      <table>
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <th>{label}</th>
              <td>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function NCP008Portal({ session, pathname, navigate, baseUrl = "", onLogout }) {
  const client = useMemo(() => createNovaCodeProNcp008Api({ baseUrl, fetchImpl: globalThis.fetch }), [baseUrl]);
  const route = useMemo(() => parseRoute(pathname), [pathname]);
  const [activeTab, setActiveTab] = useState(route.section);
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);
  const [overview, setOverview] = useState(null);
  const [activity, setActivity] = useState([]);
  const [risk, setRisk] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [environments, setEnvironments] = useState([]);
  const [services, setServices] = useState([]);
  const [deployments, setDeployments] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [actions, setActions] = useState([]);
  const [slos, setSlos] = useState([]);
  const [recoveryPlans, setRecoveryPlans] = useState([]);
  const [postIncidentReviews, setPostIncidentReviews] = useState([]);
  const [selectedServiceId, setSelectedServiceId] = useState("");
  const [selectedEnvironmentId, setSelectedEnvironmentId] = useState("");
  const [selectedIncidentId, setSelectedIncidentId] = useState("");
  const [selectedActionId, setSelectedActionId] = useState("");
  const [selectedSloId, setSelectedSloId] = useState("");
  const [selectedRecoveryPlanId, setSelectedRecoveryPlanId] = useState("");
  const [selectedDeploymentId, setSelectedDeploymentId] = useState("");
  const [selectedAlertId, setSelectedAlertId] = useState("");
  const [workspaceDraft, setWorkspaceDraft] = useState({ name: "Operations Workspace", description: "Governed runtime operations" });
  const [environmentDraft, setEnvironmentDraft] = useState({ code: "production", name: "Production", type: "PRODUCTION", region: "Australia", status: "ACTIVE" });
  const [serviceDraft, setServiceDraft] = useState({ name: "Operations Service", service_type: "api", runtime_kind: "fastapi", version: "1.0.0", health_status: "HEALTHY", readiness_status: "HEALTHY", deployment_status: "ACTIVE", criticality: "STANDARD" });
  const [incidentDraft, setIncidentDraft] = useState({ title: "Incident", summary: "", severity: "SEV3", type: "OTHER", status: "DETECTED" });
  const [actionDraft, setActionDraft] = useState({ action_type: "service_restart", reason: "Routine governed maintenance", requested_parameters: "{}" });

  useEffect(() => {
    setActiveTab(route.section);
  }, [route.section]);

  async function reload() {
    setState("loading");
    setError(null);
    try {
      const [
        overviewBody,
        activityBody,
        riskBody,
        readinessBody,
        environmentList,
        serviceList,
        deploymentList,
        alertList,
        incidentList,
        actionList,
        sloList,
        recoveryPlanList,
        reviewList,
      ] = await Promise.all([
        client.overview(),
        client.activity(),
        client.risk(),
        client.readiness(),
        client.listEnvironments(),
        client.listServices(),
        client.listDeployments(),
        client.listAlerts(),
        client.listIncidents(),
        client.listActions(),
        client.listSlos(),
        client.listRecoveryPlans(),
        client.listPostIncidentReviews(),
      ]);
      setOverview(overviewBody);
      setActivity(activityBody?.activity || []);
      setRisk(riskBody);
      setReadiness(readinessBody);
      setEnvironments(environmentList || []);
      setServices(serviceList || []);
      setDeployments(deploymentList || []);
      setAlerts(alertList || []);
      setIncidents(incidentList || []);
      setActions(actionList || []);
      setSlos(sloList || []);
      setRecoveryPlans(recoveryPlanList || []);
      setPostIncidentReviews(reviewList || []);
      setSelectedServiceId((serviceList || [])[0]?.id || "");
      setSelectedEnvironmentId((environmentList || [])[0]?.id || "");
      setSelectedIncidentId((incidentList || [])[0]?.id || "");
      setSelectedActionId((actionList || [])[0]?.id || "");
      setSelectedSloId((sloList || [])[0]?.id || "");
      setSelectedRecoveryPlanId((recoveryPlanList || [])[0]?.id || "");
      setSelectedDeploymentId((deploymentList || [])[0]?.id || "");
      setSelectedAlertId((alertList || [])[0]?.id || "");
      setState("ready");
    } catch (cause) {
      setError(cause);
      setState("error");
    }
  }

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  async function createWorkspace() {
    await client.createWorkspace({ ...workspaceDraft, environment_ids: selectedEnvironmentId ? [selectedEnvironmentId] : [] });
    await reload();
  }

  async function createEnvironment() {
    await client.createEnvironment(environmentDraft);
    await reload();
  }

  async function createService() {
    await client.createService({ ...serviceDraft, environment_id: selectedEnvironmentId || environmentDraft.code, dependencies: [], endpoints: [] });
    await reload();
  }

  async function createIncident() {
    await client.createIncident({ ...incidentDraft, environment_id: selectedEnvironmentId, affected_service_ids: selectedServiceId ? [selectedServiceId] : [] });
    await reload();
  }

  async function requestAction() {
    const payload = {
      ...actionDraft,
      requested_parameters: actionDraft.requested_parameters ? JSON.parse(actionDraft.requested_parameters) : {},
      service_id: selectedServiceId,
      environment_id: selectedEnvironmentId,
    };
    await client.createAction(payload);
    await reload();
  }

  async function acknowledgeAlert() {
    if (!selectedAlertId) return;
    await client.acknowledgeAlert(selectedAlertId, { reason: "Acknowledged in Operations Studio" });
    await reload();
  }

  async function resolveAlert() {
    if (!selectedAlertId) return;
    await client.resolveAlert(selectedAlertId, { reason: "Resolved in Operations Studio" });
    await reload();
  }

  async function evaluateSlo() {
    if (!selectedSloId) return;
    await client.evaluateSlo(selectedSloId);
    await reload();
  }

  const tabs = NAV_ITEMS.map((item) => ({
    ...item,
    active: item.id === activeTab,
  }));

  return (
    <div className="app-shell operations-studio">
      <header className="topbar">
        <div className="brand-block">
          <img className="brand-logo" src="/brand/NOVACODEPRO.webp" alt="NovaCodePro logo" />
          <div>
            <p className="eyebrow">NovaCodePro operations studio</p>
            <strong>Operations</strong>
            <p className="muted">{session?.user?.display_name || session?.user?.email || "Authenticated operator"}</p>
          </div>
        </div>
        <Actions>
          <button type="button" className="secondary-action" onClick={() => onLogout?.()}>
            Logout
          </button>
        </Actions>
      </header>

      <nav className="workspace-tabs" aria-label="Operations navigation">
        {tabs.map((item) => (
          <button key={item.id} type="button" className={item.active ? "tab active" : "tab"} onClick={() => setActiveTab(item.id)}>
            {item.label}
          </button>
        ))}
      </nav>

      <main className="workspace-main">
        <StateBanner state={state} error={error} />
        {activeTab === "overview" ? (
          <div className="stack">
            <Panel title="Operations summary" aside={<Badge label="Status" value={overview?.readiness?.status || readiness?.status || "UNKNOWN"} />}>
              <SectionTable
                rows={[
                  ["Services", String(overview?.service_count ?? services.length)],
                  ["Environments", String(overview?.environment_count ?? environments.length)],
                  ["Active incidents", String(overview?.incident_count ?? incidents.length)],
                  ["Critical alerts", String(overview?.critical_alerts ?? alerts.filter((alert) => alert.severity === "CRITICAL").length)],
                  ["Pending approvals", String(overview?.pending_approvals ?? 0)],
                  ["Error budget burn", String(overview?.error_budget_burn ?? 0)],
                ]}
              />
            </Panel>

            <Panel title="Environment risk summary">
              <List
                items={environments}
                empty="No environments discovered."
                renderItem={(environment) => (
                  <article key={environment.id} className="card">
                    <strong>{environment.name}</strong>
                    <p>{environment.type} · {environment.region}</p>
                    <p>{environment.status}</p>
                  </article>
                )}
              />
            </Panel>

            <Panel title="Recent activity">
              <List
                items={activity}
                empty="No recent operational activity."
                renderItem={(event) => (
                  <article key={event.event_id || event.id} className="card">
                    <strong>{event.event_type || event.action || "event"}</strong>
                    <p>{event.occurred_at || event.at || event.created_at || ""}</p>
                  </article>
                )}
              />
            </Panel>
          </div>
        ) : null}

        {activeTab === "environments" ? (
          <div className="stack">
            <Panel title="Create environment">
              <div className="form-grid">
                <TextField label="Name" value={environmentDraft.name} onChange={(event) => setEnvironmentDraft((current) => ({ ...current, name: event.target.value }))} />
                <TextField label="Code" value={environmentDraft.code} onChange={(event) => setEnvironmentDraft((current) => ({ ...current, code: event.target.value }))} />
                <Select label="Type" value={environmentDraft.type} onChange={(event) => setEnvironmentDraft((current) => ({ ...current, type: event.target.value }))} options={[...["LOCAL", "DEVELOPMENT", "TEST", "STAGING", "PRODUCTION", "DISASTER_RECOVERY"]].map((value) => ({ value, label: value }))} />
                <TextField label="Region" value={environmentDraft.region} onChange={(event) => setEnvironmentDraft((current) => ({ ...current, region: event.target.value }))} />
              </div>
              <Actions>
                <button type="button" className="primary-action" onClick={() => void createEnvironment()}>
                  Create environment
                </button>
              </Actions>
            </Panel>
            <Panel title="Environments">
              <List
                items={environments}
                empty="No environments available."
                renderItem={(environment) => (
                  <article key={environment.id} className="card">
                    <strong>{environment.name}</strong>
                    <p>{environment.environment_type || environment.type}</p>
                    <p>{environment.status}</p>
                  </article>
                )}
              />
            </Panel>
          </div>
        ) : null}

        {activeTab === "services" ? (
          <div className="stack">
            <Panel title="Create service">
              <div className="form-grid">
                <TextField label="Name" value={serviceDraft.name} onChange={(event) => setServiceDraft((current) => ({ ...current, name: event.target.value }))} />
                <TextField label="Runtime" value={serviceDraft.runtime_kind} onChange={(event) => setServiceDraft((current) => ({ ...current, runtime_kind: event.target.value }))} />
                <TextField label="Version" value={serviceDraft.version} onChange={(event) => setServiceDraft((current) => ({ ...current, version: event.target.value }))} />
                <TextField label="Criticality" value={serviceDraft.criticality} onChange={(event) => setServiceDraft((current) => ({ ...current, criticality: event.target.value }))} />
              </div>
              <Actions>
                <button type="button" className="primary-action" onClick={() => void createService()}>
                  Create service
                </button>
              </Actions>
            </Panel>
            <Panel title="Services" aside={<Badge label="Selected" value={selectedServiceId || "none"} />}>
              <List
                items={services}
                empty="No services discovered."
                renderItem={(service) => (
                  <article key={service.id} className="card">
                    <strong>{service.name}</strong>
                    <p>{service.health_status} · {service.deployment_status}</p>
                    <p>{service.version} → {service.desired_version}</p>
                  </article>
                )}
              />
            </Panel>
          </div>
        ) : null}

        {activeTab === "alerts" ? (
          <Panel title="Alerts" aside={<Badge label="Selected" value={selectedAlertId || "none"} />}>
            <Actions>
              <button type="button" className="secondary-action" onClick={() => void acknowledgeAlert()}>
                Acknowledge
              </button>
              <button type="button" className="secondary-action" onClick={() => void resolveAlert()}>
                Resolve
              </button>
            </Actions>
            <List
              items={alerts}
              empty="No alerts present."
              renderItem={(alert) => (
                <article key={alert.id} className="card">
                  <strong>{alert.title}</strong>
                  <p>{alert.severity} · {alert.status}</p>
                </article>
              )}
            />
          </Panel>
        ) : null}

        {activeTab === "incidents" ? (
          <div className="stack">
            <Panel title="Declare incident">
              <div className="form-grid">
                <TextField label="Title" value={incidentDraft.title} onChange={(event) => setIncidentDraft((current) => ({ ...current, title: event.target.value }))} />
                <Select label="Severity" value={incidentDraft.severity} onChange={(event) => setIncidentDraft((current) => ({ ...current, severity: event.target.value }))} options={["SEV0", "SEV1", "SEV2", "SEV3", "SEV4"].map((value) => ({ value, label: value }))} />
              </div>
              <TextArea label="Summary" value={incidentDraft.summary} onChange={(event) => setIncidentDraft((current) => ({ ...current, summary: event.target.value }))} />
              <Actions>
                <button type="button" className="primary-action" onClick={() => void createIncident()}>
                  Declare incident
                </button>
              </Actions>
            </Panel>
            <Panel title="Incidents" aside={<Badge label="Selected" value={selectedIncidentId || "none"} />}>
              <List
                items={incidents}
                empty="No incidents recorded."
                renderItem={(incident) => (
                  <article key={incident.id} className="card">
                    <strong>{incident.title}</strong>
                    <p>{incident.severity} · {incident.status}</p>
                  </article>
                )}
              />
            </Panel>
          </div>
        ) : null}

        {activeTab === "actions" ? (
          <div className="stack">
            <Panel title="Request operational action" aside={<Badge label="Selected" value={selectedActionId || "none"} />}>
              <div className="form-grid">
                <Select label="Action type" value={actionDraft.action_type} onChange={(event) => setActionDraft((current) => ({ ...current, action_type: event.target.value }))} options={["service_restart", "service_scale", "deployment_rollback", "deployment_promote", "workflow_pause", "workflow_resume", "feature_flag_disable", "feature_flag_enable", "traffic_shift", "maintenance_mode_enable", "maintenance_mode_disable", "cache_invalidate", "queue_pause", "queue_resume", "remediation_run", "recovery_plan_execute"].map((value) => ({ value, label: value }))} />
                <TextField label="Reason" value={actionDraft.reason} onChange={(event) => setActionDraft((current) => ({ ...current, reason: event.target.value }))} />
              </div>
              <TextArea label="Requested parameters" value={actionDraft.requested_parameters} onChange={(event) => setActionDraft((current) => ({ ...current, requested_parameters: event.target.value }))} rows={3} />
              <Actions>
                <button type="button" className="primary-action" onClick={() => void requestAction()}>
                  Create request
                </button>
              </Actions>
            </Panel>
            <Panel title="Actions">
              <Actions>
                <button type="button" className="secondary-action" onClick={() => void client.requestActionApproval(selectedActionId)}>
                  Request approval
                </button>
                <button type="button" className="secondary-action" onClick={() => void client.executeAction(selectedActionId)}>
                  Execute
                </button>
                <button type="button" className="secondary-action" onClick={() => void client.verifyAction(selectedActionId)}>
                  Verify
                </button>
              </Actions>
              <List
                items={actions}
                empty="No actions requested."
                renderItem={(action) => (
                  <article key={action.id} className="card">
                    <strong>{action.action_type}</strong>
                    <p>{action.status} · {action.risk_level}</p>
                  </article>
                )}
              />
            </Panel>
          </div>
        ) : null}

        {activeTab === "observability" ? (
          <Panel title="Observability">
            <div className="stack">
              <p>Service observability is constrained and scoped to the selected tenant.</p>
              <button type="button" className="secondary-action" onClick={() => void selectedServiceId && client.getServiceOverview(selectedServiceId)}>
                Refresh service overview
              </button>
            </div>
          </Panel>
        ) : null}

        {activeTab === "slos" ? (
          <Panel title="SLOs" aside={<Badge label="Selected" value={selectedSloId || "none"} />}>
            <Actions>
              <button type="button" className="secondary-action" onClick={() => void evaluateSlo()}>
                Evaluate selected SLO
              </button>
            </Actions>
            <List
              items={slos}
              empty="No SLOs defined."
              renderItem={(slo) => (
                <article key={slo.id} className="card">
                  <strong>{slo.name}</strong>
                  <p>{slo.compliance_status || slo.status || "DRAFT"}</p>
                </article>
              )}
            />
          </Panel>
        ) : null}

        {activeTab === "recovery" ? (
          <Panel title="Recovery plans" aside={<Badge label="Selected" value={selectedRecoveryPlanId || "none"} />}>
            <List
              items={recoveryPlans}
              empty="No recovery plans defined."
              renderItem={(plan) => (
                <article key={plan.id} className="card">
                  <strong>{plan.name}</strong>
                  <p>{plan.status}</p>
                </article>
              )}
            />
          </Panel>
        ) : null}

        {activeTab === "reviews" ? (
          <Panel title="Post-incident reviews">
            <List
              items={postIncidentReviews}
              empty="No post-incident reviews published."
              renderItem={(review) => (
                <article key={review.id} className="card">
                  <strong>{review.title || review.summary || review.id}</strong>
                  <p>{review.status || review.publication_status || "DRAFT"}</p>
                </article>
              )}
            />
          </Panel>
        ) : null}

        {activeTab === "deployments" ? (
          <Panel title="Deployments" aside={<Badge label="Selected" value={selectedDeploymentId || "none"} />}>
            <List
              items={deployments}
              empty="No deployments recorded."
              renderItem={(deployment) => (
                <article key={deployment.id} className="card">
                  <strong>{deployment.version || deployment.release_id || deployment.id}</strong>
                  <p>{deployment.status} · {deployment.environment || deployment.environment_id}</p>
                </article>
              )}
            />
          </Panel>
        ) : null}

        {activeTab === "activity" ? (
          <Panel title="Activity stream">
            <List
              items={activity}
              empty="No activity recorded."
              renderItem={(event) => (
                <article key={event.event_id || event.id} className="card">
                  <strong>{event.event_type || event.action}</strong>
                  <p>{event.occurred_at || event.at}</p>
                </article>
              )}
            />
          </Panel>
        ) : null}

        {activeTab === "approvals" ? (
          <Panel title="Approvals">
            <p>Operational approvals are enforced in the backend and surfaced in action and deployment workflows.</p>
          </Panel>
        ) : null}

        {activeTab === "evidence" ? (
          <Panel title="Evidence">
            <p>Evidence is captured with each incident, action, recovery and deployment operation.</p>
          </Panel>
        ) : null}

        <Panel title="Current scope">
          <SectionTable
            rows={[
              ["Tenant", session?.organization_id || session?.user?.organization || "unknown"],
              ["Environment", selectedEnvironmentId || environmentDraft.type],
              ["Service", selectedServiceId || "none"],
              ["Incident", selectedIncidentId || "none"],
              ["Action", selectedActionId || "none"],
            ]}
          />
        </Panel>
      </main>
    </div>
  );
}
