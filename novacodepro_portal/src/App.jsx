import React, { useMemo, useState } from "react";

import {
  AGENT_MARKETPLACE,
  AUTOMATION_TEMPLATES,
  DEVELOPER_SURFACES,
  INTEGRATIONS,
  PLATFORM_CENTERS,
  SERVICE_CATALOG,
  SOLUTION_TEMPLATES,
  WORKFLOW_STAGES,
  platformRuntime,
} from "./platform/runtime.js";
import { usePlatformRuntime } from "./platform/usePlatformRuntime.js";

const NAV_ITEMS = [
  "Dashboard",
  "Applications",
  "Projects",
  "Engineering",
  "Operations",
  "Customers",
  "Partners",
  "Employees",
  "Executives",
  "Marketplace",
  "Reports",
  "Analytics",
  "AI",
  "Settings",
];

const COMMANDS = [
  "Deploy NovaRide",
  "Open Studio",
  "Show failing pipelines",
  "Generate release notes",
  "Review security posture",
  "Open Partner Portal",
  "Find customer invoice",
  "Create project",
  "Switch tenant",
  "Post collaboration note",
  "Run automation template",
  "Summarize incidents",
  "Inspect audit trail",
  "Launch customer workspace",
  "Switch to Production",
  "Switch to Staging",
];

const ROLE_PROFILES = [
  {
    id: "platform-admin",
    label: "Platform Administrator",
    domain: "Engineering and governance",
    summary:
      "Full workspace control for tenants, security, layouts, releases, and policy administration.",
    accent: "#69d2a4",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Enterprise Governance",
    presence: "Online",
    metrics: [
      ["Tenants", "48"],
      ["Policies", "216"],
      ["Releases", "12"],
      ["Compliance", "99.98%"],
    ],
    actions: [
      "Create project",
      "Open Studio",
      "Review security",
      "Inspect audit trail",
      "Publish release",
      "Manage tenants",
    ],
    navFocus: "Settings",
    windows: [
      {
        id: "studio",
        title: "NovaCodePro Studio",
        status: "Primary",
        summary:
          "Unified editor for repositories, architecture diagrams, API surfaces, and deployment plans.",
        bullets: ["Repositories", "Architecture", "API Explorer", "Terminal", "Git review"],
      },
      {
        id: "security",
        title: "Security Center",
        status: "Guarded",
        summary:
          "Identity, RBAC, MFA, certificate policy, secret hygiene, and audit evidence in one control plane.",
        bullets: ["Identity", "MFA", "Certificates", "Secrets", "Audit logs"],
      },
      {
        id: "operations",
        title: "Operations Console",
        status: "Live",
        summary:
          "Services, regions, incidents, health, and availability across the NovaTech estate.",
        bullets: ["Services", "Containers", "Alerts", "Regions", "Incidents"],
      },
      {
        id: "trust",
        title: "Trust Center",
        status: "Verifiable",
        summary:
          "Receipts, certificates, release lineage, and verification records available for inspection.",
        bullets: ["Receipts", "Releases", "Evidence", "Verification", "History"],
      },
    ],
    signals: [
      ["API health", "Healthy"],
      ["Builds", "2 active"],
      ["Open incidents", "0"],
      ["Audit queue", "4 items"],
    ],
    notifications: [
      "Release lineage verified for active workspace.",
      "One policy update is awaiting approval.",
      "All production services are within SLO.",
    ],
    activity: [
      "Policy pack updated for production tenants.",
      "Release verification passed for Rider and Driver.",
      "Audit evidence exported to the trust vault.",
    ],
    agents: ["Security", "DevOps", "QA", "Release Manager"],
    permissions: ["Full tenant control", "Release approval", "Audit visibility", "Policy edits"],
  },
  {
    id: "software-engineer",
    label: "Software Engineer",
    domain: "Engineering delivery",
    summary:
      "Focused workspace for code, architecture, tests, pipeline health, and AI-assisted delivery.",
    accent: "#4ca7ff",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Builder Access",
    presence: "Available",
    metrics: [
      ["Repos", "32"],
      ["Open PRs", "9"],
      ["Tests", "1,248"],
      ["Deploy risk", "Low"],
    ],
    actions: ["Open Studio", "Run tests", "Review PRs", "Generate API", "Deploy preview", "Ask AI"],
    navFocus: "Engineering",
    windows: [
      {
        id: "studio",
        title: "Engineering Studio",
        status: "Active",
        summary:
          "Source control, architecture, code review, and preview environments in one docked workspace.",
        bullets: ["Repository tree", "Source control", "API Explorer", "Build output", "Tests"],
      },
      {
        id: "pipelines",
        title: "Pipeline Center",
        status: "Green",
        summary:
          "Validate, build, test, sign, publish, and deploy with visible gates at every step.",
        bullets: ["Validate", "Build", "Test", "Sign", "Publish"],
      },
      {
        id: "api",
        title: "API Explorer",
        status: "Synced",
        summary:
          "Browse contract changes, schema diffs, and service behavior while keeping release scope clear.",
        bullets: ["OpenAPI diff", "Requests", "Responses", "Schemas", "Mocks"],
      },
      {
        id: "ai",
        title: "AI Pair Programming",
        status: "Ready",
        summary:
          "Use NovaAI to explain code paths, draft tests, and generate documentation with policy context.",
        bullets: ["Prompt library", "Code review", "Test authoring", "Docs", "Architecture"],
      },
    ],
    signals: [
      ["Build queue", "3 jobs"],
      ["Test coverage", "91%"],
      ["Lint warnings", "12"],
      ["Deployments", "1 pending"],
    ],
    notifications: [
      "One release branch is ready for sign-off.",
      "API contract diff is within tolerance.",
      "No security blockers detected in the current workspace.",
    ],
    activity: [
      "Merged architecture update for the release registry.",
      "Validated Rider and Driver signing lineage.",
      "Closed the stale manifest mismatch in release checks.",
    ],
    agents: ["Software Engineer", "QA Engineer", "Release Manager", "Technical Writer"],
    permissions: ["Repository write", "Build access", "Pipeline review", "Preview deploy"],
  },
  {
    id: "operations-manager",
    label: "Operations Manager",
    domain: "Service operations",
    summary:
      "Live operational control center for incidents, regions, availability, sessions, and service health.",
    accent: "#56c6b2",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Operations Suite",
    presence: "Monitoring",
    metrics: [
      ["Availability", "99.99%"],
      ["Incidents", "1 open"],
      ["Regions", "6"],
      ["Latency", "118 ms"],
    ],
    actions: ["Open operations", "View incidents", "Inspect regions", "Review alerts", "Run drill"],
    navFocus: "Operations",
    windows: [
      {
        id: "ops",
        title: "Operations Console",
        status: "Live",
        summary:
          "A single view over services, regions, queues, traffic, and live incidents.",
        bullets: ["Services", "Containers", "Regions", "Queues", "Traffic"],
      },
      {
        id: "incidents",
        title: "Incident Board",
        status: "Triage",
        summary:
          "Track detection, owners, severity, containment, and rollback status in one place.",
        bullets: ["Detection", "Severity", "Owner", "Rollback", "Resolution"],
      },
      {
        id: "telemetry",
        title: "Observability",
        status: "Healthy",
        summary:
          "Latency, error rate, throughput, and session health with a concise signal view.",
        bullets: ["Latency", "Availability", "Error rate", "Sessions", "Storage"],
      },
      {
        id: "regions",
        title: "Regional Fleet",
        status: "Synced",
        summary:
          "Regional topology, promotion status, and readiness for expansion without losing control.",
        bullets: ["Regions", "Promotions", "Readiness", "SLOs", "Capacity"],
      },
    ],
    signals: [
      ["Active sessions", "1,284"],
      ["Error rate", "0.02%"],
      ["Alerts", "3 acked"],
      ["Rollback risk", "Low"],
    ],
    notifications: [
      "Latency remains stable across the primary region.",
      "One minor alert is under observation.",
      "No deployment freeze currently active.",
    ],
    activity: [
      "Confirmed container health after the latest rebuild.",
      "Reviewed region readiness for the next rollout stage.",
      "Closed the morning incident triage queue.",
    ],
    agents: ["DevOps", "Security", "Site Reliability", "Incident Manager"],
    permissions: ["Incident triage", "Deployment review", "Region controls", "Observability"],
  },
  {
    id: "business-administrator",
    label: "Business Administrator",
    domain: "Administration and finance",
    summary:
      "Manage organizations, contracts, approvals, finance, audit, procurement, and policy surfaces.",
    accent: "#f3c46b",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Business Control",
    presence: "Online",
    metrics: [
      ["Organizations", "124"],
      ["Contracts", "38"],
      ["Approvals", "6"],
      ["Revenue", "$4.8M"],
    ],
    actions: ["Review contracts", "Approve change", "Open finance", "Inspect audit", "Create tenant"],
    navFocus: "Reports",
    windows: [
      {
        id: "business",
        title: "Business Control Room",
        status: "Governed",
        summary:
          "Organizations, contracts, policies, procurement, and approvals are managed from a single queue.",
        bullets: ["Organizations", "Contracts", "Vendors", "Approvals", "Policies"],
      },
      {
        id: "finance",
        title: "Finance and Billing",
        status: "Current",
        summary:
          "Revenue, subscriptions, invoices, and procurement with direct linkage to audit trails.",
        bullets: ["Billing", "Invoices", "Revenue", "Licenses", "Forecasts"],
      },
      {
        id: "audit",
        title: "Audit and Risk",
        status: "Ready",
        summary:
          "Risk register, evidence pack, policy exceptions, and compliance checkpoints.",
        bullets: ["Audit trail", "Risk", "Evidence", "Compliance", "Controls"],
      },
      {
        id: "approvals",
        title: "Approvals Queue",
        status: "Pending",
        summary:
          "Documented approvals for contracts, renewals, exceptions, and commercial change requests.",
        bullets: ["Pending approvals", "SLA", "Commercial review", "Legal review", "Escalations"],
      },
    ],
    signals: [
      ["Monthly recurring revenue", "$1.4M"],
      ["Invoices due", "12"],
      ["Approval backlog", "2"],
      ["Audit exceptions", "0"],
    ],
    notifications: [
      "A contract renewal is awaiting commercial approval.",
      "No policy exceptions are open in the current cycle.",
      "Finance ledger sync completed successfully.",
    ],
    activity: [
      "Posted the latest billing summary.",
      "Reconciled license count against the active tenants.",
      "Reviewed the procurement queue for this month.",
    ],
    agents: ["Finance", "Procurement", "Compliance", "Legal"],
    permissions: ["Approvals", "Contracts", "Finance", "Risk review"],
  },
  {
    id: "partner-administrator",
    label: "Partner Administrator",
    domain: "Partner ecosystem",
    summary:
      "Manage partner onboarding, API keys, certification, analytics, billing, and sandbox access.",
    accent: "#7bc7ff",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Partner Network",
    presence: "Active",
    metrics: [
      ["Partners", "87"],
      ["API keys", "242"],
      ["Sandbox apps", "31"],
      ["Certifications", "14"],
    ],
    actions: ["Open sandbox", "Issue keys", "Review certification", "Inspect analytics", "Invite partner"],
    navFocus: "Partners",
    windows: [
      {
        id: "partner",
        title: "Partner Portal",
        status: "Available",
        summary:
          "A governed portal for SDKs, API keys, analytics, onboarding, and certification status.",
        bullets: ["API keys", "SDKs", "Certification", "Analytics", "Support"],
      },
      {
        id: "sandbox",
        title: "Sandbox and Certification",
        status: "Controlled",
        summary:
          "Partner testing stays isolated and only graduates after the required checks pass.",
        bullets: ["Sandbox", "Sample tenants", "Certification", "Trust checks", "Support"],
      },
      {
        id: "usage",
        title: "Usage Analytics",
        status: "Trended",
        summary:
          "Usage, revenue, and health metrics for partner traffic and integrations.",
        bullets: ["Usage", "Revenue", "Invoices", "Health", "Growth"],
      },
      {
        id: "trust",
        title: "Trust Verification",
        status: "Verified",
        summary:
          "Public trust artifacts, certificate checks, and partner governance live in the same surface.",
        bullets: ["Trust", "Certificates", "Evidence", "Policies", "Audits"],
      },
    ],
    signals: [
      ["Sandbox traffic", "Healthy"],
      ["Partner uptime", "99.95%"],
      ["Certification wait", "4"],
      ["Invoices in review", "9"],
    ],
    notifications: [
      "Two partner certifications are ready for final review.",
      "Sandbox traffic is within policy limits.",
      "Key rotation reminders are due this week.",
    ],
    activity: [
      "Approved a new SDK request.",
      "Published partner analytics for the week.",
      "Validated partner trust evidence.",
    ],
    agents: ["Partner Success", "Developer Relations", "Security", "Billing"],
    permissions: ["Partner onboarding", "API keys", "Certification", "Sandbox management"],
  },
  {
    id: "customer-success",
    label: "Customer Success",
    domain: "Support and customer experience",
    summary:
      "Operate the customer portal, support queue, downloads, trust pages, and payment visibility.",
    accent: "#8cd46a",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Customer Care",
    presence: "Ready",
    metrics: [
      ["Customers", "12,840"],
      ["Tickets", "142"],
      ["Downloads", "91%"],
      ["Satisfaction", "4.9/5"],
    ],
    actions: ["Open support", "Review trust", "Manage downloads", "Inspect payments", "Message customer"],
    navFocus: "Customers",
    windows: [
      {
        id: "customer",
        title: "Customer Portal",
        status: "Open",
        summary:
          "Products, subscriptions, downloads, invoices, and trust pages in one customer-facing workspace.",
        bullets: ["Products", "Subscriptions", "Downloads", "Invoices", "Security"],
      },
      {
        id: "support",
        title: "Support Queue",
        status: "In progress",
        summary:
          "Triage customer issues with context from trust, billing, and service health.",
        bullets: ["Tickets", "Escalations", "SLA", "Macros", "Knowledge base"],
      },
      {
        id: "payments",
        title: "Payments and Billing",
        status: "Monitored",
        summary:
          "Visibility into invoices, settlements, and payment issues without exposing internal controls.",
        bullets: ["Invoices", "Receipts", "Refunds", "Plans", "History"],
      },
      {
        id: "trust",
        title: "Customer Trust",
        status: "Published",
        summary:
          "Customer-visible identity, certificates, release notes, and verification references.",
        bullets: ["Trust", "Security", "Release notes", "Verification", "Status"],
      },
    ],
    signals: [
      ["Open tickets", "142"],
      ["Satisfied customers", "97%"],
      ["Refund queue", "3"],
      ["Release questions", "4"],
    ],
    notifications: [
      "A high-priority support ticket is waiting for owner assignment.",
      "Customer download links are serving normally.",
      "Trust verification status remains green.",
    ],
    activity: [
      "Updated the customer portal trust page.",
      "Resolved a billing exception for a premium account.",
      "Published the latest support bulletin.",
    ],
    agents: ["Support", "Billing", "Trust", "Knowledge"],
    permissions: ["Support view", "Customer communication", "Billing visibility", "Trust publishing"],
  },
  {
    id: "executive",
    label: "Executive",
    domain: "Strategy and performance",
    summary:
      "Portfolio, growth, security, compliance, and regional performance in a concise decision surface.",
    accent: "#f39f75",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Executive Review",
    presence: "Available",
    metrics: [
      ["ARR", "$28.2M"],
      ["Growth", "+18%"],
      ["Security score", "96"],
      ["Compliance", "99.7%"],
    ],
    actions: ["View KPIs", "Open portfolio", "Read forecast", "Review compliance", "Inspect regions"],
    navFocus: "Executives",
    windows: [
      {
        id: "executive",
        title: "Executive Dashboard",
        status: "Decision ready",
        summary:
          "Revenue, users, transactions, availability, security, and trust aligned in one strategic view.",
        bullets: ["Revenue", "Growth", "Users", "Availability", "Security"],
      },
      {
        id: "forecast",
        title: "Financial Forecast",
        status: "Stable",
        summary:
          "Forecasts, regional performance, and product portfolio movements with scenario context.",
        bullets: ["Forecast", "Regions", "Products", "Margins", "Scenario"],
      },
      {
        id: "portfolio",
        title: "Product Portfolio",
        status: "Balanced",
        summary:
          "NovaRide, NovaPay, NovaID, and platform services tracked as a single governed portfolio.",
        bullets: ["Portfolio", "Adoption", "Risk", "Progress", "Investment"],
      },
      {
        id: "compliance",
        title: "Compliance Review",
        status: "Ready",
        summary:
          "A compact board for governance, audit, and public-readiness decisions.",
        bullets: ["Compliance", "Audit", "Release", "Risk", "Controls"],
      },
    ],
    signals: [
      ["Net revenue", "+18%"],
      ["Retention", "94%"],
      ["Risk posture", "Green"],
      ["Region coverage", "4 active"],
    ],
    notifications: [
      "Executive review packet is ready for the board meeting.",
      "Compliance posture remains within target.",
      "Regional expansion scorecard is stable.",
    ],
    activity: [
      "Reviewed quarterly growth performance.",
      "Approved the next regional capacity step.",
      "Noted the platform remains above target availability.",
    ],
    agents: ["Analyst", "Compliance", "Finance", "Strategy"],
    permissions: ["Read-only portfolio", "KPI view", "Compliance review", "Scenario planning"],
  },
];

const TOPICS = [
  {
    name: "Workspace",
    detail: "Docked windows, saved layouts, and role-based surfaces for each organization.",
  },
  {
    name: "Governance",
    detail: "Identity, policies, approvals, audit, and trust artifacts live in the same workspace.",
  },
  {
    name: "AI",
    detail: "Command palette, workflow builder, and assistant panels stay embedded in context.",
  },
  {
    name: "Platform",
    detail: "Engineering, operations, business administration, partners, customers, and executives.",
  },
];

const WORKFLOW_STEPS = [
  "User",
  "AI Planning",
  "Development",
  "Testing",
  "Security",
  "Approval",
  "Deployment",
  "Monitoring",
];

const MARKETPLACE = [
  "Engineering",
  "Business",
  "Finance",
  "Healthcare",
  "Ride",
  "Payments",
  "Identity",
  "Logistics",
  "CRM",
  "HR",
  "AI",
  "IoT",
];

const DIGITAL_TWIN_LAYERS = [
  ["Australia", "Active region"],
  ["Africa", "Pilot region"],
  ["Europe", "Scaling region"],
  ["Asia", "Expansion region"],
  ["America", "Growth region"],
];

function App() {
  const runtime = usePlatformRuntime();
  const [roleId, setRoleId] = useState(ROLE_PROFILES[0].id);
  const [search, setSearch] = useState("");
  const [environment, setEnvironment] = useState("Production");
  const [focusNav, setFocusNav] = useState("Dashboard");
  const [selectedWindowId, setSelectedWindowId] = useState(ROLE_PROFILES[0].windows[0].id);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [solutionTemplateId, setSolutionTemplateId] = useState(SOLUTION_TEMPLATES[0].id);
  const [solutionTitle, setSolutionTitle] = useState("");
  const [solutionRequest, setSolutionRequest] = useState(SOLUTION_TEMPLATES[0].request);
  const [solutionDomain, setSolutionDomain] = useState(SOLUTION_TEMPLATES[0].domain);
  const [solutionRegion, setSolutionRegion] = useState("Australia");
  const [solutionCompliance, setSolutionCompliance] = useState("enterprise");
  const [solutionSurfaces, setSolutionSurfaces] = useState(
    SOLUTION_TEMPLATES[0].surfaces,
  );
  const [projectName, setProjectName] = useState("NovaCodePro Solution");
  const [projectOwner, setProjectOwner] = useState("Platform Engineering");
  const [projectBudget, setProjectBudget] = useState("$250K");
  const [projectRegion, setProjectRegion] = useState("Melbourne");
  const [commentDraft, setCommentDraft] = useState(
    "Architecture and requirements are ready for review.",
  );
  const [automationTemplateId, setAutomationTemplateId] = useState(
    AUTOMATION_TEMPLATES[0].id,
  );

  const activeRole = useMemo(
    () => ROLE_PROFILES.find((role) => role.id === roleId) ?? ROLE_PROFILES[0],
    [roleId],
  );

  const filteredCommands = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return COMMANDS.slice(0, 6);
    }
    return COMMANDS.filter((command) => command.toLowerCase().includes(query)).slice(0, 6);
  }, [search]);

  const appCatalog = useMemo(() => {
    return activeRole.actions.filter((action) => {
      const query = search.trim().toLowerCase();
      if (!query) {
        return true;
      }
      return action.toLowerCase().includes(query);
    });
  }, [activeRole, search]);

  const selectedRequest =
    runtime.solutionRequests.find((request) => request.id === runtime.selectedRequestId) ??
    runtime.solutionRequests[0];
  const currentStage = selectedRequest?.workflow[selectedRequest?.stageIndex ?? 0];
  const pendingSolutions = runtime.solutionRequests.filter((request) => request.status !== "operating");
  const liveSolutions = runtime.solutionRequests.filter((request) => request.status === "operating");
  const activeTenant =
    runtime.tenants.find((tenant) => tenant.id === runtime.activeTenantId) ?? runtime.tenants[0];
  const activeProject =
    runtime.projects.find((project) => project.id === runtime.activeProjectId) ?? runtime.projects[0];
  const activeThread =
    runtime.collaborationThreads.find((thread) => thread.id === runtime.activeThreadId) ??
    runtime.collaborationThreads[0];
  const activeKnowledgeNode =
    runtime.knowledgeGraph.find((node) => node.id === runtime.selectedKnowledgeNodeId) ??
    runtime.knowledgeGraph[0];
  const activeAutomationTemplate =
    AUTOMATION_TEMPLATES.find((template) => template.id === automationTemplateId) ??
    AUTOMATION_TEMPLATES[0];

  const solutionBlueprint = useMemo(() => {
    const template =
      SOLUTION_TEMPLATES.find((item) => item.id === solutionTemplateId) ?? SOLUTION_TEMPLATES[0];
    return {
      template,
      title: solutionTitle || template.title,
      request: solutionRequest || template.request,
      domain: solutionDomain || template.domain,
      region: solutionRegion,
      compliance: solutionCompliance,
      surfaces: solutionSurfaces,
    };
  }, [
    solutionCompliance,
    solutionDomain,
    solutionRegion,
    solutionRequest,
    solutionSurfaces,
    solutionTemplateId,
    solutionTitle,
  ]);

  const selectedWindow =
    activeRole.windows.find((window) => window.id === selectedWindowId) ?? activeRole.windows[0];

  const secondaryWindows = activeRole.windows.filter((window) => window.id !== selectedWindow.id);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">N</div>
          <div>
            <p className="eyebrow">NovaTech enterprise workspace</p>
            <strong>NovaCodePro</strong>
          </div>
        </div>

        <label className="global-search" aria-label="Global search">
          <span>Search</span>
          <input
            type="search"
            placeholder="Projects, releases, customers, incidents..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <div className="topbar-actions">
          <button type="button" className="toolbar-chip" onClick={() => setPaletteOpen(true)}>
            Command Palette
          </button>
          <div className="environment-switch">
            {["Production", "Staging", "Pilot"].map((item) => (
              <button
                key={item}
                type="button"
                className={item === environment ? "env-pill active" : "env-pill"}
                onClick={() => setEnvironment(item)}
              >
                {item}
              </button>
            ))}
          </div>
          <button type="button" className="toolbar-chip">
            Notifications
          </button>
          <button type="button" className="toolbar-chip">
            NovaID
          </button>
        </div>
      </header>

      <div className="workspace-shell">
        <aside className="sidebar">
          <div className="sidebar-card identity-card">
            <p className="section-label">Signed in</p>
            <strong>Djuma</strong>
            <span>{activeRole.label}</span>
            <span>{activeRole.organization}</span>
          </div>

          <nav className="nav-list" aria-label="Primary navigation">
            {NAV_ITEMS.map((item) => (
              <button
                key={item}
                type="button"
                className={item === focusNav ? "nav-item active" : "nav-item"}
                onClick={() => setFocusNav(item)}
              >
                {item}
              </button>
            ))}
          </nav>

          <div className="sidebar-card">
            <p className="section-label">Role presets</p>
            <div className="role-switcher">
              {ROLE_PROFILES.map((role) => (
                <button
                  key={role.id}
                  type="button"
                  className={role.id === roleId ? "role-pill active" : "role-pill"}
                  onClick={() => {
                    setRoleId(role.id);
                    setSelectedWindowId(role.windows[0].id);
                    setFocusNav(role.navFocus);
                  }}
                >
                  {role.label}
                </button>
              ))}
            </div>
          </div>
        </aside>

        <main className="content">
          <section className="hero-card">
            <div className="hero-copy">
              <p className="eyebrow">Unified digital workplace and engineering platform</p>
              <h1>{activeRole.label} workspace for the NovaTech ecosystem</h1>
              <p className="hero-summary">{activeRole.summary}</p>

              <div className="hero-badges">
                <span className="badge">Organization: {activeRole.organization}</span>
                <span className="badge">Environment: {environment}</span>
                <span className="badge">Subscription: {activeRole.subscription}</span>
                <span className="badge">Presence: {activeRole.presence}</span>
                <span className="badge">Tenant: {activeTenant.name}</span>
                <span className="badge">Project: {activeProject.name}</span>
              </div>
            </div>

            <div className="hero-panel">
              <div className="identity-summary">
                <span className="dot" style={{ background: activeRole.accent }} />
                <div>
                  <p className="section-label">Current context</p>
                  <strong>{activeRole.domain}</strong>
                </div>
              </div>
              <div className="metric-grid">
                {activeRole.metrics.map(([label, value]) => (
                  <article className="metric-card" key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Quick actions</p>
                <h2>Role-aware entry points</h2>
              </div>
              <div className="layout-hint">
                <span>Command palette ready</span>
                <span>Ctrl / Cmd + K</span>
              </div>
            </div>

            <div className="action-grid">
              {activeRole.actions.map((action) => (
                <button type="button" className="action-chip" key={action}>
                  {action}
                </button>
              ))}
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Universal workspace</p>
                <h2>Command-centered enterprise home</h2>
              </div>
              <div className="layout-hint">
                <span>NovaID-first access</span>
                <span>Layouts persist across devices</span>
              </div>
            </div>

            <div className="universal-grid">
              <article className="universal-card">
                <p className="section-label">Home workspace</p>
                <strong>Dashboard, Projects, Engineering, Operations, Business, AI</strong>
                <p>
                  One governed workspace that assembles role-specific tools without changing the
                  platform boundary for the current NovaTech dashboard.
                </p>
              </article>
              <article className="universal-card">
                <p className="section-label">Workspace rules</p>
                <strong>Dock, detach, split, stack, pin, and save layouts</strong>
                <p>
                  Every session can be restored as a workspace profile for developers, DevOps,
                  executives, support, or administrators.
                </p>
              </article>
              <article className="universal-card">
                <p className="section-label">Command palette</p>
                <strong>Search everything, launch anything</strong>
                <p>
                  Users can open tools, run workflows, and switch contexts without hunting through
                  menus or leaving the governed workspace.
                </p>
              </article>
              <article className="universal-card">
                <p className="section-label">Filtered actions</p>
                <strong>{appCatalog.length} actions available in this role</strong>
                <p>
                  {appCatalog.slice(0, 4).join(", ") || "No action matched the current query."}
                </p>
              </article>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Enterprise foundation</p>
                <h2>Tenants, projects, and collaboration are backed by real platform state</h2>
              </div>
              <div className="layout-hint">
                <span>Multi-tenant service layer</span>
                <span>Audit trail updated on every action</span>
              </div>
            </div>

            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Tenants</p>
                <strong>{activeTenant.name}</strong>
                <p className="studio-note">
                  The workspace switches tenant context without affecting the current NovaTech dashboard.
                </p>
                <div className="chip-cloud compact">
                  {runtime.tenants.map((tenant) => (
                    <button
                      type="button"
                      key={tenant.id}
                      className={tenant.id === activeTenant.id ? "context-chip active" : "context-chip"}
                      onClick={() => runtime.switchTenant(tenant.id)}
                    >
                      {tenant.name}
                    </button>
                  ))}
                </div>
                <dl className="service-meta">
                  <div>
                    <dt>Tier</dt>
                    <dd>{activeTenant.tier}</dd>
                  </div>
                  <div>
                    <dt>Regions</dt>
                    <dd>{activeTenant.regions.join(", ")}</dd>
                  </div>
                  <div>
                    <dt>Quota</dt>
                    <dd>{activeTenant.quota}</dd>
                  </div>
                  <div>
                    <dt>Residency</dt>
                    <dd>{activeTenant.residency}</dd>
                  </div>
                </dl>
              </article>

              <article className="studio-card">
                <p className="section-label">Projects</p>
                <strong>{activeProject.name}</strong>
                <p className="studio-note">
                  Projects are stored, versioned, and linked to tenant identity and budget context.
                </p>
                <div className="field-grid">
                  <label className="field">
                    <span>Project name</span>
                    <input
                      value={projectName}
                      onChange={(event) => setProjectName(event.target.value)}
                      placeholder="NovaCodePro Portal"
                    />
                  </label>
                  <label className="field">
                    <span>Owner</span>
                    <input
                      value={projectOwner}
                      onChange={(event) => setProjectOwner(event.target.value)}
                    />
                  </label>
                </div>
                <div className="field-grid">
                  <label className="field">
                    <span>Budget</span>
                    <input
                      value={projectBudget}
                      onChange={(event) => setProjectBudget(event.target.value)}
                    />
                  </label>
                  <label className="field">
                    <span>Region</span>
                    <input
                      value={projectRegion}
                      onChange={(event) => setProjectRegion(event.target.value)}
                    />
                  </label>
                </div>
                <button
                  type="button"
                  className="primary-action"
                  onClick={() =>
                    runtime.createProject({
                      name: projectName,
                      tenantId: activeTenant.id,
                      owner: projectOwner,
                      budget: projectBudget,
                      region: projectRegion,
                      solution: solutionBlueprint.title,
                      status: "Discovery",
                    })
                  }
                >
                  Create project
                </button>
                <div className="artifact-list">
                  {runtime.projects
                    .filter((project) => project.tenantId === activeTenant.id)
                    .slice(0, 4)
                    .map((project) => (
                      <button
                        type="button"
                        className="artifact-row project-row"
                        key={project.id}
                        onClick={() => runtime.selectProject(project.id)}
                      >
                        <strong>{project.name}</strong>
                        <span>{project.owner}</span>
                      </button>
                    ))}
                </div>
              </article>

              <article className="studio-card">
                <p className="section-label">Collaboration</p>
                <strong>{activeThread.scope}</strong>
                <p className="studio-note">
                  Notes, approvals, and review requests are captured against the active thread.
                </p>
                <div className="artifact-list">
                  {activeThread.messages.map((message) => (
                    <div className="audit-row" key={message.id}>
                      <span>{message.at}</span>
                      <strong>{message.author}</strong>
                      <p>{message.body}</p>
                    </div>
                  ))}
                </div>
                <label className="field">
                  <span>New comment</span>
                  <textarea
                    rows="3"
                    value={commentDraft}
                    onChange={(event) => setCommentDraft(event.target.value)}
                  />
                </label>
                <button
                  type="button"
                  className="toolbar-chip"
                  onClick={() => runtime.postComment(activeThread.id, commentDraft)}
                >
                  Post comment
                </button>
              </article>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Solution Studio</p>
                <h2>Request a governed software solution, not a prompt</h2>
              </div>
              <div className="layout-hint">
                <span>Workflow engine, API, storage, audit, and UI all in play</span>
                <span>Human approval stays mandatory at governance gates</span>
              </div>
            </div>

            <div className="template-strip">
              {SOLUTION_TEMPLATES.map((template) => (
                <button
                  key={template.id}
                  type="button"
                  className={template.id === solutionBlueprint.template.id ? "template-chip active" : "template-chip"}
                  onClick={() => {
                    setSolutionTemplateId(template.id);
                    setSolutionTitle(template.title);
                    setSolutionRequest(template.request);
                    setSolutionDomain(template.domain);
                    setSolutionSurfaces(template.surfaces);
                    setSolutionCompliance(template.domain === "finance" ? "very high" : "enterprise");
                  }}
                >
                  <strong>{template.title}</strong>
                  <span>{template.request}</span>
                </button>
              ))}
            </div>

            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Request intake</p>
                <label className="field">
                  <span>Solution name</span>
                  <input
                    value={solutionTitle}
                    onChange={(event) => setSolutionTitle(event.target.value)}
                    placeholder="Online pharmacy platform"
                  />
                </label>
                <label className="field">
                  <span>Business request</span>
                  <textarea
                    rows="4"
                    value={solutionRequest}
                    onChange={(event) => setSolutionRequest(event.target.value)}
                  />
                </label>
                <div className="field-grid">
                  <label className="field">
                    <span>Domain</span>
                    <input
                      value={solutionDomain}
                      onChange={(event) => setSolutionDomain(event.target.value)}
                    />
                  </label>
                  <label className="field">
                    <span>Region</span>
                    <input
                      value={solutionRegion}
                      onChange={(event) => setSolutionRegion(event.target.value)}
                    />
                  </label>
                </div>
                <div className="field-grid">
                  <label className="field">
                    <span>Compliance level</span>
                    <select
                      value={solutionCompliance}
                      onChange={(event) => setSolutionCompliance(event.target.value)}
                    >
                      <option value="enterprise">Enterprise</option>
                      <option value="high">High</option>
                      <option value="very high">Very high</option>
                    </select>
                  </label>
                  <label className="field">
                    <span>Surfaces</span>
                    <div className="chip-cloud compact">
                      {solutionBlueprint.template.surfaces.map((surface) => (
                        <button
                          type="button"
                          key={surface}
                          className={solutionSurfaces.includes(surface) ? "context-chip active" : "context-chip"}
                          onClick={() => {
                            setSolutionSurfaces((current) =>
                              current.includes(surface)
                                ? current.filter((item) => item !== surface)
                                : [...current, surface],
                            );
                          }}
                        >
                          {surface}
                        </button>
                      ))}
                    </div>
                  </label>
                </div>
                <button
                  type="button"
                  className="primary-action"
                  onClick={() =>
                    platformRuntime.createSolution({
                      title: solutionBlueprint.title,
                      request: solutionBlueprint.request,
                      domain: solutionBlueprint.domain,
                      region: solutionBlueprint.region,
                      compliance: solutionBlueprint.compliance,
                      surfaces: solutionBlueprint.surfaces,
                      template: solutionBlueprint.template,
                    })
                  }
                >
                  Create governed solution
                </button>
              </article>

              <article className="studio-card">
                <p className="section-label">Workflow engine</p>
                <strong>{selectedRequest?.title || "No solution selected"}</strong>
                <p className="studio-note">
                  Each stage carries a service, API, storage location, audit event, and UI owner.
                </p>
                <div className="workflow-rail">
                  {selectedRequest?.workflow.map((stage) => (
                    <button
                      key={stage.id}
                      type="button"
                      className={stage.id === currentStage?.id ? "workflow-node active" : "workflow-node"}
                      onClick={() => platformRuntime.runCommand(`Inspect ${stage.label}`)}
                    >
                      <span>{stage.label}</span>
                      <strong>{stage.status}</strong>
                      <em>{stage.service}</em>
                    </button>
                  ))}
                </div>
                <div className="studio-actions">
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.advanceWorkflow(selectedRequest.id)}
                  >
                    Advance stage
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() =>
                      platformRuntime.approveGate(selectedRequest.id, "Human approval captured in NovaCodePro.")
                    }
                  >
                    Approve gate
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.runCommand("Generate release package")}
                  >
                    Generate package
                  </button>
                </div>
                <div className="artifact-list">
                  {selectedRequest?.artifacts.map((artifact) => (
                    <div className="artifact-row" key={artifact.id}>
                      <strong>{artifact.title}</strong>
                      <span>{artifact.stage}</span>
                    </div>
                  ))}
                </div>
              </article>

              <article className="studio-card">
                <p className="section-label">Audit trail</p>
                <strong>Immutable activity log</strong>
                <div className="audit-list">
                  {runtime.auditTrail.slice(0, 8).map((entry) => (
                    <div className="audit-row" key={entry.id}>
                      <span>{entry.at}</span>
                      <strong>{entry.action}</strong>
                      <p>
                        {entry.service} · {entry.subject}
                      </p>
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Knowledge graph</p>
                <h2>Requirements, architecture, code, tests, release, and operations stay linked</h2>
              </div>
            </div>
            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Graph focus</p>
                <strong>{activeKnowledgeNode.label}</strong>
                <p className="studio-note">
                  Nodes remain traceable from the business request through deployment and audit evidence.
                </p>
                <div className="bullet-grid">
                  {activeKnowledgeNode.links.map((link) => {
                    const linked = runtime.knowledgeGraph.find((node) => node.id === link);
                    return (
                      <button
                        type="button"
                        className="bullet"
                        key={link}
                        onClick={() => runtime.focusKnowledgeNode(link)}
                      >
                        {linked?.label || link}
                      </button>
                    );
                  })}
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">Enterprise graph</p>
                <div className="service-grid compact">
                  {runtime.knowledgeGraph.map((node) => (
                    <button
                      type="button"
                      className={node.id === activeKnowledgeNode.id ? "service-card active" : "service-card"}
                      key={node.id}
                      onClick={() => runtime.focusKnowledgeNode(node.id)}
                    >
                      <p className="section-label">{node.type}</p>
                      <strong>{node.label}</strong>
                      <p>{node.links.length} linked nodes</p>
                    </button>
                  ))}
                </div>
              </article>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Automation engine</p>
                <h2>Reusable workflows turn requests into governed solution deliveries</h2>
              </div>
            </div>
            <div className="template-strip">
              {AUTOMATION_TEMPLATES.map((template) => (
                <button
                  key={template.id}
                  type="button"
                  className={template.id === activeAutomationTemplate.id ? "template-chip active" : "template-chip"}
                  onClick={() => setAutomationTemplateId(template.id)}
                >
                  <strong>{template.title}</strong>
                  <span>{template.description}</span>
                </button>
              ))}
            </div>
            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Run template</p>
                <strong>{activeAutomationTemplate.title}</strong>
                <p className="studio-note">
                  {activeAutomationTemplate.stages.length} workflow stages, each with audit and state.
                </p>
                <div className="workflow-track compact">
                  {activeAutomationTemplate.stages.map((stage, index) => (
                    <React.Fragment key={stage}>
                      <div className="workflow-step">
                        <span>{String(index + 1).padStart(2, "0")}</span>
                        <strong>{stage}</strong>
                      </div>
                      {index < activeAutomationTemplate.stages.length - 1 ? (
                        <div className="workflow-arrow">→</div>
                      ) : null}
                    </React.Fragment>
                  ))}
                </div>
                <button
                  type="button"
                  className="primary-action"
                  onClick={() => runtime.runAutomationTemplate(activeAutomationTemplate.id)}
                >
                  Run automation template
                </button>
              </article>
              <article className="studio-card">
                <p className="section-label">Recent automation runs</p>
                <strong>Workflow execution history</strong>
                <div className="artifact-list">
                  {runtime.automationRuns.length ? (
                    runtime.automationRuns.slice(0, 4).map((run) => (
                      <div className="artifact-row" key={run.id}>
                        <strong>{run.title}</strong>
                        <span>{run.status}</span>
                      </div>
                    ))
                  ) : (
                    <div className="audit-row">
                      <span>None</span>
                      <strong>Queue is idle</strong>
                      <p>Run a template to create a governed execution record.</p>
                    </div>
                  )}
                </div>
              </article>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Platform services</p>
                <h2>Each AI agent is backed by a service, API, storage layer, audit, and UI</h2>
              </div>
            </div>
            <div className="service-grid">
              {SERVICE_CATALOG.map((service) => (
                <article className="service-card" key={service.id}>
                  <p className="section-label">{service.kind}</p>
                  <strong>{service.title}</strong>
                  <p>{service.description}</p>
                  <dl className="service-meta">
                    <div>
                      <dt>Service</dt>
                      <dd>{service.service}</dd>
                    </div>
                    <div>
                      <dt>API</dt>
                      <dd>{service.api}</dd>
                    </div>
                    <div>
                      <dt>Storage</dt>
                      <dd>{service.storage}</dd>
                    </div>
                    <div>
                      <dt>Audit</dt>
                      <dd>{service.audit}</dd>
                    </div>
                    <div>
                      <dt>UI</dt>
                      <dd>{service.ui}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Developer platform</p>
                <h2>Integrations, APIs, SDKs, and policy packs remain first-class platform surfaces</h2>
              </div>
            </div>
            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Integrations</p>
                <strong>Connected enterprise services</strong>
                <div className="service-grid compact">
                  {INTEGRATIONS.map((integration) => {
                    const connected = runtime.connectedIntegrations.includes(integration.id);
                    return (
                      <button
                        type="button"
                        className={connected ? "service-card active" : "service-card"}
                        key={integration.id}
                        onClick={() => runtime.installIntegration(integration.id)}
                      >
                        <p className="section-label">{integration.kind}</p>
                        <strong>{integration.name}</strong>
                        <p>{integration.purpose}</p>
                        <span className="status-pill">{connected ? "Connected" : integration.status}</span>
                      </button>
                    );
                  })}
                </div>
              </article>

              <article className="studio-card">
                <p className="section-label">Developer surfaces</p>
                <strong>APIs and extension points</strong>
                <div className="chip-cloud">
                  {DEVELOPER_SURFACES.map((surface) => (
                    <span className="context-chip" key={surface.name}>
                      {surface.name}
                    </span>
                  ))}
                </div>
                <div className="artifact-list">
                  {DEVELOPER_SURFACES.map((surface) => (
                    <div className="artifact-row" key={surface.name}>
                      <strong>{surface.name}</strong>
                      <span>{surface.description}</span>
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">AI agent marketplace</p>
                <h2>Install specialist solution agents as governed services</h2>
              </div>
            </div>
            <div className="service-grid marketplace">
              {AGENT_MARKETPLACE.map((agent) => {
                const installed = runtime.installedAgents.includes(agent.id);
                return (
                  <article className="service-card" key={agent.id}>
                    <p className="section-label">{agent.category}</p>
                    <strong>{agent.title}</strong>
                    <p>{agent.summary}</p>
                    <dl className="service-meta">
                      <div>
                        <dt>Service</dt>
                        <dd>{agent.service}</dd>
                      </div>
                      <div>
                        <dt>API</dt>
                        <dd>{agent.api}</dd>
                      </div>
                      <div>
                        <dt>Storage</dt>
                        <dd>{agent.storage}</dd>
                      </div>
                      <div>
                        <dt>Audit</dt>
                        <dd>{agent.audit}</dd>
                      </div>
                      <div>
                        <dt>UI</dt>
                        <dd>{agent.ui}</dd>
                      </div>
                    </dl>
                    <button
                      type="button"
                      className={installed ? "toolbar-chip active" : "toolbar-chip"}
                      onClick={() => platformRuntime.installAgent(agent.id)}
                    >
                      {installed ? "Installed" : "Install agent"}
                    </button>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="workspace-band">
            <div className="band-header">
              <div>
                <p className="section-label">Workspace</p>
                <h2>Multi-window dock for active work</h2>
              </div>
              <div className="workspace-tabs">
                {activeRole.windows.map((window) => (
                  <button
                    key={window.id}
                    type="button"
                    className={window.id === selectedWindow.id ? "workspace-tab active" : "workspace-tab"}
                    onClick={() => setSelectedWindowId(window.id)}
                  >
                    {window.title}
                  </button>
                ))}
              </div>
            </div>

            <div className="workspace-grid">
              <article className="primary-window">
                <div className="window-head">
                  <div>
                    <p className="section-label">Focused window</p>
                    <h3>{selectedWindow.title}</h3>
                  </div>
                  <span className="status-pill">{selectedWindow.status}</span>
                </div>
                <p className="window-summary">{selectedWindow.summary}</p>
                <div className="bullet-grid">
                  {selectedWindow.bullets.map((bullet) => (
                    <span className="bullet" key={bullet}>
                      {bullet}
                    </span>
                  ))}
                </div>
                <div className="topology">
                  <div className="topology-node node-a">NovaID</div>
                  <div className="topology-node node-b">Workspace</div>
                  <div className="topology-node node-c">Trust</div>
                  <div className="topology-node node-d">AI</div>
                  <div className="topology-node node-e">Compliance</div>
                  <div className="topology-node node-f">Delivery</div>
                  <div className="topology-line line-a" />
                  <div className="topology-line line-b" />
                  <div className="topology-line line-c" />
                  <div className="topology-line line-d" />
                </div>
              </article>

              <div className="secondary-stack">
                {secondaryWindows.map((window) => (
                  <article className="secondary-window" key={window.id}>
                    <div className="window-head compact">
                      <div>
                        <p className="section-label">{window.status}</p>
                        <h3>{window.title}</h3>
                      </div>
                    </div>
                    <p className="window-summary">{window.summary}</p>
                    <div className="compact-list">
                      {window.bullets.map((bullet) => (
                        <span className="compact-pill" key={bullet}>
                          {bullet}
                        </span>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="module-grid">
            {TOPICS.map((topic) => (
              <article className="module-card" key={topic.name}>
                <p className="section-label">{topic.name}</p>
                <p>{topic.detail}</p>
              </article>
            ))}
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Platform centers</p>
                <h2>Operational modules that behave like first-class apps</h2>
              </div>
            </div>
            <div className="center-grid">
              {PLATFORM_CENTERS.map((center) => (
                <article className="center-card" key={center.title}>
                  <p className="section-label">{center.title}</p>
                  <p>{center.summary}</p>
                  <div className="chip-cloud">
                    {center.chips.map((chip) => (
                      <span className="context-chip" key={chip}>
                        {chip}
                      </span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Workflow builder</p>
                <h2>Drag-and-drop release and governance pipeline</h2>
              </div>
            </div>
            <div className="workflow-track" aria-label="AI and release workflow">
              {WORKFLOW_STEPS.map((step, index) => (
                <React.Fragment key={step}>
                  <div className="workflow-step">
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <strong>{step}</strong>
                  </div>
                  {index < WORKFLOW_STEPS.length - 1 ? <div className="workflow-arrow">→</div> : null}
                </React.Fragment>
              ))}
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Marketplace</p>
                <h2>Install capabilities like apps on a device</h2>
              </div>
            </div>
            <div className="marketplace-grid">
              {MARKETPLACE.map((item) => (
                <article className="marketplace-card" key={item}>
                  <strong>{item}</strong>
                  <p>Install, govern, certify, and remove from the NovaCodePro workspace.</p>
                </article>
              ))}
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Digital twin</p>
                <h2>Real-time operational map from region to transaction</h2>
              </div>
            </div>
            <div className="twin-shell">
              <div className="twin-map">
                {DIGITAL_TWIN_LAYERS.map(([name, detail], index) => (
                  <div className="twin-node" key={name} style={{ "--node-delay": `${index * 80}ms` }}>
                    <strong>{name}</strong>
                    <span>{detail}</span>
                  </div>
                ))}
              </div>
              <div className="twin-metrics">
                {[
                  ["Clusters", "18"],
                  ["Services", "412"],
                  ["Databases", "86"],
                  ["Users", "221K"],
                  ["Transactions", "9.8M"],
                ].map(([label, value]) => (
                  <div className="metric-card" key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </main>

        <aside className="context-rail">
          <section className="rail-card">
            <p className="section-label">Command palette</p>
            <strong>Universal search and command center</strong>
            <div className="command-list">
              {filteredCommands.map((command) => (
                <button type="button" className="command-chip" key={command}>
                  {command}
                </button>
              ))}
            </div>
          </section>

          <section className="rail-card">
            <p className="section-label">Live signals</p>
            <div className="signal-list">
              {activeRole.signals.map(([label, value]) => (
                <div className="signal-row" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="rail-card">
            <p className="section-label">Permissions</p>
            <div className="chip-cloud">
              {activeRole.permissions.map((item) => (
                <span className="context-chip" key={item}>
                  {item}
                </span>
              ))}
            </div>
          </section>

          <section className="rail-card">
            <p className="section-label">AI workspace</p>
            <strong>Assistant and agents</strong>
            <div className="chip-cloud">
              {activeRole.agents.map((item) => (
                <span className="context-chip" key={item}>
                  {item}
                </span>
              ))}
            </div>
          </section>

          <section className="rail-card">
            <p className="section-label">Notifications</p>
            <ul className="feed-list">
              {activeRole.notifications.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="rail-card">
            <p className="section-label">Recent activity</p>
            <ul className="feed-list">
              {activeRole.activity.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="rail-card">
            <p className="section-label">Navigation focus</p>
            <strong>{focusNav}</strong>
            <p className="rail-note">
              The active role assembles a curated workspace for {activeRole.domain.toLowerCase()}.
            </p>
          </section>
        </aside>
      </div>

      <footer className="footer-bar">
        <span>Separate from the current NovaTech dashboard surface.</span>
        <span>Role-aware workspace, governed access, synchronized state, and NovaID login.</span>
      </footer>

      {paletteOpen ? (
        <div
          role="presentation"
          className="palette-overlay"
          onClick={() => setPaletteOpen(false)}
        >
          <div className="palette-panel" onClick={(event) => event.stopPropagation()}>
            <div className="band-header">
              <div>
                <p className="section-label">Command palette</p>
                <h2>Deploy, inspect, navigate, and govern</h2>
              </div>
              <button type="button" className="toolbar-chip" onClick={() => setPaletteOpen(false)}>
                Close
              </button>
            </div>
            <div className="command-list large">
              {filteredCommands.map((command) => (
                <button type="button" className="command-chip" key={command}>
                  {command}
                </button>
              ))}
            </div>
            <div className="palette-meta">
              <span>Current role: {activeRole.label}</span>
              <span>Environment: {environment}</span>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;
