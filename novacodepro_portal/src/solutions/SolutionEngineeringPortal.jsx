import React, { useEffect, useMemo, useRef, useState } from "react";

import { ROUTES } from "../platform/routes.js";
import { createSolutionEngineeringClient } from "../platform/solutionEngineeringApi.js";
import { buildUniversalAIWorkspaceModel, UniversalAIWorkspace } from "../platform/aiWorkspace.jsx";
import {
  buildSolutionProjectPath,
  isSolutionRoute,
  parseSolutionRoute,
  solutionNavigationForRole,
  SOLUTION_PROJECT_SECTIONS,
  solutionRoleCanAccessSection,
  solutionSectionLabel,
} from "../platform/solutionRoutes.js";
import { NOVACODEPRO_BUILD_INFO } from "../platform/version.js";

const LANDING_CACHE_PREFIX = "novacodepro.solution.portal.cache";

const PROJECT_SECTIONS = SOLUTION_PROJECT_SECTIONS;

const ROLE_LABELS = {
  ADMIN: "Platform Administrator",
  PLATFORM_ADMIN: "Platform Administrator",
  CUSTOMER: "Customer",
  CLIENT: "Customer",
  PARTNER: "Partner",
  CUSTOMER_APPROVER: "Customer Approver",
  BUSINESS_ANALYST: "Business Analyst",
  PRODUCT_MANAGER: "Product Manager",
  PROJECT_MANAGER: "Project Manager",
  ARCHITECT: "Architect",
  UI_UX_DESIGNER: "UI/UX Designer",
  DEVELOPER: "Developer",
  QA_ENGINEER: "QA Engineer",
  SECURITY_ENGINEER: "Security Engineer",
  PRIVACY_COMPLIANCE: "Privacy & Compliance",
  COMPLIANCE_TEAM: "Compliance Team",
  RISK_MANAGEMENT: "Risk Management",
  DEVOPS_ENGINEER: "DevOps Engineer",
  OPERATIONS_TEAM: "Operations",
  CUSTOMER_SUPPORT: "Customer Support",
  AUDIT_TEAM: "Audit",
};

function roleLabel(role) {
  return ROLE_LABELS[String(role || "").toUpperCase()] || String(role || "").replaceAll("_", " ");
}

function formatDate(value) {
  if (!value) {
    return "Not updated";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString();
}

function scopeKey(...parts) {
  return parts.map((part) => String(part || "none")).join(":");
}

function readCache(key) {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function writeCache(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // ignore cache failures
  }
}

function useConnectionState() {
  const [online, setOnline] = useState(typeof navigator === "undefined" ? true : navigator.onLine);
  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);
  return online;
}

function usePortalLoader(loaderKey, loader, deps = []) {
  const [state, setState] = useState({ status: "loading", data: null, error: null, source: "live" });
  const requestId = useRef(0);

  useEffect(() => {
    let active = true;
    const currentRequest = ++requestId.current;

    (async () => {
      try {
        setState((current) => ({ ...current, status: current.data ? "refreshing" : "loading", error: null }));
        const data = await loader();
        if (!active || requestId.current !== currentRequest) {
          return;
        }
        setState({ status: "ready", data, error: null, source: "live" });
        writeCache(loaderKey, { data, updated_at: new Date().toISOString() });
      } catch (error) {
        if (!active || requestId.current !== currentRequest) {
          return;
        }
        const cached = readCache(loaderKey);
        if (cached?.data) {
          setState({
            status: "degraded",
            data: cached.data,
            error: error instanceof Error ? error.message : String(error || "Unable to load"),
            source: "cache",
            last_successful_refresh: cached.updated_at || null,
          });
          return;
        }
        setState({
          status: "error",
          data: null,
          error: error instanceof Error ? error.message : String(error || "Unable to load"),
          source: "live",
        });
      }
    })();

    return () => {
      active = false;
    };
  }, deps);

  return [state, setState];
}

function StatusPill({ label, tone = "neutral" }) {
  return <span className={`solution-pill tone-${tone}`}>{label}</span>;
}

function Frame({ title, description, actions, children, aside }) {
  return (
    <section className="solution-frame">
      <div className="solution-frame-head">
        <div>
          <p className="section-label">{title}</p>
          <p className="studio-note">{description}</p>
        </div>
        {actions ? <div className="solution-frame-actions">{actions}</div> : null}
      </div>
      <div className={aside ? "solution-frame-body with-aside" : "solution-frame-body"}>
        <div>{children}</div>
        {aside}
      </div>
    </section>
  );
}

function EmptyState({ title, message, action }) {
  return (
    <div className="solution-empty">
      <strong>{title}</strong>
      <p>{message}</p>
      {action}
    </div>
  );
}

function ErrorState({ title, message, action }) {
  return (
    <div className="solution-state error" role="alert">
      <strong>{title}</strong>
      <p>{message}</p>
      {action}
    </div>
  );
}

function LoadingState({ label }) {
  return (
    <div className="solution-state loading" aria-live="polite">
      <strong>{label}</strong>
      <p>Loading live data from the Solution Engineering API.</p>
    </div>
  );
}

function ForbiddenState({ section, role, onHome }) {
  return (
    <div className="solution-state forbidden" role="alert">
      <strong>Access denied</strong>
      <p>
        {roleLabel(role)} cannot access {section || "this solution window"}.
      </p>
      <button type="button" className="toolbar-chip" onClick={onHome}>
        Return to accessible workspace
      </button>
    </div>
  );
}

function LifecycleRail({ lifecycle, currentStage, onNavigate }) {
  return (
    <div className="lifecycle-rail" aria-label="Project lifecycle">
      {lifecycle.map((stage, index) => {
        const state =
          stage === currentStage ? "current" : index < lifecycle.indexOf(currentStage) ? "complete" : "future";
        return (
          <button
            key={stage}
            type="button"
            className={`lifecycle-step ${state}`}
            onClick={() => onNavigate(stage)}
          >
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{stage.replaceAll("_", " ")}</strong>
          </button>
        );
      })}
    </div>
  );
}

function BadgeRow({ items }) {
  return (
    <div className="solution-badges">
      {items.map(([label, value]) => (
        <span className="solution-badge" key={`${label}-${value}`}>
          <strong>{label}</strong>
          <span>{value}</span>
        </span>
      ))}
    </div>
  );
}

function Table({ title, rows, columns }) {
  return (
    <div className="table-wrap">
      <table className="solution-table">
        <caption>{title}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row) => (
              <tr key={row.id || row.name || row.title}>
                {columns.map((column) => (
                  <td key={column}>{String(row[column] ?? row[column.toLowerCase()] ?? "")}</td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length}>
                <EmptyState title="No records" message="No live records returned from the backend yet." />
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function ProjectHeader({ project, session, routeLabel, onNavigate, healthLabel, pendingApprovals }) {
  return (
    <header className="solution-project-header">
      <div>
        <p className="section-label">Customer Solutions</p>
        <h1>{project.name}</h1>
        <p className="studio-note">
          {project.customer_name || project.customer_id || "Customer"} · {routeLabel}
        </p>
      </div>
      <div className="project-header-meta">
        <StatusPill label={project.stage || "IDEA"} tone="neutral" />
        <StatusPill label={project.environment || "development"} tone="info" />
        <StatusPill label={project.version || "1"} tone="neutral" />
        <StatusPill label={healthLabel} tone={healthLabel === "Healthy" ? "success" : "warning"} />
        <StatusPill label={`${pendingApprovals} approvals`} tone="warning" />
      </div>
      <div className="project-header-meta compact">
        <span>Owner: {project.owner || session?.display_name || "NovaCodePro"}</span>
        <span>Tenant: {project.tenant_id || session?.tenant_id || session?.organization || "unknown"}</span>
        <span>Updated: {formatDate(project.updated_at)}</span>
      </div>
      <div className="solution-project-tabs" role="tablist" aria-label="Solution project sections">
        {PROJECT_SECTIONS.map((section) => (
          <button
            key={section}
            type="button"
            className={solutionSectionLabel(section) === routeLabel ? "workspace-tab active" : "workspace-tab"}
            onClick={() => onNavigate(section)}
          >
            {solutionSectionLabel(section)}
          </button>
        ))}
      </div>
    </header>
  );
}

function AssistantPanel({ role, project, section, pendingApprovals }) {
  const prompts = {
    CUSTOMER: [
      "Turn my idea into a structured project.",
      "Explain what requires my approval.",
      "Show unresolved risks.",
    ],
    BUSINESS_ANALYST: [
      "Generate requirements from discovery.",
      "Find missing acceptance criteria.",
      "Create the target process.",
    ],
    ARCHITECT: [
      "Generate architecture from approved requirements.",
      "Create an ADR.",
      "Assess scalability risks.",
    ],
    DEVELOPER: [
      "Generate an implementation plan.",
      "Show requirements without implementation artifacts.",
      "Explain current blockers.",
    ],
    QA_ENGINEER: [
      "Generate tests for uncovered requirements.",
      "Show release blockers.",
      "Create an acceptance test plan.",
    ],
  };
  const items = prompts[String(role || "").toUpperCase()] || prompts.CUSTOMER;
  return (
    <aside className="solution-assistant">
      <p className="section-label">NovaAI Assistant</p>
      <strong>{project.name}</strong>
      <p className="studio-note">Route: {section} · Pending approvals: {pendingApprovals}</p>
      <div className="assistant-prompt-list">
        {items.map((item) => (
          <div className="assistant-prompt" key={item}>
            {item}
          </div>
        ))}
      </div>
    </aside>
  );
}

function ActivityPanel({ timeline, evidence }) {
  return (
    <aside className="solution-activity">
      <p className="section-label">Activity</p>
      <div className="timeline-list">
        {(timeline || []).slice(0, 5).map((entry) => (
          <div className="timeline-item" key={`${entry.at}-${entry.action}`}>
            <strong>{entry.action}</strong>
            <span>{formatDate(entry.at)}</span>
          </div>
        ))}
        {!timeline?.length ? <span className="muted">No activity yet.</span> : null}
      </div>
      <p className="section-label">Evidence</p>
      <div className="timeline-list">
        {(evidence || []).slice(0, 4).map((item) => (
          <div className="timeline-item" key={item.id}>
            <strong>{item.category || item.type || "Evidence"}</strong>
            <span>{item.evidence_hash || item.hash || item.id}</span>
          </div>
        ))}
        {!evidence?.length ? <span className="muted">No evidence yet.</span> : null}
      </div>
    </aside>
  );
}

function LandingPage({
  session,
  summaryState,
  customersState,
  projectsState,
  filters,
  setFilters,
  onCreateCustomer,
  onCreateProject,
  onOpenProject,
  onContinuePending,
  onReviewApprovals,
  onViewOperations,
  onNavigate,
}) {
  const projects = projectsState.data?.projects || projectsState.data || [];
  const customers = customersState.data || [];
  const summary = summaryState.data || {};
  const stages = Array.isArray(summary.projects_by_stage)
    ? summary.projects_by_stage
    : Array.from(
        projects.reduce((accumulator, project) => {
          const stage = String(project.stage || "IDEA");
          accumulator.set(stage, (accumulator.get(stage) || 0) + 1);
          return accumulator;
        }, new Map()),
        ([stage, count]) => ({ stage, count }),
      );

  return (
    <div className="solution-landing">
      <section className="solution-hero">
        <div>
          <p className="section-label">Customer Solutions</p>
          <h1>NovaCodePro Enterprise Solution Engineering</h1>
          <p className="studio-note">
            Browser-connected lifecycle from discovery through operations, support, and knowledge.
          </p>
          <BadgeRow
            items={[
              ["Customers", String(customers.length)],
              ["Projects", String(projects.length)],
              ["Approvals", String(summary.pending_approvals ?? 0)],
              ["Deploying", String(summary.deployments_in_progress ?? 0)],
              ["Acceptance", String(summary.acceptance_pending ?? 0)],
              ["Support", String(summary.open_support_cases ?? 0)],
            ]}
          />
        </div>
        <div className="solution-hero-actions">
          <button type="button" className="primary-action" onClick={onCreateCustomer}>
            Create Customer
          </button>
          <button type="button" className="toolbar-chip" onClick={onCreateProject}>
            Create Project
          </button>
          <button type="button" className="toolbar-chip" onClick={onReviewApprovals}>
            Review Approvals
          </button>
          <button type="button" className="toolbar-chip" onClick={onViewOperations}>
            View Operations
          </button>
        </div>
      </section>

      <section className="solution-toolbar">
        <label className="field">
          <span>Customer</span>
          <select value={filters.customerId} onChange={(event) => setFilters((current) => ({ ...current, customerId: event.target.value }))}>
            <option value="">All</option>
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.name || customer.id}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Lifecycle state</span>
          <input
            value={filters.stage}
            onChange={(event) => setFilters((current) => ({ ...current, stage: event.target.value }))}
            placeholder="REQUIREMENTS_APPROVED"
          />
        </label>
        <label className="field">
          <span>Owner</span>
          <input
            value={filters.owner}
            onChange={(event) => setFilters((current) => ({ ...current, owner: event.target.value }))}
            placeholder="Project owner"
          />
        </label>
        <label className="field">
          <span>Environment</span>
          <input
            value={filters.environment}
            onChange={(event) => setFilters((current) => ({ ...current, environment: event.target.value }))}
            placeholder="pilot"
          />
        </label>
      </section>

      <div className="solution-landing-grid">
        <Frame
          title="Lifecycle board"
          description="Live projects by stage."
          actions={<button className="toolbar-chip" onClick={() => onNavigate("projects")}>Projects</button>}
        >
          <div className="board-list">
            {stages.map((stage) => (
              <div className="board-column" key={stage.stage}>
                <strong>{stage.stage}</strong>
                <span>{stage.count} projects</span>
              </div>
            ))}
            {!stages.length ? <EmptyState title="No lifecycle data" message="The backend has not returned stage counts yet." /> : null}
          </div>
        </Frame>
        <Frame title="Projects" description="Open the governed browser lifecycle." aside={<AssistantPanel role={session?.active_role} project={{ name: "NovaCodePro" }} section="overview" pendingApprovals={summary.pending_approvals ?? 0} />}>
          <Table
            title="Projects"
            columns={["name", "stage", "owner", "environment", "updated_at"]}
            rows={projects
              .filter((project) => {
                if (filters.customerId && project.customer_id !== filters.customerId) return false;
                if (filters.stage && String(project.stage || "").toUpperCase() !== String(filters.stage || "").toUpperCase()) return false;
                if (filters.owner && !String(project.owner || "").toLowerCase().includes(filters.owner.toLowerCase())) return false;
                if (filters.environment && !String(project.environment || "").toLowerCase().includes(filters.environment.toLowerCase())) return false;
                return true;
              })
              .map((project) => ({
                ...project,
                updated_at: formatDate(project.updated_at),
              }))}
          />
          <div className="solution-inline-actions">
            {projects.slice(0, 5).map((project) => (
              <button key={project.id} type="button" className="toolbar-chip" onClick={() => onOpenProject(project.id)}>
                Open {project.name}
              </button>
            ))}
          </div>
          <div className="solution-inline-actions">
            <button type="button" className="toolbar-chip" onClick={onContinuePending}>Continue Pending Work</button>
          </div>
        </Frame>
      </div>
    </div>
  );
}

function ProjectSection({
  section,
  project,
  reloadProject,
  client,
  session,
  navigateToSection,
  workflowState,
  setWorkflowPrompt,
  workflowPrompt,
  setStatusMessage,
  currentProjectId,
  summaryState,
}) {
  const requirements = project.requirements || [];
  const blueprint = project.blueprint;
  const architecture = project.architecture;
  const release = project.release;
  const acceptance = project.acceptance;
  const supportCases = project.support_cases || [];
  const enhancements = project.enhancements || [];
  const knowledge = project.knowledge || [];
  const evidence = project.evidence || [];
  const timeline = workflowState?.timeline || project.timeline || [];
  const workflows = workflowState?.workflows || [];
  const workflow = workflowState?.workflow || null;

  const pendingApprovals =
    [
      blueprint?.sections?.filter((item) => item.status !== "APPROVED").length || 0,
      project.approvals?.filter((item) => item.status !== "APPROVED").length || 0,
      release?.status === "APPROVED" ? 0 : release ? 1 : 0,
    ].reduce((total, value) => total + value, 0);

  const handleAction = async (message, action) => {
    setStatusMessage(message);
    try {
      await action();
      await reloadProject();
      setStatusMessage(`${message} completed.`);
    } catch (error) {
      setStatusMessage(error.message || String(error || "Request failed"));
      throw error;
    }
  };

  const onConfirmingAction = async (label, action) => {
    if (window.confirm(`Confirm ${label} for ${project.name}?`)) {
      await handleAction(label, action);
    }
  };

  const lifecycleIndex = PROJECT_SECTIONS.indexOf(section);
  const routeLabel = solutionSectionLabel(section);

  const sideRail = (
    <>
      <AssistantPanel role={session?.active_role} project={project} section={section} pendingApprovals={pendingApprovals} />
      <ActivityPanel timeline={timeline} evidence={evidence} />
    </>
  );

  if (section === "dashboard") {
    return (
      <Frame
        title="Project Dashboard"
        description="Live lifecycle, approvals, evidence, and operations."
        aside={sideRail}
        actions={
          <>
            <button type="button" className="toolbar-chip" onClick={() => navigateToSection("discovery")}>Discovery</button>
            <button type="button" className="toolbar-chip" onClick={() => navigateToSection("requirements")}>Requirements</button>
            <button type="button" className="toolbar-chip" onClick={() => navigateToSection("approvals")}>Approvals</button>
          </>
        }
      >
        <LifecycleRail lifecycle={PROJECT_SECTIONS} currentStage={section} onNavigate={navigateToSection} />
        <BadgeRow
          items={[
            ["Project", project.name],
            ["Stage", project.stage || "IDEA"],
            ["Version", project.version || "1"],
            ["Health", project.health || "Healthy"],
            ["Pending approvals", String(pendingApprovals)],
            ["Evidence", String(evidence.length)],
          ]}
        />
        <div className="solution-grid">
          <section className="solution-card">
            <p className="section-label">Project summary</p>
            <strong>{project.summary || project.idea || project.request || "No summary yet."}</strong>
            <p className="studio-note">Customer: {project.customer_name || project.customer_id || "Unknown"}</p>
          </section>
          <section className="solution-card">
            <p className="section-label">Latest deliverables</p>
            <div className="solution-list">
              {(project.deliverables || []).slice(0, 5).map((item) => (
                <div className="solution-list-item" key={item.id || item.title}>
                  <strong>{item.title || item.name || item.id}</strong>
                  <span>{item.status || item.stage || "Draft"}</span>
                </div>
              ))}
              {!project.deliverables?.length ? <EmptyState title="No deliverables" message="Deliverables will appear when the backend records them." /> : null}
            </div>
          </section>
        </div>
      </Frame>
    );
  }

  if (section === "discovery") {
    return (
      <Frame
        title="Discovery Workspace"
        description="Capture idea, problem statement, objectives, and discovery summary."
        aside={sideRail}
        actions={
          <>
            <button type="button" className="primary-action" onClick={() => onConfirmingAction("Submit idea", () => client.submitIdea(currentProjectId, {
              title: project.name,
              problem: project.summary || project.idea || "Problem statement",
              target_users: project.target_users || [],
              market: project.market || "",
              industry: project.industry || "",
            }))}>
              Save Draft
            </button>
            <button type="button" className="toolbar-chip" onClick={() => onConfirmingAction("Run discovery", () => client.runDiscovery(currentProjectId, {
              template: "enterprise",
              discovery_summary: project.discovery_summary || project.summary || "",
              objectives: project.objectives || [],
              stakeholders: project.stakeholders || [],
              follow_up_questions: project.follow_up_questions || [],
            }))}>
              Generate Discovery Summary
            </button>
          </>
        }
      >
        <div className="solution-grid">
          <section className="solution-card">
            <p className="section-label">Business idea</p>
            <strong>{project.idea || project.summary || "No idea submitted yet."}</strong>
            <p className="studio-note">Workflow state: {project.stage || "IDEA"}</p>
          </section>
          <section className="solution-card">
            <p className="section-label">Discovery summary</p>
            <p>{project.discovery_summary || "Run discovery to populate the structured summary."}</p>
            <div className="solution-list">
              {(project.follow_up_questions || []).slice(0, 5).map((item) => (
                <div className="solution-list-item" key={item}>
                  <strong>{item}</strong>
                </div>
              ))}
            </div>
          </section>
        </div>
      </Frame>
    );
  }

  if (section === "requirements") {
    return (
      <Frame
        title="Requirements Studio"
        description="Versioned requirements, traceability, and approvals."
        aside={sideRail}
        actions={
          <>
            <button type="button" className="primary-action" onClick={() => onConfirmingAction("Create requirement", () => client.createRequirement(currentProjectId, {
              summary: workflowPrompt || "New requirement",
              kind: "functional",
              priority: "medium",
              version: String((requirements.length || 0) + 1),
            }))}>
              Create Requirement
            </button>
            <button type="button" className="toolbar-chip" onClick={() => onConfirmingAction("Approve requirements", () => client.approveRequirements(currentProjectId))}>
              Approve Requirements
            </button>
          </>
        }
      >
        <Table title="Requirements" columns={["summary", "kind", "priority", "version", "status"]} rows={requirements} />
        <div className="solution-inline-actions">
          <button type="button" className="toolbar-chip" onClick={() => navigateToSection("approvals")}>Open Approval Trail</button>
          <button type="button" className="toolbar-chip" onClick={() => navigateToSection("architecture")}>Trace to Architecture</button>
        </div>
      </Frame>
    );
  }

  if (section === "business-analysis") {
    return (
      <Frame title="Business Analysis Studio" description="Current state, target state, and value stream." aside={sideRail}>
        <div className="solution-grid">
          <section className="solution-card">
            <p className="section-label">Stakeholder map</p>
            <div className="solution-list">
              {(project.stakeholders || []).map((item) => (
                <div className="solution-list-item" key={item}>
                  <strong>{item}</strong>
                </div>
              ))}
              {!project.stakeholders?.length ? <EmptyState title="No stakeholders" message="Stakeholders will appear after discovery." /> : null}
            </div>
          </section>
          <section className="solution-card">
            <p className="section-label">Current-state process</p>
            <p>{project.current_process || project.discovery_summary || "No current-state process stored yet."}</p>
          </section>
          <section className="solution-card">
            <p className="section-label">Target-state process</p>
            <p>{project.target_process || project.blueprint?.business_processes?.[0]?.name || "No target-state process stored yet."}</p>
          </section>
          <section className="solution-card">
            <p className="section-label">Workflow fabric</p>
            <div className="solution-list">
              {(workflows || []).slice(0, 4).map((item) => (
                <div className="solution-list-item" key={item.id}>
                  <strong>{item.title || item.name}</strong>
                  <span>{item.lifecycle || item.status}</span>
                </div>
              ))}
              {!workflows?.length ? <EmptyState title="No workflow fabric data" message="Workflow Fabric will populate once workflows are created." /> : null}
            </div>
          </section>
        </div>
      </Frame>
    );
  }

  if (section === "ux-ui") {
    return (
      <Frame
        title="UX/UI Studio"
        description="Design artifacts, responsive states, accessibility, and prototypes."
        aside={sideRail}
        actions={
          <button
            type="button"
            className="primary-action"
            onClick={() =>
              onConfirmingAction("Create design artifact", () =>
                client.createDesign(currentProjectId, {
                  artifact_type: "wireframe",
                  surface: "web",
                  requirements: requirements.map((item) => item.id),
                  prototype_links: [],
                }))
            }
          >
            Create Design Artifact
          </button>
        }
      >
        <Table title="Designs" columns={["artifact_type", "surface", "status", "version"]} rows={project.designs || []} />
        <div className="solution-inline-actions">
          <button type="button" className="toolbar-chip" onClick={() => navigateToSection("requirements")}>Link Requirements</button>
          <button type="button" className="toolbar-chip" onClick={() => navigateToSection("architecture")}>Review Architecture</button>
        </div>
      </Frame>
    );
  }

  if (section === "architecture") {
    return (
      <Frame
        title="Architecture Studio"
        description="Architecture summary, decision records, and approvals."
        aside={sideRail}
        actions={
          <>
            <button type="button" className="primary-action" onClick={() => onConfirmingAction("Approve architecture", () => client.approveArchitecture(currentProjectId))}>
              Approve Architecture
            </button>
          </>
        }
      >
        <section className="solution-card">
          <p className="section-label">Architecture summary</p>
          <strong>{architecture?.decision || "No architecture decision recorded yet."}</strong>
          <p className="studio-note">
            Requirements: {(architecture?.requirements || []).length} · Risks: {(architecture?.risks || []).length}
          </p>
        </section>
        <div className="solution-grid">
          <section className="solution-card">
            <p className="section-label">Trust boundaries</p>
            <div className="solution-list">
              {(architecture?.policies || []).map((item) => (
                <div className="solution-list-item" key={item}>
                  <strong>{item}</strong>
                </div>
              ))}
            </div>
          </section>
          <section className="solution-card">
            <p className="section-label">Evidence</p>
            <div className="solution-list">
              {(architecture?.evidence || []).map((item) => (
                <div className="solution-list-item" key={item}>
                  <strong>{item}</strong>
                </div>
              ))}
            </div>
          </section>
        </div>
      </Frame>
    );
  }

  if (section === "engineering") {
    return (
      <Frame title="Engineering Studio" description="Implementation plan and generated artifacts." aside={sideRail}>
        <div className="solution-grid">
          <section className="solution-card">
            <p className="section-label">Implementation plan</p>
            <strong>{project.release?.name || "No release plan yet."}</strong>
            <p className="studio-note">Repository not connected if no source control information is returned by the backend.</p>
          </section>
          <section className="solution-card">
            <p className="section-label">Generated artifacts</p>
            <div className="solution-list">
              {(project.artifacts || []).slice(0, 6).map((item) => (
                <div className="solution-list-item" key={item.id}>
                  <strong>{item.title || item.name || item.id}</strong>
                  <span>{item.review_status || item.status || "Draft"}</span>
                </div>
              ))}
              {!project.artifacts?.length ? <EmptyState title="Repository not connected" message="The backend does not expose repository records for this project yet." /> : null}
            </div>
          </section>
        </div>
      </Frame>
    );
  }

  if (section === "quality") {
    return (
      <Frame title="Quality Studio" description="Test executions and quality status." aside={sideRail}>
        <div className="solution-card">
          <p className="section-label">Tests</p>
          <Table title="Tests" columns={["suite", "status", "created_at"]} rows={project.tests || []} />
        </div>
      </Frame>
    );
  }

  if (section === "security") {
    return (
      <Frame
        title="Security Studio"
        description="Security review, findings, and release readiness."
        aside={sideRail}
        actions={
          <button type="button" className="primary-action" onClick={() => onConfirmingAction("Run security review", () => client.runSecurityReview(currentProjectId, { status: "APPROVED" }))}>
            Start Security Review
          </button>
        }
      >
        <section className="solution-card">
          <p className="section-label">Security status</p>
          <strong>{project.security_review?.status || "Pending"}</strong>
        </section>
      </Frame>
    );
  }

  if (section === "compliance-risk") {
    return (
      <Frame
        title="Compliance & Risk Studio"
        description="Compliance obligations and risk records."
        aside={sideRail}
        actions={
          <button type="button" className="primary-action" onClick={() => onConfirmingAction("Run compliance review", () => client.runComplianceReview(currentProjectId, { status: "APPROVED" }))}>
            Start Compliance Review
          </button>
        }
      >
        <section className="solution-card">
          <p className="section-label">Compliance</p>
          <strong>{project.compliance_review?.status || "Pending"}</strong>
        </section>
      </Frame>
    );
  }

  if (section === "releases") {
    return (
      <Frame
        title="Release Studio"
        description="Release scope, blocker status, approval, and notes."
        aside={sideRail}
        actions={
          <button type="button" className="primary-action" onClick={() => onConfirmingAction("Create release", () => client.createRelease(currentProjectId, { name: `${project.name} Release`, version: String((release?.version || 0) || 1), environment: project.environment || "development" }))}>
            Create Release
          </button>
        }
      >
        <section className="solution-card">
          <p className="section-label">Release state</p>
          <strong>{release?.status || "No release yet"}</strong>
          <p className="studio-note">{release?.rollback_plan || "Rollback plan not captured yet."}</p>
        </section>
      </Frame>
    );
  }

  if (section === "deployments") {
    return (
      <Frame
        title="Deployment Studio"
        description="Deployment plan, evidence, and verified rollout."
        aside={sideRail}
        actions={
          <button type="button" className="primary-action" onClick={() => onConfirmingAction("Deploy release", () => client.deployRelease(release?.id, { environment: project.environment || "development", verification: { source: "portal" } }))}>
            Start Deployment
          </button>
        }
      >
        <section className="solution-card">
          <p className="section-label">Deployment</p>
          <strong>{project.deployment?.status || release?.status || "Not deployed"}</strong>
          <p className="studio-note">The portal waits for authoritative server confirmation after deployment.</p>
        </section>
      </Frame>
    );
  }

  if (section === "acceptance") {
    return (
      <Frame
        title="Customer Acceptance Portal"
        description="Version-specific customer acceptance and evidence review."
        aside={sideRail}
        actions={
          <button type="button" className="primary-action" onClick={() => onConfirmingAction("Accept release", () => client.acceptRelease(release?.id, { decision: "ACCEPTED", version: release?.version }))}>
            Accept Delivery
          </button>
        }
      >
        <section className="solution-card">
          <p className="section-label">Acceptance</p>
          <strong>{acceptance?.status || "Pending"}</strong>
          <p className="studio-note">Acceptance applies only to the selected release version.</p>
        </section>
      </Frame>
    );
  }

  if (section === "operations") {
    return (
      <Frame title="Operations Layer" description="Service health, incidents, evidence, and support." aside={sideRail}>
        <div className="solution-grid">
          <section className="solution-card">
            <p className="section-label">Operational health</p>
            <strong>{project.health || "Healthy"}</strong>
            <p className="studio-note">Read-only customer visibility with controlled actions from the backend only.</p>
          </section>
          <section className="solution-card">
            <p className="section-label">Incidents</p>
            <strong>{project.incidents?.length || 0}</strong>
          </section>
        </div>
      </Frame>
    );
  }

  if (section === "support") {
    return (
      <Frame title="Support and Evolution" description="Support cases and enhancement requests." aside={sideRail}>
        <div className="solution-grid">
          <section className="solution-card">
            <p className="section-label">Support cases</p>
            <Table title="Support cases" columns={["title", "status", "severity"]} rows={supportCases} />
          </section>
          <section className="solution-card">
            <p className="section-label">Enhancements</p>
            <Table title="Enhancements" columns={["title", "status", "priority"]} rows={enhancements} />
          </section>
        </div>
      </Frame>
    );
  }

  if (section === "workflows") {
    return (
      <Frame
        title="Workflow Fabric"
        description="API-connected workflow summary, validation, approval, deploy, replay, and evidence."
        aside={sideRail}
        actions={
          <>
            <button type="button" className="primary-action" onClick={() => onConfirmingAction("Generate workflow", () => client.generateWorkflow({ prompt: workflowPrompt || project.summary || project.name }))}>
              Generate Workflow from Prompt
            </button>
            {workflow ? (
              <>
                <button type="button" className="toolbar-chip" onClick={() => onConfirmingAction("Validate workflow", () => client.validateWorkflow(workflow.id))}>Validate</button>
                <button type="button" className="toolbar-chip" onClick={() => onConfirmingAction("Compile workflow", () => client.compileWorkflow(workflow.id))}>Compile</button>
              </>
            ) : null}
          </>
        }
      >
        <div className="solution-grid">
          <section className="solution-card">
            <p className="section-label">Workflow list</p>
            <Table title="Workflows" columns={["title", "status", "lifecycle"]} rows={workflows} />
          </section>
          <section className="solution-card">
            <p className="section-label">Timeline</p>
            <div className="solution-list">
              {(workflowState?.timeline || []).slice(0, 6).map((entry) => (
                <div className="solution-list-item" key={`${entry.at}-${entry.action}`}>
                  <strong>{entry.action}</strong>
                  <span>{formatDate(entry.at)}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </Frame>
    );
  }

  if (section === "approvals") {
    return (
      <Frame title="Approvals" description="Unified approvals across the delivery lifecycle." aside={sideRail}>
        <Table
          title="Approvals"
          columns={["type", "status", "required_role", "version"]}
          rows={[
            { type: "Requirements", status: project.stage || "Pending", required_role: "BUSINESS_ANALYST", version: project.version || "1" },
            { type: "Architecture", status: architecture?.status || "Pending", required_role: "ARCHITECT", version: project.version || "1" },
            { type: "Release", status: release?.status || "Pending", required_role: "PROJECT_MANAGER", version: release?.version || "1" },
            { type: "Acceptance", status: acceptance?.status || "Pending", required_role: "CUSTOMER_APPROVER", version: release?.version || "1" },
          ]}
        />
      </Frame>
    );
  }

  if (section === "knowledge") {
    return (
      <Frame title="Knowledge" description="Approved reusable project knowledge." aside={sideRail}>
        <Table title="Knowledge" columns={["category", "title", "status"]} rows={knowledge} />
      </Frame>
    );
  }

  if (section === "evidence") {
    return (
      <Frame title="Evidence" description="Immutable evidence trail for the project." aside={sideRail}>
        <Table title="Evidence" columns={["category", "evidence_hash", "status"]} rows={evidence} />
      </Frame>
    );
  }

  return null;
}

export function SolutionEngineeringPortal({
  session,
  pathname,
  navigate,
  baseUrl,
  onLogout,
}) {
  const role = String(session?.active_role || "").toUpperCase();
  const route = useMemo(() => parseSolutionRoute(pathname), [pathname]);
  const online = useConnectionState();
  const client = useMemo(() => createSolutionEngineeringClient({ baseUrl, session }), [baseUrl, session]);
  const [filters, setFilters] = useState({ customerId: "", stage: "", owner: "", environment: "" });
  const [workflowPrompt, setWorkflowPrompt] = useState("Design a governed customer solution workflow.");
  const [statusMessage, setStatusMessage] = useState("");
  const [landingState, setLandingState] = useState({ status: "loading", data: null, error: null, source: "live" });
  const [customersState, setCustomersState] = useState({ status: "loading", data: [], error: null, source: "live" });
  const [projectsState, setProjectsState] = useState({ status: "loading", data: [], error: null, source: "live" });
  const [projectState, setProjectState] = useState({ status: "loading", data: null, error: null, source: "live" });
  const [workflowState, setWorkflowState] = useState({ status: "loading", data: null, error: null, source: "live" });
  const [selectedProjectId, setSelectedProjectId] = useState(() => {
    try {
      return window.sessionStorage.getItem("novacodepro.solution.selectedProjectId") || "";
    } catch {
      return "";
    }
  });

  const summaryLoaderKey = `${LANDING_CACHE_PREFIX}:${session?.tenant_id || session?.organization || "default"}:summary`;
  const customerLoaderKey = `${LANDING_CACHE_PREFIX}:${session?.tenant_id || session?.organization || "default"}:customers`;
  const projectLoaderKey = `${LANDING_CACHE_PREFIX}:${session?.tenant_id || session?.organization || "default"}:${selectedProjectId || route?.projectId || "landing"}`;

  const [summaryState, setSummaryState] = usePortalLoader(
    summaryLoaderKey,
    () => client.getPlatformSummary(),
    [session?.tenant_id, session?.organization],
  );
  const [liveCustomersState, setLiveCustomersState] = usePortalLoader(
    customerLoaderKey,
    () => client.listCustomers(),
    [session?.tenant_id, session?.organization],
  );
  const [liveProjectsState, setLiveProjectsState] = usePortalLoader(
    `${LANDING_CACHE_PREFIX}:${session?.tenant_id || session?.organization || "default"}:projects`,
    () => client.listProjects(),
    [session?.tenant_id, session?.organization],
  );

  useEffect(() => {
    setLandingState(summaryState);
    setCustomersState(liveCustomersState);
    setProjectsState(liveProjectsState);
  }, [summaryState, liveCustomersState, liveProjectsState]);

  useEffect(() => {
    if (route?.kind === "project" && route.projectId) {
      setSelectedProjectId(route.projectId);
      try {
        window.sessionStorage.setItem("novacodepro.solution.selectedProjectId", route.projectId);
      } catch {
        // ignore
      }
    }
  }, [route?.kind, route?.projectId]);

  const loadProject = async (projectId) => {
    const project = await client.getProject(projectId);
    const timeline = await client.getTimeline(projectId);
    let workflowSummary = null;
    let workflows = [];
    try {
      workflowSummary = await client.getWorkflowFabricSummary();
      workflows = await client.listWorkflows();
    } catch {
      workflowSummary = null;
      workflows = [];
    }
    setProjectState({ status: "ready", data: project, error: null, source: "live" });
    setWorkflowState({
      status: "ready",
      data: { timeline: timeline?.timeline || timeline || [], workflowSummary, workflows },
      error: null,
      source: "live",
    });
    writeCache(projectLoaderKey, { data: project, updated_at: new Date().toISOString() });
    return project;
  };

  useEffect(() => {
    let active = true;
    if (route?.kind !== "project" || !route.projectId) {
      setProjectState({ status: "idle", data: null, error: null, source: "live" });
      setWorkflowState({ status: "idle", data: null, error: null, source: "live" });
      return () => {
        active = false;
      };
    }
    setProjectState((current) => ({ ...current, status: "loading" }));
    setWorkflowState((current) => ({ ...current, status: "loading" }));
    loadProject(route.projectId)
      .then(() => {
        if (!active) {
          return;
        }
      })
      .catch((error) => {
        if (!active) {
          return;
        }
        const cached = readCache(projectLoaderKey);
        if (cached?.data) {
          setProjectState({
            status: "degraded",
            data: cached.data,
            error: error instanceof Error ? error.message : String(error || "Unable to load project"),
            source: "cache",
            last_successful_refresh: cached.updated_at || null,
          });
          return;
        }
        setProjectState({
          status: "error",
          data: null,
          error: error instanceof Error ? error.message : String(error || "Unable to load project"),
          source: "live",
        });
      });
    return () => {
      active = false;
    };
  }, [route?.kind, route?.projectId, session?.tenant_id, session?.organization, projectLoaderKey]);

  const currentProject = projectState.data;
  const roleNavigation = useMemo(() => solutionNavigationForRole(role), [role]);
  const currentSection = route?.kind === "project" ? route.section : route?.section || "overview";

  const navigateTo = (path) => {
    navigate(path);
  };

  const openProject = (projectId, section = "dashboard") => navigate(buildSolutionProjectPath(projectId, section));

  const continuePending = () => {
    const nextProject = (projectsState.data || []).find((project) => String(project.stage || "").toUpperCase() !== "OPERATING");
    if (nextProject) {
      openProject(nextProject.id);
    }
  };

  const createCustomer = async () => {
    const name = window.prompt("Customer name");
    if (!name) {
      return;
    }
    const record = await client.createCustomer({
      tenant_id: session?.tenant_id || session?.organization || "novacodepro",
      organization_id: session?.organization || session?.tenant_id || "novacodepro",
      name,
      segment: "enterprise",
      country: window.prompt("Country code", "AU") || "AU",
    });
    setStatusMessage(`Created customer ${record.name || record.id}`);
    await client.getPlatformSummary().then((data) => setSummaryState({ status: "ready", data, error: null, source: "live" }));
    await client.listCustomers().then((data) => setCustomersState({ status: "ready", data, error: null, source: "live" }));
  };

  const createProject = async () => {
    const name = window.prompt("Project name");
    if (!name) {
      return;
    }
    const idea = window.prompt("Business idea", "Build a multilingual customer portal.") || "Build a multilingual customer portal.";
    const project = await client.createProject({
      tenant_id: session?.tenant_id || session?.organization || "novacodepro",
      organization_id: session?.organization || session?.tenant_id || "novacodepro",
      name,
      idea,
    });
    setStatusMessage(`Created project ${project.name || project.id}`);
    await client.getPlatformSummary().then((data) => setSummaryState({ status: "ready", data, error: null, source: "live" }));
    await client.listProjects().then((data) => setProjectsState({ status: "ready", data, error: null, source: "live" }));
    openProject(project.id);
  };

  const reloadProject = async () => {
    if (route?.kind !== "project" || !route.projectId) {
      return;
    }
    await loadProject(route.projectId);
  };

  const loadLanding = landingState.status === "loading" || customersState.status === "loading" || projectsState.status === "loading";

  if (route && !isSolutionRoute(pathname)) {
    return null;
  }

  if (!solutionRoleCanAccessSection(role, route?.kind === "project" ? route.section : route?.section || "overview")) {
    return <ForbiddenState section={route?.section || "Customer Solutions"} role={role} onHome={() => navigate(ROUTES.dashboard)} />;
  }

  if (route?.kind === "project" && route.projectId && projectState.status === "loading" && !projectState.data) {
    return <LoadingState label="Loading solution project" />;
  }

  if (route?.kind === "project" && projectState.status === "error" && !projectState.data) {
    return (
      <ErrorState
        title="Project not found"
        message={projectState.error || "The selected project could not be loaded."}
        action={<button type="button" className="toolbar-chip" onClick={() => navigate(ROUTES.solutionRoot)}>Go to Customer Solutions</button>}
      />
    );
  }

  const project = currentProject || {
    id: route?.projectId || "",
    name: "Customer project",
    stage: "IDEA",
    environment: "development",
    version: "1",
    owner: session?.display_name || "NovaCodePro",
    tenant_id: session?.tenant_id || session?.organization || "novacodepro",
    summary: "",
    requirements: [],
    timeline: [],
    deliverables: [],
    evidence: [],
    support_cases: [],
    enhancements: [],
    knowledge: [],
    approvals: [],
  };

  const currentWindowTitle = route?.kind === "project" ? solutionSectionLabel(route.section) : "Overview";
  const solutionAiModel = useMemo(
    () =>
      buildUniversalAIWorkspaceModel({
        session,
        role,
        roleLabel: roleLabel(role),
        workspace: "Customer Solutions",
        project: project.name,
        tenant: session?.tenant_id || session?.organization,
        organization: session?.organization,
        environment: project.environment,
        route: currentWindowTitle,
        modelLabel: "NovaCodePro portal",
        statusLabel: online ? "Live project data" : "Offline",
        connection: {
          connected: false,
          backend: false,
          runtime: true,
          reason: "NovaAI backend is not connected in the portal yet.",
          lastSyncedAt: project.updated_at || null,
        },
        request: {
          id: project.id,
          title: project.name,
          request: project.idea || project.summary || "",
          status: project.stage || "IDEA",
          summary: project.discovery_summary || project.summary || "Project context loaded from live backend data.",
          confidence: null,
          intent: route?.kind === "project" ? route.section : "overview",
          outcome: project.summary || project.idea || "",
          scope: project.scope || project.surfaces || "Not connected",
          tools: [route?.section || "overview"],
          approvals: project.approvals || [],
          questions: project.follow_up_questions || [],
          files: project.attachments || [],
          approvalsState: (project.approvals || []).length ? "PENDING" : "NOT_REQUIRED",
        },
        requestState: project.stage || "IDEA",
        requestSummary: project.discovery_summary || project.summary || "",
        requestOutcome: project.summary || project.idea || "",
        requestScope: project.scope || project.surfaces || "Not connected",
        requestTools: [route?.section || "overview"],
        requestApprovals: project.approvals || [],
        requestQuestions: project.follow_up_questions || [],
        requestFiles: project.attachments || [],
        requestArtifacts: [
          ...(project.requirements || []),
          ...(project.designs || []),
          ...(project.deliverables || []),
        ],
        requestApprovalsState: (project.approvals || []).length ? "PENDING" : "NOT_REQUIRED",
        executionState: workflowState.data?.workflowSummary?.status || project.stage || "IDEA",
        knowledgeState: (project.knowledge || []).length ? "PUBLISHED" : "DRAFT",
        currentAgentTasks: [],
        conversations: project.timeline || [],
        savedPrompts: [project.idea || project.summary || "Open project"],
        approvedSolutions: project.deliverables || [],
        sharedConversations: [],
        recentRequests: project.support_cases || [],
        suggestedPrompts: [
          "Ask NovaAI about this project",
          "Generate a discovery summary",
          "Review pending approvals",
          "Compare versions",
        ],
        artifacts: [
          ...(project.requirements || []),
          ...(project.designs || []),
          ...(project.deliverables || []),
          ...(project.evidence || []),
        ],
        timeline: workflowState.data?.timeline || project.timeline || [],
        approvals: project.approvals || [],
        evidence: project.evidence || [],
        knowledge: project.knowledge || [],
        policies: summaryState.data?.policy_summary || [],
        standards: workflowState.data?.workflowSummary?.standards || [],
        context: {
          customer: project.customer_name || project.customer_id || "Unknown",
          project: project.name,
          repository: project.repository || "Not connected",
          branch: project.branch || "Not connected",
          commit: project.commit || "Not connected",
          activeArtifact: project.designs?.[0]?.title || project.requirements?.[0]?.summary || "Not connected",
          planSummary: project.summary || project.discovery_summary || "",
          filesChanged: (project.designs || []).length || "Not connected",
          apisChanged: "Not connected",
          migrations: "Not connected",
          testsAdded: (project.tests || []).length || "Not connected",
          securityResult: project.security_review?.status || "Not assessed",
          complianceResult: project.compliance_review?.status || "Not assessed",
          rollbackPlan: project.release?.rollback_plan || "Not connected",
          riskLevel: project.risk_level || "medium",
          complianceImpact: project.compliance_status || "Not assessed",
          currentStep: route?.section || project.stage || "overview",
          queuedSteps: project.timeline?.length || 0,
          failedSteps: project.timeline?.filter((entry) => String(entry.status || "").toLowerCase() === "failed").length || 0,
          cancelledSteps: project.timeline?.filter((entry) => String(entry.status || "").toLowerCase() === "cancelled").length || 0,
          retries: workflowState.data?.workflowSummary?.retryQueue || 0,
          estimatedRemaining: project.stage || "Not connected",
        },
        metrics: {
          customers: customersState.data?.length || 0,
          projects: projectsState.data?.length || 0,
          approvals: (project.approvals || []).length,
          evidence: (project.evidence || []).length,
        },
        supportedActions: {
          ask: true,
          plan: true,
          generate: true,
          analyze: true,
          review: true,
          compare: true,
          createWorkflow: true,
        },
      }),
    [
      currentWindowTitle,
      customersState.data,
      online,
      projectsState.data,
      project,
      role,
      session,
      summaryState.data,
      workflowState.data,
    ],
  );
  const portalAiNotice = "NovaAI backend is not connected yet. Live project context is available.";
  const portalAiActions = {
    ask: () => setStatusMessage(portalAiNotice),
    plan: () => setStatusMessage(portalAiNotice),
    generate: () => setStatusMessage(portalAiNotice),
    analyze: () => setStatusMessage(portalAiNotice),
    review: () => setStatusMessage(portalAiNotice),
    compare: () => setStatusMessage(portalAiNotice),
    createWorkflow: () => setStatusMessage(portalAiNotice),
    cancel: () => setStatusMessage("Request cancelled locally."),
    confirmInterpretation: () => setStatusMessage(portalAiNotice),
    correctInterpretation: () => setStatusMessage(portalAiNotice),
    addContext: () => setStatusMessage(portalAiNotice),
    requestClarification: () => setStatusMessage(portalAiNotice),
    regeneratePlan: () => setStatusMessage(portalAiNotice),
    inspectAgentWork: () => setStatusMessage(portalAiNotice),
    pauseAgent: () => setStatusMessage(portalAiNotice),
    cancelAgent: () => setStatusMessage(portalAiNotice),
    retryAgent: () => setStatusMessage(portalAiNotice),
    reassignAgent: () => setStatusMessage(portalAiNotice),
    requestAgentReview: () => setStatusMessage(portalAiNotice),
    openAgentOutput: () => setStatusMessage(portalAiNotice),
    openAgentEvidence: () => setStatusMessage(portalAiNotice),
    openArtifact: () => setStatusMessage(portalAiNotice),
    compareArtifact: () => setStatusMessage(portalAiNotice),
    reviewArtifact: () => setStatusMessage(portalAiNotice),
    commentArtifact: () => setStatusMessage(portalAiNotice),
    requestChangesArtifact: () => setStatusMessage(portalAiNotice),
    approveArtifact: () => setStatusMessage(portalAiNotice),
    rejectArtifact: () => setStatusMessage(portalAiNotice),
    regenerateArtifact: () => setStatusMessage(portalAiNotice),
    exportArtifact: () => setStatusMessage(portalAiNotice),
    openSpecializedTool: () => setStatusMessage(portalAiNotice),
    approveReview: () => setStatusMessage(portalAiNotice),
    rejectReview: () => setStatusMessage(portalAiNotice),
    requestReviewChanges: () => setStatusMessage(portalAiNotice),
    editReview: () => setStatusMessage(portalAiNotice),
    askFollowUp: () => setStatusMessage(portalAiNotice),
    sendToReviewer: () => setStatusMessage(portalAiNotice),
    compareReviewVersion: () => setStatusMessage(portalAiNotice),
    openEvidence: () => setStatusMessage(portalAiNotice),
    approve: () => setStatusMessage(portalAiNotice),
    reject: () => setStatusMessage(portalAiNotice),
    requestChanges: () => setStatusMessage(portalAiNotice),
    delegate: () => setStatusMessage(portalAiNotice),
    openRelatedArtifact: () => setStatusMessage(portalAiNotice),
    openPolicy: () => setStatusMessage(portalAiNotice),
    pauseExecution: () => setStatusMessage(portalAiNotice),
    resumeExecution: () => setStatusMessage(portalAiNotice),
    cancelExecution: () => setStatusMessage(portalAiNotice),
    retryFailedStep: () => setStatusMessage(portalAiNotice),
    openLogs: () => setStatusMessage(portalAiNotice),
    openTraces: () => setStatusMessage(portalAiNotice),
    rollbackExecution: () => setStatusMessage(portalAiNotice),
    viewKnowledge: () => setStatusMessage(portalAiNotice),
    publishKnowledge: () => setStatusMessage(portalAiNotice),
    compareKnowledge: () => setStatusMessage(portalAiNotice),
    supersedeKnowledge: () => setStatusMessage(portalAiNotice),
    linkKnowledgeToProject: () => setStatusMessage(portalAiNotice),
    createTemplate: () => setStatusMessage(portalAiNotice),
  };

  const solutionStatusTone = online ? "success" : "warning";
  const solutionStatusLabel = online ? "Online" : "Offline";

  if (route?.kind === "project") {
    return (
      <div className="solution-shell">
        <nav className="solution-nav" aria-label="Customer Solutions navigation">
          {roleNavigation.map((item) => (
            <button key={item.id} type="button" className="nav-item active" onClick={() => navigateTo(item.path)}>
              {item.label}
            </button>
          ))}
        </nav>
        <main className="solution-main">
          <UniversalAIWorkspace
            model={solutionAiModel}
            requestValue={project.idea || project.summary || ""}
            onRequestChange={(value) => setStatusMessage(value ? `AI draft updated for ${project.name}.` : "")}
            attachments={project.attachments || []}
            selectedMode="ask"
            selectedAgents={[]}
            selectedContextSources={["Project", "Workspace"]}
            selectedProjectArtifact={project.designs?.[0]?.title || project.requirements?.[0]?.summary || ""}
            selectedIncident=""
            selectedRequirement={project.requirements?.[0]?.summary || ""}
            selectedToolContext={currentWindowTitle}
            onAction={portalAiActions}
            onChooseSuggestion={(suggestion) => setStatusMessage(`${suggestion} is not connected to the portal AI backend yet.`)}
          />
          <ProjectHeader
            project={project}
            session={session}
            routeLabel={currentWindowTitle}
            onNavigate={(section) => navigateTo(buildSolutionProjectPath(project.id, section))}
            healthLabel={projectState.source === "cache" ? "Degraded" : "Healthy"}
            pendingApprovals={(project.approvals || []).filter((item) => String(item.status || "").toUpperCase() !== "APPROVED").length}
          />
          <div className="solution-subheader">
            <StatusPill label={solutionStatusLabel} tone={solutionStatusTone} />
            <span>Tenant: {session?.tenant_id || session?.organization || "unknown"}</span>
            <span>Build {NOVACODEPRO_BUILD_INFO.build_id}</span>
            <span>Current section: {currentWindowTitle}</span>
            {projectState.status === "degraded" ? <span>Cached data in use</span> : null}
          </div>
          <div className="solution-project-shell">
            <ProjectSection
              section={route.section}
              project={project}
              reloadProject={reloadProject}
              client={client}
              session={session}
              navigateToSection={(section) => navigateTo(buildSolutionProjectPath(project.id, section))}
              workflowState={workflowState.data || {}}
              setWorkflowPrompt={setWorkflowPrompt}
              workflowPrompt={workflowPrompt}
              setStatusMessage={setStatusMessage}
              currentProjectId={project.id}
              summaryState={summaryState}
            />
            <aside className="solution-context">
              <AssistantPanel role={session?.active_role} project={project} section={route.section} pendingApprovals={(project.approvals || []).length} />
              <ActivityPanel timeline={workflowState.data?.timeline || project.timeline || []} evidence={project.evidence || []} />
            </aside>
          </div>
          {statusMessage ? <p className="solution-status-message" role="status">{statusMessage}</p> : null}
        </main>
      </div>
    );
  }

  return (
      <div className="solution-shell">
        <nav className="solution-nav" aria-label="Customer Solutions navigation">
          {roleNavigation.map((item) => (
            <button
              key={item.id}
            type="button"
            className={item.id === "overview" ? "nav-item active" : "nav-item"}
            onClick={() => navigateTo(item.path)}
          >
            {item.label}
          </button>
          ))}
        </nav>
        <main className="solution-main">
          <UniversalAIWorkspace
            model={solutionAiModel}
            requestValue={project.idea || project.summary || ""}
            onRequestChange={(value) => setStatusMessage(value ? `AI draft updated for ${project.name}.` : "")}
            attachments={project.attachments || []}
            selectedMode="ask"
            selectedAgents={[]}
            selectedContextSources={["Project", "Workspace"]}
            selectedProjectArtifact={project.designs?.[0]?.title || project.requirements?.[0]?.summary || ""}
            selectedIncident=""
            selectedRequirement={project.requirements?.[0]?.summary || ""}
            selectedToolContext="Overview"
            onAction={portalAiActions}
            onChooseSuggestion={(suggestion) => setStatusMessage(`${suggestion} is not connected to the portal AI backend yet.`)}
          />
          {loadLanding && !landingState.data ? (
            <LoadingState label="Loading customer solutions" />
          ) : landingState.status === "error" ? (
            <ErrorState
            title="Customer Solutions unavailable"
            message={landingState.error || "Unable to load live customer solutions."}
            action={<button type="button" className="toolbar-chip" onClick={() => navigate(ROUTES.dashboard)}>Return to dashboard</button>}
          />
        ) : (
          <LandingPage
            session={session}
            summaryState={summaryState}
            customersState={customersState}
            projectsState={projectsState}
            filters={filters}
            setFilters={setFilters}
            onCreateCustomer={createCustomer}
            onCreateProject={createProject}
            onOpenProject={openProject}
            onContinuePending={continuePending}
            onReviewApprovals={() => navigateTo(appPath("/solutions/projects"))}
            onViewOperations={() => navigateTo(appPath("/solutions/projects"))}
            onNavigate={(section) => navigateTo(appPath(`/solutions/${section}`))}
          />
        )}
        {statusMessage ? <p className="solution-status-message" role="status">{statusMessage}</p> : null}
      </main>
    </div>
  );
}

function appPath(path) {
  return path.startsWith("/novacodepro") ? path : `/novacodepro${path.startsWith("/") ? path : `/${path}`}`;
}
