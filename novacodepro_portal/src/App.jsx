import React, { Suspense, lazy, useEffect, useMemo, useRef, useState } from "react";

import {
  AGENT_MARKETPLACE,
  AUTOMATION_TEMPLATES,
  COMPLETION_STANDARD,
  DEVELOPER_SURFACES,
  INTEGRATIONS,
  OPERATIONAL_READINESS_PROGRAM,
  PLATFORM_CENTERS,
  SERVICE_CATALOG,
  SOLUTION_TEMPLATES,
  UX_COMPONENT_REGISTRY,
  UXOS_RUNTIME_SERVICES,
  UX_OPERATING_SYSTEM,
  WORKFLOW_STAGES,
  platformRuntime,
} from "./platform/runtime.js";
import { fetchBootstrap, normalizeBootstrapResponse } from "./platform/bootstrap.js";
import { buildUniversalAIWorkspaceModel, UniversalAIWorkspace } from "./platform/aiWorkspace.jsx";
import { ROUTES } from "./platform/routes.js";
import { RoleWorkspaceWindows } from "./platform/roleWorkspaceView.jsx";
import { buildRoleWorkspaceModel } from "./platform/roleWorkspace.js";
import { resolveWorkspaceLoginRoleFromPathname } from "./platform/workspaceRoutes.js";
import { isSolutionRoute } from "./platform/solutionRoutes.js";
import { StudioChrome } from "./novacodepro/StudioChrome.js";
import { findNovaCodeProAppByPath, isNovaCodeProRouteAccessible, parseNovaCodeProRoute } from "./platform/appRegistry.js";
import { clearNovaCodeProSessionState } from "./platform/sessionState.js";
import {
  createDefaultFrontendRuntimeConfig,
  loadFrontendRuntimeConfig,
  resolveFrontendRuntimeConfigUrl,
} from "./platform/frontendConfig.js";
import { createDefaultProductFrontendRegistry } from "./platform/productFrontendRegistry.js";
import {
  registerDefaultFrontendManifests,
  registerDefaultInteractionManifests,
  registerDefaultRenderingManifests,
} from "./platform/productFrontendManifests.js";
import { createDefaultRenderingRegistry } from "./platform/rendering/index.js";
import { createDefaultInteractionRegistry } from "./platform/interaction/index.js";
import { usePlatformRuntime } from "./platform/usePlatformRuntime.js";
import { NOVACODEPRO_BUILD_INFO } from "./platform/version.js";
import { PublicLandingPage } from "./public/PublicLandingPage.jsx";
import { LoginPage } from "./auth/LoginPage.jsx";
import { createClientReferenceId, getCorrelationId, getUserSafeMessage, normalizeApiError } from "./auth/authErrors.js";
import { isPublicAuthPath, resolveSafeReturnTo } from "./auth/authRouting.js";
import { DesignDashboard } from "./design/DesignDashboard.jsx";
import { DesignStudioWorkspace } from "./design/DesignStudioWorkspace.jsx";
import { ExperienceMappingStudio } from "./design/ExperienceMappingStudio.jsx";
import { DesignSystemStudio } from "./design/DesignSystemStudio.jsx";
import { AIDesignStudio } from "./design/AIDesignStudio.jsx";
import { AccessibilityStudio } from "./design/AccessibilityStudio.jsx";
import { PrototypeCollaborationStudio } from "./design/PrototypeCollaborationStudio.jsx";
import { DeliveryGovernanceStudio } from "./design/DeliveryGovernanceStudio.jsx";

function lazyNamed(loader, exportName) {
  return lazy(() => loader().then((module) => ({ default: module[exportName] })));
}

const LazySolutionEngineeringPortal = lazyNamed(() => import("./solutions/SolutionEngineeringPortal.jsx"), "SolutionEngineeringPortal");
const LazyNovaCodeProWorkspaceHub = lazyNamed(() => import("./novacodepro/NovaCodeProWorkspaceHub.jsx"), "NovaCodeProWorkspaceHub");
const LazyStudioExplorer = lazyNamed(() => import("./novacodepro/explorer/StudioExplorer.js"), "StudioExplorer");
const LazyProductFactoryPortal = lazyNamed(() => import("./novacodepro/ProductFactoryPortal.jsx"), "ProductFactoryPortal");
const LazyStrategyWorkspace = lazyNamed(() => import("./strategy/StrategyWorkspace.jsx"), "StrategyWorkspace");
const LazyNCP003Portal = lazyNamed(() => import("./novacodepro/NCP003Portal.jsx"), "NCP003Portal");
const LazyNCP004Portal = lazyNamed(() => import("./novacodepro/NCP004Portal.jsx"), "NCP004Portal");
const LazyNCP005Portal = lazyNamed(() => import("./novacodepro/NCP005Portal.jsx"), "NCP005Portal");
const LazyNCP006APortal = lazyNamed(() => import("./novacodepro/NCP006APortal.jsx"), "NCP006APortal");
const LazyNCP006BPortal = lazyNamed(() => import("./novacodepro/NCP006BPortal.jsx"), "NCP006BPortal");
const LazyNCP007Portal = lazyNamed(() => import("./novacodepro/NCP007Portal.jsx"), "NCP007Portal");
const LazyNCP008Portal = lazyNamed(() => import("./novacodepro/NCP008Portal.jsx"), "NCP008Portal");

function StudioSurfaceFallback() {
  return (
    <div className="app-shell studio-shell">
      <div className="studio-loading-state" role="status" aria-live="polite">
        Loading studio surface…
      </div>
    </div>
  );
}

const NAV_ITEMS = [
  "Dashboard",
  "Applications",
  "Apps",
  "Projects",
  "Engineering",
  "Operations",
  "Operational Verification",
  "Verification",
  "Developer Portal",
  "Mobile",
  "Inspector",
  "Desktop",
  "Customers",
  "Partners",
  "Employees",
  "Board",
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
  "Open board pack",
  "Review risk register",
  "Approve strategy",
  "Open developer portal",
  "Open mobile companion",
  "Open inspector app",
  "Open desktop app",
  "Open verification center",
  "Switch to Production",
  "Switch to Staging",
];

const GOVERNANCE_MATRIX = [
  ["Corporate strategy", "Board / CEO", "CEO", "Advise", "Advise", "—"],
  ["Annual technology roadmap", "Review", "Approve", "✓", "Advise", "Contribute"],
  ["Major platform architecture", "Inform", "Inform", "✓", "Review", "Implement"],
  ["Production operations", "—", "Oversight", "Oversight", "Security oversight", "Execute"],
  ["Security policy", "Review", "Approve", "Collaborate", "✓", "Implement"],
  ["Release governance", "—", "Oversight", "✓", "Security approval", "Execute"],
  ["Infrastructure management", "—", "—", "Oversight", "Review", "Execute"],
  ["Incident response", "Oversight", "Coordinate", "Lead technical response", "Lead security response", "Execute operations"],
];

const LEADERSHIP_ROLE_IDS = new Set([
  "board",
  "ceo",
  "coo",
  "cto",
  "cfo",
  "cpo",
  "ciso",
  "chief-legal-compliance-officer",
]);

const DISCOVERY_PROMPTS = [
  "Who are the primary users?",
  "Which countries and regions must be supported?",
  "Which regulations, policies, or data residency rules apply?",
  "Which channels are required: mobile, web, APIs, partners?",
  "Which languages, currencies, and payment methods are required?",
];

const ENTERPRISE_WINDOWS = [
  {
    id: "window-01",
    label: "Window 1",
    title: "NovaID Identity Center",
    phase: "Identity and trust",
    service: "Identity Service",
    summary: "Unified identity, authentication, authorization, session intelligence, and trust.",
  },
  {
    id: "window-02",
    label: "Window 2",
    title: "Unified Workspace",
    phase: "Workspace",
    service: "Workspace Service",
    summary: "Persistent role-aware workspace with shared conversations, memory, files, and layouts.",
  },
  {
    id: "window-03",
    label: "Window 3",
    title: "Multimodal Request Composer",
    phase: "Request",
    service: "Conversation Service",
    summary: "Universal request input for text, files, diagrams, repositories, logs, and voice.",
  },
  {
    id: "window-04",
    label: "Window 4",
    title: "AI Discovery Center",
    phase: "Discovery",
    service: "Discovery Agent",
    summary: "Dynamic interviews that convert incomplete ideas into structured intent and constraints.",
  },
  {
    id: "window-05",
    label: "Window 5",
    title: "Requirements Studio",
    phase: "Definition",
    service: "Requirements Service",
    summary: "Versioned requirements, baselines, coverage, traceability, and approval-ready analysis.",
  },
  {
    id: "window-06",
    label: "Window 6",
    title: "Architecture Center",
    phase: "Architecture",
    service: "Architecture Service",
    summary: "Enterprise and solution architecture, fitness functions, ADRs, and trust boundaries.",
  },
  {
    id: "window-07",
    label: "Window 7",
    title: "UX and Experience Studio",
    phase: "Design",
    service: "Design Service",
    summary: "Research, journeys, wireframes, prototypes, responsive layouts, and accessibility.",
  },
  {
    id: "window-08",
    label: "Window 8",
    title: "Data and API Center",
    phase: "Data and APIs",
    service: "Integration API Service",
    summary: "API contracts, schemas, data models, lineage, compatibility, and contract testing.",
  },
  {
    id: "window-09",
    label: "Window 9",
    title: "Solution Factory",
    phase: "Engineering",
    service: "Solution Orchestrator Engine",
    summary: "Repository-aware generation for web, mobile, data, infrastructure, docs, and tests.",
  },
  {
    id: "window-10",
    label: "Window 10",
    title: "Agent Orchestrator",
    phase: "Orchestration",
    service: "Agent Orchestrator",
    summary: "Specialized agents execute within verified identities, budgets, scopes, and data boundaries.",
  },
  {
    id: "window-11",
    label: "Window 11",
    title: "Enterprise Knowledge Graph",
    phase: "Memory",
    service: "Knowledge Graph",
    summary: "Semantic graph for traceability, impact analysis, search, and institutional memory.",
  },
  {
    id: "window-12",
    label: "Window 12",
    title: "Workflow and Decision Engine",
    phase: "Automation",
    service: "Workflow Engine",
    summary: "Long-running workflows, decisions, compensations, approvals, replays, and evidence.",
  },
  {
    id: "window-13",
    label: "Window 13",
    title: "Test and Quality Center",
    phase: "Quality",
    service: "Verification Service",
    summary: "Unified quality engineering for software, infrastructure, data, AI, and accessibility.",
  },
  {
    id: "window-14",
    label: "Window 14",
    title: "Security Center",
    phase: "Security",
    service: "Security Review Service",
    summary: "Threat modelling, SAST, DAST, SBOM, runtime protection, and supply-chain defense.",
  },
  {
    id: "window-15",
    label: "Window 15",
    title: "Compliance and Assurance Center",
    phase: "Compliance",
    service: "Compliance Service",
    summary: "Control mapping, evidence capture, readiness, exceptions, and continuous compliance.",
  },
  {
    id: "window-16",
    label: "Window 16",
    title: "Human Approval Center",
    phase: "Human review",
    service: "Approval Service",
    summary:
      "Reviewer workspace for human authorization of requirements, architecture, security, release, deployment, and risk actions.",
  },
  {
    id: "window-17",
    label: "Window 17",
    title: "Release Factory",
    phase: "Release",
    service: "Release Factory",
    summary: "Build, sign, attest, package, verify, promote, and archive governed release artifacts.",
  },
  {
    id: "window-18",
    label: "Window 18",
    title: "Deployment Center",
    phase: "Deployment",
    service: "Deployment Service",
    summary: "Progressive delivery across governed environments with validation, rollback, and evidence.",
  },
  {
    id: "window-19",
    label: "Window 19",
    title: "Observability Platform",
    phase: "Operations",
    service: "Observability Service",
    summary: "Unified metrics, logs, traces, RUM, business telemetry, and service maps.",
  },
  {
    id: "window-20",
    label: "Window 20",
    title: "Enterprise Digital Twin",
    phase: "Simulation",
    service: "Digital Twin Engine",
    summary: "Live computational model for scenario simulation, forecasting, and impact analysis.",
  },
  {
    id: "window-21",
    label: "Window 21",
    title: "Operations Center",
    phase: "Operations",
    service: "Operations Center",
    summary: "Incident response, runbooks, continuity, problem management, and operational evidence.",
  },
  {
    id: "window-22",
    label: "Window 22",
    title: "Enterprise Marketplace",
    phase: "Ecosystem",
    service: "Marketplace Service",
    summary: "Governed distribution for solutions, agents, templates, packs, and connectors.",
  },
  {
    id: "window-23",
    label: "Window 23",
    title: "Executive Dashboard",
    phase: "Executive",
    service: "Executive Analytics",
    summary: "Real-time business, technology, risk, and AI performance intelligence for executives.",
  },
  {
    id: "window-24",
    label: "Window 24",
    title: "Continuous Improvement Center",
    phase: "Optimization",
    service: "Improvement Engine",
    summary: "Closed-loop measurement, prioritization, implementation, and learning from outcomes.",
  },
  {
    id: "window-25",
    label: "Window 25",
    title: "Enterprise Risk Center",
    phase: "Risk",
    service: "Risk Engine",
    summary: "Unified risk taxonomy, control effectiveness, treatment plans, and board reporting.",
  },
  {
    id: "window-26",
    label: "Window 26",
    title: "Approval Policy and Routing Engine",
    phase: "Policy orchestration",
    service: "Policy Engine",
    summary:
      "Routing, quorum, separation of duties, escalation, time bounds, and policy enforcement beneath human review.",
  },
  {
    id: "window-27",
    label: "Window 27",
    title: "Executive AI Agents",
    phase: "Advisory AI",
    service: "Executive AI Platform",
    summary: "Role-specific strategic assistants that advise without replacing accountable executives.",
  },
  {
    id: "window-28",
    label: "Window 28",
    title: "Board Portal",
    phase: "Governance",
    service: "Board Service",
    summary: "Secure board packs, voting, resolutions, decisions, and fiduciary evidence.",
  },
  {
    id: "window-29",
    label: "Window 29",
    title: "Enterprise Command Center",
    phase: "Command",
    service: "Command Service",
    summary: "Unified command room across strategy, operations, security, finance, risk, and AI.",
  },
];

const COMPOSER_MODES = [
  { id: "ask", label: "Ask", description: "Explain without changing files." },
  { id: "plan", label: "Plan", description: "Produce a governed execution plan." },
  { id: "design", label: "Design", description: "Generate architecture and UX direction." },
  { id: "build", label: "Build", description: "Create or modify implementation." },
  { id: "fix", label: "Fix", description: "Diagnose and correct defects." },
  { id: "review", label: "Review", description: "Inspect code, security, or governance." },
  { id: "test", label: "Test", description: "Generate and run validation." },
  { id: "deploy", label: "Deploy", description: "Prepare or execute deployment." },
  { id: "operate", label: "Operate", description: "Investigate runtime health." },
  { id: "full_solution", label: "Full solution", description: "Run the complete lifecycle." },
];

const COMPOSER_CONTEXT_SOURCES = [
  "Current conversation",
  "Current project",
  "Selected repository",
  "Selected files",
  "Organization knowledge",
  "Approved external knowledge",
  "Previous solutions",
  "Production telemetry",
];

const COMPOSER_AGENTS = [
  "Solution Architect",
  "Product Manager",
  "UI Designer",
  "Frontend Engineer",
  "Backend Engineer",
  "QA Agent",
  "Security Agent",
  "DevOps Agent",
];

const OUTPUT_TABS = [
  "Overview",
  "Plan",
  "Code",
  "Design",
  "Tests",
  "Security",
  "Architecture",
  "Evidence",
  "Deployment",
  "Files",
  "Agent Activity",
];

const STARTER_REQUESTS = [
  "Build a modern customer-service portal with authentication, case management, analytics, and an AI support assistant.",
  "Analyse this repository, identify production blockers, fix the critical issues, run validation, and prepare a release report.",
  "Design and implement a mobile payment application for consumers, agents, merchants, and businesses.",
];

const ROLE_PROFILES = [
  {
    id: "platform-admin",
    label: "Platform Administrator",
    domain: "Engineering and governance",
    summary:
      "Highest operational control for NovaTech platform health, governance, security, and lifecycle operations.",
    accent: "#69d2a4",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Enterprise Governance",
    presence: "Online",
    metrics: [
      ["Platform health", "Healthy"],
      ["Services", "7 core"],
      ["Workflows", "312"],
      ["Compliance", "99.98%"],
    ],
    actions: [
      "Create organization",
      "Provision tenant",
      "Open digital twin",
      "Review security alerts",
      "Inspect audit trail",
      "Enable maintenance mode",
    ],
    navFocus: "Settings",
    windows: [
      {
        id: "overview",
        title: "Platform Overview",
        status: "Primary",
        summary:
          "Command-center overview of platform health, services, workflows, approvals, and release readiness.",
        bullets: ["Health", "Services", "Workflows", "Approvals", "Releases"],
      },
      {
        id: "identity",
        title: "Identity & Access",
        status: "Guarded",
        summary:
          "NovaID, SSO, MFA, RBAC, certificates, secrets, and role assignments controlled from one place.",
        bullets: ["NovaID", "SSO", "MFA", "RBAC", "Certificates"],
      },
      {
        id: "operations",
        title: "Infrastructure & Operations",
        status: "Live",
        summary:
          "Infrastructure, Kubernetes, storage, databases, networking, alerts, capacity, and runtime health.",
        bullets: ["Infrastructure", "Kubernetes", "Storage", "Databases", "Alerts"],
      },
      {
        id: "governance",
        title: "Governance & Audit",
        status: "Verifiable",
        summary:
          "Audit, compliance, security, risk, policy, approvals, evidence, and certificate controls.",
        bullets: ["Audit", "Compliance", "Security", "Evidence", "Approvals"],
      },
      {
        id: "delivery",
        title: "Engineering & Delivery",
        status: "Connected",
        summary:
          "Solution Factory, workflow engine, release center, deployment center, artifact repository, knowledge graph, and digital twin.",
        bullets: ["Solution Factory", "Workflow Engine", "Release Center", "Deployment Center", "Digital Twin"],
      },
      {
        id: "marketplace",
        title: "Marketplace & Settings",
        status: "Controlled",
        summary:
          "Marketplace packs, branding, notifications, API keys, backups, and maintenance remain governed.",
        bullets: ["Marketplace", "Branding", "Notifications", "Backups", "Maintenance"],
      },
    ],
    signals: [
      ["API health", "Healthy"],
      ["Pending approvals", "2"],
      ["Open incidents", "0"],
      ["Service registry", "7 healthy"],
    ],
    notifications: [
      "Platform health is green across the core service registry.",
      "One policy update is awaiting approval.",
      "Release lineage remains verified for the active platform.",
    ],
    activity: [
      "Validated the active NovaCodePro service registry.",
      "Reviewed pending governance approvals.",
      "Confirmed release and deployment status for production services.",
    ],
    agents: ["Security", "DevOps", "QA", "Release Manager", "Platform SRE"],
    permissions: ["Global tenant control", "Release approval", "Audit visibility", "Policy edits", "Maintenance"],
  },
  {
    id: "board",
    label: "Board of Directors",
    domain: "Governance and oversight",
    summary:
      "Strategic oversight for enterprise performance, risk, capital allocation, and governance.",
    accent: "#8f98aa",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Board Portal",
    presence: "Read-only",
    metrics: [
      ["Revenue growth", "18.4%"],
      ["Customer satisfaction", "94.2%"],
      ["Platform availability", "99.98%"],
      ["Enterprise risk", "Low"],
    ],
    actions: [
      "Review board pack",
      "Open risk register",
      "Inspect strategy",
      "Review audit trail",
      "Approve priorities",
    ],
    navFocus: "Board",
    windows: [
      {
        id: "board-overview",
        title: "Board Dashboard",
        status: "Decision ready",
        summary:
          "A strategic dashboard for performance, risk, and governance without exposing operational depth.",
        bullets: ["Revenue", "Growth", "Satisfaction", "Risk", "Compliance"],
      },
      {
        id: "board-risk",
        title: "Risk and Governance",
        status: "Monitored",
        summary:
          "High-level risk posture, major audit outcomes, and governance matters presented for directors.",
        bullets: ["Risk", "Audit", "Compliance", "Ethics", "Oversight"],
      },
      {
        id: "board-strategy",
        title: "Strategic Initiatives",
        status: "Active",
        summary:
          "Board-level priorities, market expansion, and major investment themes stay visible here.",
        bullets: ["Strategy", "Investment", "Expansion", "Portfolio", "Transformation"],
      },
      {
        id: "board-finance",
        title: "Financial Summary",
        status: "Healthy",
        summary:
          "Profitability, cash flow, and capital deployment summaries for the next board review.",
        bullets: ["Cash flow", "Margin", "Forecast", "Capital", "Liquidity"],
      },
    ],
    signals: [
      ["Board actions", "4 pending"],
      ["Security issues", "0 critical"],
      ["Compliance", "Compliant"],
      ["Strategic initiatives", "12 active"],
    ],
    notifications: [
      "Board pack is ready for the next scheduled review.",
      "Enterprise risk remains within appetite.",
      "No critical audit findings are currently open.",
    ],
    activity: [
      "Prepared strategic performance summary for directors.",
      "Reviewed capital allocation and risk posture.",
      "Published the latest board evidence pack.",
    ],
    agents: ["Analyst", "Finance", "Legal", "Strategy"],
    permissions: ["Read-only enterprise view", "Board pack review", "Risk oversight", "Strategic approval"],
  },
  {
    id: "ceo",
    label: "Chief Executive Officer",
    domain: "Strategy and enterprise performance",
    summary:
      "Owns company strategy, partnerships, market expansion, and enterprise performance.",
    accent: "#e0a85d",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Executive Leadership",
    presence: "Available",
    metrics: [
      ["Revenue", "$28.2M"],
      ["Growth", "+18.4%"],
      ["Customer adoption", "94%"],
      ["Portfolio", "6 products"],
    ],
    actions: [
      "Review KPI pack",
      "Open board pack",
      "Set strategic priorities",
      "Inspect portfolio",
      "Review risk posture",
    ],
    navFocus: "Executives",
    windows: [
      {
        id: "ceo-dashboard",
        title: "CEO Dashboard",
        status: "Decision ready",
        summary:
          "Strategic KPIs, enterprise health, and major initiatives presented for executive action.",
        bullets: ["Revenue", "Growth", "Adoption", "Portfolio", "Risk"],
      },
      {
        id: "ceo-strategy",
        title: "Strategic Initiatives",
        status: "Active",
        summary:
          "Market entry, product investment, and executive priorities remain visible in one workspace.",
        bullets: ["Markets", "Partnerships", "Initiatives", "Investments", "Expansion"],
      },
      {
        id: "ceo-portfolio",
        title: "Product Portfolio",
        status: "Balanced",
        summary:
          "NovaCodePro, NovaRide, NovaPay, NovaID, NovaHealth, and future products tracked together.",
        bullets: ["NovaCodePro", "NovaRide", "NovaPay", "NovaID", "NovaHealth"],
      },
      {
        id: "ceo-board",
        title: "Board Reporting",
        status: "Prepared",
        summary:
          "Board-ready summaries with a clear view of performance, risk, and initiative progress.",
        bullets: ["Board pack", "KPI trend", "Risk summary", "Forecast", "Actions"],
      },
    ],
    signals: [
      ["ARR", "$28.2M"],
      ["Growth", "+18%"],
      ["Customer adoption", "94%"],
      ["Strategic initiatives", "12 active"],
    ],
    notifications: [
      "Board reporting packet is ready for review.",
      "Growth remains above plan for the current quarter.",
      "Strategic initiative status is stable.",
    ],
    activity: [
      "Reviewed enterprise growth and portfolio health.",
      "Aligned executive priorities with the board agenda.",
      "Checked partner and market expansion readiness.",
    ],
    agents: ["Strategy", "Finance", "Product", "Analyst"],
    permissions: ["Strategic oversight", "Board reporting", "Portfolio view", "Executive planning"],
  },
  {
    id: "coo",
    label: "Chief Operating Officer",
    domain: "Operations and service delivery",
    summary:
      "Owns daily operations, service delivery, continuity, and regional execution.",
    accent: "#53c3b8",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Executive Leadership",
    presence: "Monitoring",
    metrics: [
      ["Availability", "99.99%"],
      ["Incidents", "1 open"],
      ["Regions", "6"],
      ["SLA", "99.96%"],
    ],
    actions: [
      "Open operations",
      "Review incidents",
      "Inspect continuity",
      "Review regions",
      "Run operational drill",
    ],
    navFocus: "Operations",
    windows: [
      {
        id: "coo-ops",
        title: "Operations Dashboard",
        status: "Live",
        summary:
          "Service delivery, regional performance, and support operations in a single executive view.",
        bullets: ["Delivery", "Regions", "Support", "Incidents", "Continuity"],
      },
      {
        id: "coo-continuity",
        title: "Business Continuity",
        status: "Ready",
        summary:
          "Recovery posture, failover readiness, and operational resilience sit behind the COO view.",
        bullets: ["DR", "Backups", "Failover", "Recovery", "Readiness"],
      },
      {
        id: "coo-regions",
        title: "Regional Operations",
        status: "Synced",
        summary:
          "Regional fleet health, service rollout, and operational risk by geography.",
        bullets: ["Australia", "Africa", "Europe", "Asia", "America"],
      },
      {
        id: "coo-support",
        title: "Service Delivery",
        status: "Monitored",
        summary:
          "Customer support, issue resolution, and SLA adherence tracked alongside platform health.",
        bullets: ["Tickets", "SLA", "Escalations", "Resolution", "Monitoring"],
      },
    ],
    signals: [
      ["Availability", "99.99%"],
      ["Incidents", "1 open"],
      ["Backlog", "3 items"],
      ["Recovery posture", "Ready"],
    ],
    notifications: [
      "No regional freeze is currently active.",
      "Service delivery remains within the agreed SLA.",
      "Continuity controls are ready for the next drill.",
    ],
    activity: [
      "Reviewed the latest operational performance summary.",
      "Checked continuity and recovery preparedness.",
      "Validated regional service health.",
    ],
    agents: ["Operations", "Support", "SRE", "Continuity"],
    permissions: ["Operational oversight", "Continuity review", "Service delivery", "Regional review"],
  },
  {
    id: "cto",
    label: "Chief Technology Officer",
    domain: "Technology strategy and architecture",
    summary:
      "Owns technology strategy, platform architecture, AI direction, and engineering health.",
    accent: "#4ca7ff",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Executive Leadership",
    presence: "Available",
    metrics: [
      ["Architecture health", "Healthy"],
      ["Deployments", "24"],
      ["Technical debt", "Low"],
      ["AI platform", "Scaling"],
    ],
    actions: [
      "Review roadmap",
      "Inspect architecture",
      "Review platform health",
      "Plan migration",
      "Align architecture",
    ],
    navFocus: "Engineering",
    windows: [
      {
        id: "cto-roadmap",
        title: "Technology Roadmap",
        status: "Strategic",
        summary:
          "Architecture, cloud, AI, and engineering priorities in one technology leadership workspace.",
        bullets: ["Roadmap", "Architecture", "Cloud", "AI", "Delivery"],
      },
      {
        id: "cto-health",
        title: "Platform Health",
        status: "Healthy",
        summary:
          "Engineering health, release velocity, and technical risk surfaced for CTO review.",
        bullets: ["Builds", "Deployments", "Debt", "Quality", "Velocity"],
      },
      {
        id: "cto-architecture",
        title: "Architecture Review",
        status: "Reviewed",
        summary:
          "Major platform architecture changes, trust boundaries, and platform standards are coordinated here.",
        bullets: ["Architecture", "Trust", "Standards", "Services", "Dependencies"],
      },
      {
        id: "cto-ai",
        title: "AI Platform",
        status: "Scaling",
        summary:
          "AI orchestration, agent services, and governed solution generation tracked as a strategic platform.",
        bullets: ["Agents", "Orchestration", "Policies", "Costs", "Scaling"],
      },
    ],
    signals: [
      ["Technical debt", "Low"],
      ["Deployments", "24 active"],
      ["AI maturity", "Scaling"],
      ["Architecture review", "Ready"],
    ],
    notifications: [
      "Technology roadmap is aligned with the current investment plan.",
      "Platform health remains within target.",
      "AI platform scaling review is scheduled.",
    ],
    activity: [
      "Reviewed architecture and cloud strategy.",
      "Checked the engineering delivery trend.",
      "Validated the current AI platform direction.",
    ],
    agents: ["Architecture", "DevOps", "AI Platform", "Engineering"],
    permissions: ["Technology strategy", "Architecture review", "Platform oversight", "Roadmap planning"],
  },
  {
    id: "cfo",
    label: "Chief Financial Officer",
    domain: "Finance and capital management",
    summary:
      "Owns finance, forecasting, budgeting, investor reporting, and cost optimisation.",
    accent: "#f3c46b",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Executive Leadership",
    presence: "Online",
    metrics: [
      ["ARR", "$28.2M"],
      ["Cash flow", "Healthy"],
      ["Margin", "38%"],
      ["Forecast accuracy", "96%"],
    ],
    actions: ["Review forecasts", "Inspect spend", "Approve budget", "Review revenue", "Open procurement"],
    navFocus: "Reports",
    windows: [
      {
        id: "cfo-finance",
        title: "Financial Control",
        status: "Current",
        summary:
          "Revenue, costs, budgeting, and cash flow presented for finance leadership review.",
        bullets: ["Revenue", "Costs", "Cash flow", "Margin", "Forecast"],
      },
      {
        id: "cfo-budget",
        title: "Budget Performance",
        status: "Tracked",
        summary:
          "Budget consumption, investment approval, and forecast variance are captured here.",
        bullets: ["Budget", "Variance", "Investment", "Approvals", "Plan"],
      },
      {
        id: "cfo-ops",
        title: "Cost Optimisation",
        status: "Monitored",
        summary:
          "Cloud spend, vendor commitments, and operational cost efficiency remain visible.",
        bullets: ["Cloud spend", "Vendor cost", "Efficiency", "Savings", "Run rate"],
      },
      {
        id: "cfo-reporting",
        title: "Investor Reporting",
        status: "Prepared",
        summary:
          "Executive financial summaries for leadership, board, and investor reporting cycles.",
        bullets: ["Reporting", "KPIs", "Cash flow", "Forecasts", "Disclosure"],
      },
    ],
    signals: [
      ["ARR", "$28.2M"],
      ["Cash flow", "Healthy"],
      ["Budget variance", "2%"],
      ["Forecast accuracy", "96%"],
    ],
    notifications: [
      "Quarterly financial reporting packet is prepared.",
      "Cost posture remains within target.",
      "Budget requests are within the current envelope.",
    ],
    activity: [
      "Reviewed spend and margin performance.",
      "Validated the current budget forecast.",
      "Checked reporting readiness.",
    ],
    agents: ["Finance", "Procurement", "Analyst", "Strategy"],
    permissions: ["Financial review", "Budget approval", "Reporting", "Procurement visibility"],
  },
  {
    id: "cpo",
    label: "Chief Product Officer",
    domain: "Product strategy and user experience",
    summary:
      "Owns product strategy, roadmap, user experience, and portfolio investment.",
    accent: "#9a7dff",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Executive Leadership",
    presence: "Available",
    metrics: [
      ["Portfolio", "6 products"],
      ["Adoption", "94%"],
      ["NPS", "62"],
      ["Roadmap confidence", "High"],
    ],
    actions: [
      "Review roadmap",
      "Inspect adoption",
      "Review feedback",
      "Prioritize initiatives",
      "Open research",
    ],
    navFocus: "Applications",
    windows: [
      {
        id: "cpo-portfolio",
        title: "Product Portfolio",
        status: "Balanced",
        summary:
          "NovaCodePro, NovaRide, NovaPay, NovaID, NovaHealth, and future products managed together.",
        bullets: ["Portfolio", "Adoption", "Risk", "Value", "Investment"],
      },
      {
        id: "cpo-roadmap",
        title: "Product Roadmap",
        status: "Planned",
        summary:
          "Product roadmap, delivery milestones, and feature prioritisation stay visible to the CPO.",
        bullets: ["Roadmap", "Milestones", "Priorities", "Themes", "Outcomes"],
      },
      {
        id: "cpo-feedback",
        title: "Customer Feedback",
        status: "Tracked",
        summary:
          "User feedback, support trends, and product sentiment inform roadmap choices.",
        bullets: ["Feedback", "Sentiment", "Support", "Requests", "Insights"],
      },
      {
        id: "cpo-research",
        title: "UX and Research",
        status: "Active",
        summary:
          "Research findings and experience quality remain central to product decisions.",
        bullets: ["UX", "Research", "Accessibility", "Journeys", "Experiments"],
      },
    ],
    signals: [
      ["Adoption", "94%"],
      ["NPS", "62"],
      ["Roadmap confidence", "High"],
      ["Feature demand", "Strong"],
    ],
    notifications: [
      "Roadmap review is scheduled for the next product cycle.",
      "Feature adoption remains above plan.",
      "Customer feedback is trending positive.",
    ],
    activity: [
      "Reviewed product portfolio health.",
      "Prioritized new product investments.",
      "Validated the latest user feedback summary.",
    ],
    agents: ["Product", "Research", "Design", "Analytics"],
    permissions: ["Product review", "Roadmap planning", "Portfolio view", "UX oversight"],
  },
  {
    id: "ciso",
    label: "Chief Information Security Officer",
    domain: "Security and risk governance",
    summary:
      "Owns security strategy, Zero Trust, threat detection, incident response, and approvals.",
    accent: "#ff7f7f",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Executive Leadership",
    presence: "Monitoring",
    metrics: [
      ["Security score", "96"],
      ["Threats", "0 critical"],
      ["Vulnerabilities", "2 medium"],
      ["Incident posture", "Green"],
    ],
    actions: [
      "Review threats",
      "Open incident",
      "Inspect policies",
      "Approve exception",
      "Run assessment",
    ],
    navFocus: "Settings",
    windows: [
      {
        id: "ciso-security",
        title: "Security Posture",
        status: "Green",
        summary:
          "Threats, incidents, vulnerability posture, and security score for executive review.",
        bullets: ["Threats", "Vulnerabilities", "Incidents", "Score", "Zero Trust"],
      },
      {
        id: "ciso-threats",
        title: "Threat Operations",
        status: "Monitored",
        summary:
          "Security operations and detection feeds remain visible to the security leader.",
        bullets: ["Detection", "Incidents", "Response", "Containment", "Evidence"],
      },
      {
        id: "ciso-policies",
        title: "Policy and Approvals",
        status: "Controlled",
        summary:
          "Security policies, exceptions, and protected approvals stay governed here.",
        bullets: ["Policies", "Exceptions", "Approvals", "Certificates", "Controls"],
      },
      {
        id: "ciso-risk",
        title: "Risk and Compliance",
        status: "Reviewed",
        summary:
          "Risk posture, compliance mapping, and audit evidence ready for security oversight.",
        bullets: ["Risk", "Compliance", "Audit", "Evidence", "Remediation"],
      },
    ],
    signals: [
      ["Security score", "96"],
      ["Critical threats", "0"],
      ["Vulnerabilities", "2 medium"],
      ["Approvals pending", "1"],
    ],
    notifications: [
      "Security posture remains within target.",
      "One policy update awaits approval.",
      "No critical incidents are open.",
    ],
    activity: [
      "Reviewed the threat and vulnerability summary.",
      "Validated the approval queue.",
      "Checked the current Zero Trust posture.",
    ],
    agents: ["Security", "Compliance", "Threat Intel", "Incident Response"],
    permissions: ["Security approvals", "Threat review", "Policy management", "Incident coordination"],
  },
  {
    id: "chief-legal-compliance-officer",
    label: "Chief Legal & Compliance Officer",
    domain: "Legal, privacy, and compliance",
    summary:
      "Owns legal, privacy, compliance, contracts, regulatory affairs, and governance.",
    accent: "#b6b0a4",
    environment: "Production",
    organization: "NovaTech",
    subscription: "Executive Leadership",
    presence: "Available",
    metrics: [
      ["Open obligations", "7"],
      ["Policy exceptions", "0"],
      ["Contracts", "38"],
      ["Audit findings", "0 critical"],
    ],
    actions: [
      "Review obligations",
      "Inspect contracts",
      "Approve compliance",
      "Review privacy",
      "Open audit pack",
    ],
    navFocus: "Reports",
    windows: [
      {
        id: "legal-compliance",
        title: "Legal Operations",
        status: "Governed",
        summary:
          "Contracts, obligations, and legal review items collected for executive management.",
        bullets: ["Contracts", "Obligations", "Review", "IP", "Regulatory"],
      },
      {
        id: "privacy",
        title: "Privacy and Data",
        status: "Controlled",
        summary:
          "Privacy controls, data usage, and residency topics remain visible for compliance leadership.",
        bullets: ["Privacy", "Residency", "Retention", "Consent", "Controls"],
      },
      {
        id: "compliance",
        title: "Compliance Center",
        status: "Ready",
        summary:
          "Policy exceptions, audit evidence, and regulated workflow approvals stay in scope.",
        bullets: ["Compliance", "Audit", "Exceptions", "Evidence", "Reviews"],
      },
      {
        id: "legal-risk",
        title: "Risk and Governance",
        status: "Monitored",
        summary:
          "Legal, regulatory, and governance risk tracked alongside board-ready evidence.",
        bullets: ["Risk", "Governance", "Regulatory", "Evidence", "Reviews"],
      },
    ],
    signals: [
      ["Open obligations", "7"],
      ["Policy exceptions", "0"],
      ["Contracts", "38"],
      ["Audit findings", "0 critical"],
    ],
    notifications: [
      "No active policy exceptions are open.",
      "Regulatory obligations are within the expected cycle.",
      "Contracts queue is awaiting normal review.",
    ],
    activity: [
      "Reviewed the latest compliance and privacy summary.",
      "Checked open legal obligations.",
      "Validated the audit evidence pack.",
    ],
    agents: ["Legal", "Compliance", "Privacy", "Risk"],
    permissions: ["Compliance review", "Contract oversight", "Privacy governance", "Legal signoff"],
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

const EXPERIENCE_CHANNELS = [
  {
    id: "web",
    title: "Web Frontend",
    domain: "novacodepro.afritechnology.com",
    summary: "Unified enterprise workspace for engineering delivery, governance, PRR, and executive approvals.",
    availability: "Primary",
    auth: "NovaID required",
    version: "Web 1.0",
    region: "Global",
    evidence: "Workspace session and governed state",
    command: "Open web frontend",
  },
  {
    id: "mobile",
    title: "Mobile App",
    domain: "NovaCodePro mobile companion",
    summary: "Executive and operational companion for alerts, incidents, approvals, evidence, and release status.",
    availability: "Companion",
    auth: "Passkey + biometrics",
    version: "Mobile 1.0",
    region: "Offline capable",
    evidence: "Push, review, and on-call workflows",
    command: "Open mobile companion",
  },
  {
    id: "inspector",
    title: "Inspector App",
    domain: "NovaCodePro certification",
    summary: "Field certification, scanning, evidence capture, signed checklists, and offline sync.",
    availability: "Certified",
    auth: "Device trust",
    version: "Inspector 1.0",
    region: "Offline first",
    evidence: "QR, barcode, screenshot, and video capture",
    command: "Open inspector app",
  },
  {
    id: "desktop",
    title: "Desktop App",
    domain: "Tauri workspace",
    summary: "Local coding workspace with editor, terminal, agent runtime, builds, and artifact inspection.",
    availability: "Engineering",
    auth: "Local secure session",
    version: "Desktop 1.0",
    region: "macOS, Windows, Linux",
    evidence: "Local project and artifact sync",
    command: "Open desktop app",
  },
  {
    id: "cli",
    title: "CLI",
    domain: "Automation surface",
    summary: "Command-line control for scaffolding, workflows, verification, deployment, and governance checks.",
    availability: "Automation",
    auth: "Token or passkey session",
    version: "CLI 1.0",
    region: "Local and remote",
    evidence: "Scripted actions and logs",
    command: "Open CLI commands",
  },
  {
    id: "developer",
    title: "Developer Portal",
    domain: "developer.afritechnology.com",
    summary: "API docs, SDKs, sandbox access, webhooks, status, tutorials, and partner onboarding.",
    availability: "Public",
    auth: "Public + sign in",
    version: "Portal 1.0",
    region: "Global",
    evidence: "API docs and release notes",
    command: "Open developer portal",
  },
];

const OPERATIONAL_VERIFICATION_STEPS = [
  {
    status: "Configured",
    detail: "Verification scopes, evidence sources, and channel ownership are defined.",
  },
  {
    status: "Executed",
    detail: "Tests, checks, and validation jobs have run against the active workspace.",
  },
  {
    status: "Verified",
    detail: "Observed results match the governed expectations for the release candidate.",
  },
  {
    status: "Certified",
    detail: "Release evidence, signatures, and reference proofs are captured and stored.",
  },
  {
    status: "Approved",
    detail: "PRR, GA governance, and executive approval are recorded separately from local state.",
  },
];

const DIGITAL_TWIN_LAYERS = [
  ["Observed", "Live enterprise state"],
  ["Desired", "Target operating posture"],
  ["Predicted", "Forward risk model"],
  ["Simulated", "What-if response"],
  ["Approved", "Governed intervention"],
  ["Recovered", "Validated safe state"],
];

const DISTRIBUTED_SERVICES = [
  ["Gateway Service", "Authentication, routing, billing, and workspace entry control."],
  ["NovaID Service", "Identity, SSO, MFA, and role assignment."],
  ["Workflow Service", "Pause, resume, retry, rollback, approve, and replay."],
  ["Agent Orchestrator", "Specialist AI services with execution history and evidence."],
  ["Artifact Service", "Versioned requirements, code, docs, and deployment assets."],
  ["Audit Service", "Immutable audit trail and evidence capture."],
  ["Policy Engine", "Governance rules, approval gates, and compliance checks."],
  ["Notification Service", "Tasks, approvals, alerts, and workflow messages."],
  ["Marketplace Service", "Extensions, agents, and solution packs."],
  ["Search Service", "Semantic discovery across projects and artifacts."],
  ["Deployment Service", "Release promotion, rollback, and verification."],
  ["Release Factory", "Release creation, stage promotion, and publication evidence."],
  ["Billing Service", "Metering, quotas, licensing, and subscriptions."],
  ["Licensing Service", "Entitlements, plan enforcement, and activation."],
  ["Observability Service", "Metrics, logs, traces, SLOs, and incidents."],
];

const PLATFORM_ADMIN_SECTIONS = [
  {
    title: "Identity & Access",
    summary: "NovaID, SSO, MFA, RBAC, roles, permissions, API keys, certificates, and secrets.",
    bullets: ["NovaID", "SSO", "MFA", "RBAC", "Keys", "Certificates"],
    command: "Open identity controls",
  },
  {
    title: "Organizations & Tenants",
    summary: "Provision organizations, tenants, projects, licenses, subscriptions, and ownership boundaries.",
    bullets: ["Organizations", "Tenants", "Projects", "Licenses", "Subscriptions", "Users"],
    command: "Provision tenant",
  },
  {
    title: "Infrastructure & Operations",
    summary: "Manage services, containers, Kubernetes, virtual machines, storage, databases, networking, and DNS.",
    bullets: ["Infrastructure", "Kubernetes", "Storage", "Databases", "Networking", "DNS"],
    command: "Inspect infrastructure",
  },
  {
    title: "Engineering & Delivery",
    summary: "Solution Factory, workflow engine, release center, deployment center, artifact repository, and digital twin.",
    bullets: ["Solution Factory", "Workflow Engine", "Release Center", "Deployment Center", "Artifacts", "Digital Twin"],
    command: "Open release center",
  },
  {
    title: "Governance & Audit",
    summary: "Audit, compliance, security, policy, risk, approvals, certificates, and evidence stay centrally governed.",
    bullets: ["Audit", "Compliance", "Security", "Risk", "Policy", "Evidence"],
    command: "Review security alerts",
  },
  {
    title: "Monitoring & Cost",
    summary: "Metrics, logs, tracing, alerts, health, performance, capacity, and cost visibility for the platform.",
    bullets: ["Metrics", "Logs", "Tracing", "Alerts", "Health", "Cost"],
    command: "Open observability center",
  },
  {
    title: "Marketplace & Settings",
    summary: "Marketplace packs, design systems, branding, notifications, backups, maintenance, and rollout controls.",
    bullets: ["Marketplace", "Design systems", "Branding", "Notifications", "Backups", "Maintenance"],
    command: "Open marketplace",
  },
];

const AUTH_ROLE_TO_PROFILE_ID = {
  ADMIN: "platform-admin",
  PLATFORM_ADMIN: "platform-admin",
  PLATFORM_OWNER: "platform-admin",
  DEVELOPER: "software-engineer",
  PRODUCT_MANAGER: "cpo",
  BUSINESS_ANALYST: "business-administrator",
  UI_UX_DESIGNER: "software-engineer",
  PROJECT_MANAGER: "business-administrator",
  ARCHITECT: "platform-admin",
  QA_ENGINEER: "software-engineer",
  DEVOPS_ENGINEER: "operations-manager",
  CUSTOMER_SUPPORT: "customer-success",
  OPERATIONS_TEAM: "operations-manager",
  BRAND_TEAM: "business-administrator",
  COMPLIANCE_TEAM: "chief-legal-compliance-officer",
  AUDIT_TEAM: "chief-legal-compliance-officer",
  SECURITY_ENGINEER: "ciso",
  INCIDENT_RESPONSE_TEAM: "operations-manager",
  DATA_ARCHITECT: "platform-admin",
  DATA_ENGINEER: "software-engineer",
  DATABASE_ENGINEER: "software-engineer",
  AI_ML_ENGINEER: "software-engineer",
  DATA_SCIENTIST: "software-engineer",
  PRIVACY_COMPLIANCE: "chief-legal-compliance-officer",
  RISK_MANAGEMENT: "chief-legal-compliance-officer",
  LEGAL: "chief-legal-compliance-officer",
  EXTERNAL_REGULATOR: "board",
};

const AUTH_ROLE_DISPLAY_LABELS = {
  ADMIN: "Platform Administrator",
  PLATFORM_ADMIN: "Platform Administrator",
  PLATFORM_OWNER: "Platform Owner",
  DEVELOPER: "Developer",
  PRODUCT_MANAGER: "Product Manager",
  BUSINESS_ANALYST: "Business Analyst",
  UI_UX_DESIGNER: "UI/UX Designer",
  PROJECT_MANAGER: "Project Manager",
  ARCHITECT: "Architect",
  QA_ENGINEER: "QA Engineer",
  DEVOPS_ENGINEER: "DevOps Engineer",
  CUSTOMER_SUPPORT: "Customer Support",
  OPERATIONS_TEAM: "Operations Team",
  BRAND_TEAM: "Brand Team",
  COMPLIANCE_TEAM: "Compliance Team",
  AUDIT_TEAM: "Audit Team",
  SECURITY_ENGINEER: "Security Engineer",
  INCIDENT_RESPONSE_TEAM: "Incident Response Team",
  DATA_ARCHITECT: "Data Architect",
  DATA_ENGINEER: "Data Engineer",
  DATABASE_ENGINEER: "Database Engineer",
  AI_ML_ENGINEER: "AI/ML Engineer",
  DATA_SCIENTIST: "Data Scientist",
  PRIVACY_COMPLIANCE: "Privacy & Compliance",
  RISK_MANAGEMENT: "Risk Management",
  LEGAL: "Legal",
  EXTERNAL_REGULATOR: "Regulator",
};

const AUTH_API_BASE = String(import.meta.env.VITE_NOVACODEPRO_API_BASE_URL || import.meta.env.VITE_AFRIRIDE_API_URL || "")
  .replace(/\/v1\/?$/, "")
  .replace(/\/$/, "");
const FRONTEND_RUNTIME_CONFIG_URL = resolveFrontendRuntimeConfigUrl();
const SESSION_API_BASE = `${AUTH_API_BASE}/v1/novacodepro/session`;
const AUTH_WARNING_MS = 2 * 60 * 1000;

function userSafeText(value, fallback) {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function resolveProfileIdForRole(role) {
  return AUTH_ROLE_TO_PROFILE_ID[role] || AUTH_ROLE_TO_PROFILE_ID.ADMIN;
}

function resolveAuthRoleLabel(role) {
  return AUTH_ROLE_DISPLAY_LABELS[role] || String(role || "").replaceAll("_", " ");
}

function resolveFirstWindowIdForRole(role) {
  const profileId = resolveProfileIdForRole(role);
  return ROLE_PROFILES.find((profile) => profile.id === profileId)?.windows[0]?.id ?? ROLE_PROFILES[0].windows[0].id;
}

function toArray(value) {
  return Array.isArray(value) ? value : [];
}

function toPairArray(value) {
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (Array.isArray(item) && item.length >= 2) {
          return [String(item[0]), String(item[1])];
        }
        if (item && typeof item === "object") {
          const label = item.label ?? item.name ?? item.title ?? item.id ?? "";
          const pairValue = item.value ?? item.detail ?? item.status ?? item.count ?? "";
          if (label || pairValue) {
            return [String(label), String(pairValue)];
          }
        }
        return null;
      })
      .filter(Boolean);
  }
  if (value && typeof value === "object") {
    return Object.entries(value).map(([label, pairValue]) => [String(label), String(pairValue)]);
  }
  return [];
}

function buildSessionFromAuthPayload(payload, fallbackRole, fallbackEmail) {
  const source = payload?.session && typeof payload.session === "object" ? payload.session : payload?.user ?? payload ?? {};
  const context = payload?.context && typeof payload.context === "object" ? payload.context : {};
  const roles = Array.isArray(payload?.roles) && payload.roles.length ? payload.roles : [fallbackRole];
  const assignedRoles = Array.isArray(source.assigned_roles) && source.assigned_roles.length ? source.assigned_roles : roles;
  const permissions = Array.isArray(payload?.permissions) ? payload.permissions : Array.isArray(source.permissions) ? source.permissions : [];
  const tenantId = source.tenant_id ?? payload?.tenant?.id ?? payload?.organization?.id ?? source.organization ?? null;
  const workspace = payload?.workspace && typeof payload.workspace === "object" ? payload.workspace : null;
  return {
    session_id: source.session_id ?? context.session_id ?? null,
    user_id: source.user_id ?? source.id ?? source.username ?? fallbackEmail,
    email: source.email ?? fallbackEmail,
    display_name: source.display_name ?? source.name ?? fallbackEmail,
    organization: source.organization ?? payload?.organization?.id ?? payload?.tenant?.id ?? null,
    tenant_id: tenantId,
    workspace_id: source.workspace_id ?? workspace?.id ?? null,
    workspace,
    active_role: source.active_role ?? roles[0] ?? fallbackRole,
    assigned_roles: assignedRoles,
    permissions,
    status: source.status ?? "active",
    created_at: source.created_at ?? context.created_at ?? new Date().toISOString(),
    last_seen_at: source.last_seen_at ?? context.last_seen_at ?? new Date().toISOString(),
    absolute_expires_at: source.absolute_expires_at ?? context.absolute_expires_at ?? new Date().toISOString(),
    idle_expires_at: source.idle_expires_at ?? context.idle_expires_at ?? new Date().toISOString(),
  };
}

function App() {
  const initialPathname = typeof window !== "undefined" ? window.location.pathname : ROUTES.login;
  const initialLoginRole = resolveWorkspaceLoginRoleFromPathname(initialPathname) || "ADMIN";
  const attachmentInputRef = useRef(null);
  const [currentPathname, setCurrentPathname] = useState(initialPathname);
  const runtime = usePlatformRuntime();
  const [platformSummary, setPlatformSummary] = useState(null);
  const [authStatus, setAuthStatus] = useState("checking");
  const [bootstrapState, setBootstrapState] = useState("loading");
  const [bootstrapError, setBootstrapError] = useState("");
  const [bootstrapErrorReference, setBootstrapErrorReference] = useState("");
  const [bootstrapContext, setBootstrapContext] = useState(null);
  const [bootstrapAttempt, setBootstrapAttempt] = useState(0);
  const [session, setSession] = useState(null);
  const [sessionWarning, setSessionWarning] = useState(false);
  const [frontendRuntimeConfig, setFrontendRuntimeConfig] = useState(() => createDefaultFrontendRuntimeConfig());
  const [frontendRuntimeState, setFrontendRuntimeState] = useState("LOADING");
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [showRoleSwitcher, setShowRoleSwitcher] = useState(false);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginRole, setLoginRole] = useState(initialLoginRole);
  const [loginError, setLoginError] = useState("");
  const [loginErrorReference, setLoginErrorReference] = useState("");
  const [loginStatus, setLoginStatus] = useState("idle");
  const publicAuthRoute = isPublicAuthPath(currentPathname);
  const [toolView, setToolView] = useState("ai");
  const [smartCommand, setSmartCommand] = useState("");
  const [roleId, setRoleId] = useState(resolveProfileIdForRole(initialLoginRole));
  const [search, setSearch] = useState("");
  const [environment, setEnvironment] = useState("Production");
  const [focusNav, setFocusNav] = useState("Dashboard");
  const [selectedWindowId, setSelectedWindowId] = useState(resolveFirstWindowIdForRole(initialLoginRole));
  const [activeWorkspaceSurfaceId, setActiveWorkspaceSurfaceId] = useState("dashboard");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [solutionTemplateId, setSolutionTemplateId] = useState(SOLUTION_TEMPLATES[0].id);
  const [solutionTitle, setSolutionTitle] = useState("");
  const [solutionRequest, setSolutionRequest] = useState(SOLUTION_TEMPLATES[0].request);
  const [solutionDomain, setSolutionDomain] = useState(SOLUTION_TEMPLATES[0].domain);
  const [solutionIndustry, setSolutionIndustry] = useState(SOLUTION_TEMPLATES[0].domain);
  const [solutionCountry, setSolutionCountry] = useState("Australia");
  const [solutionBudget, setSolutionBudget] = useState("$1M");
  const [solutionTimeline, setSolutionTimeline] = useState("12 weeks");
  const [solutionStakeholders, setSolutionStakeholders] = useState(
    "CEO, Product, Security, Finance",
  );
  const [solutionRegion, setSolutionRegion] = useState("Australia");
  const [solutionCompliance, setSolutionCompliance] = useState("enterprise");
  const [solutionSurfaces, setSolutionSurfaces] = useState(
    SOLUTION_TEMPLATES[0].surfaces,
  );
  const [composerPrompt, setComposerPrompt] = useState("");
  const [composerMode, setComposerMode] = useState("full_solution");
  const [composerContextSources, setComposerContextSources] = useState([
    "Current conversation",
    "Current project",
  ]);
  const [composerAgents, setComposerAgents] = useState([
    "Solution Architect",
    "Frontend Engineer",
    "QA Agent",
  ]);
  const [composerAttachments, setComposerAttachments] = useState([]);
  const [composerEnvironment, setComposerEnvironment] = useState(environment);
  const [selectedOutputTab, setSelectedOutputTab] = useState("Overview");
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
  const [selectedJourneyStageId, setSelectedJourneyStageId] = useState(
    WORKFLOW_STAGES[0]?.id ?? "intent",
  );
  const [knowledgeQuery, setKnowledgeQuery] = useState("request");
  const [knowledgeTraceTargetId, setKnowledgeTraceTargetId] = useState("kg-audit");
  const [knowledgeSearchResults, setKnowledgeSearchResults] = useState(runtime.knowledgeGraph);
  const [knowledgeTracePath, setKnowledgeTracePath] = useState(["kg-request", "kg-audit"]);
  const [discoveryAnswers, setDiscoveryAnswers] = useState({
    users: "Customers, operations, and support teams.",
    regions: "Australia, Kenya, and DR Congo.",
    controls: "Regulated payments, privacy, and audit controls.",
    channels: "Mobile apps, web portal, partner APIs.",
    languages: "English, French, and Swahili.",
  });

  const navigateTo = (path, { replace = false } = {}) => {
    const target = path.startsWith("/novacodepro") ? path : `/novacodepro${path.startsWith("/") ? path : `/${path}`}`;
    if (replace) {
      window.history.replaceState({}, "", target);
    } else {
      window.history.pushState({}, "", target);
    }
    setCurrentPathname(target);
  };

  useEffect(() => {
    const handlePopState = () => setCurrentPathname(window.location.pathname);
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    setFrontendRuntimeState("LOADING");
    loadFrontendRuntimeConfig({ signal: controller.signal, runtimeConfigUrl: FRONTEND_RUNTIME_CONFIG_URL })
      .then((config) => {
        if (!active) {
          return;
        }
        setFrontendRuntimeConfig(config);
        setFrontendRuntimeState(config.source === "runtime.json" ? "READY" : "FALLBACK");
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setFrontendRuntimeConfig(createDefaultFrontendRuntimeConfig());
        setFrontendRuntimeState("FALLBACK");
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  useEffect(() => {
    if (authStatus !== "signed-in") {
      return undefined;
    }
    const controller = new AbortController();
    fetch(`${AUTH_API_BASE}/v1/novacodepro/admin/summary`, {
      signal: controller.signal,
      credentials: "include",
    })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (data) {
          setPlatformSummary(data);
        }
      })
      .catch(() => {
        setPlatformSummary(null);
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    (async () => {
      try {
        const { response, payload } = await fetchBootstrap(AUTH_API_BASE, { signal: controller.signal });
        if (!active) {
          return;
        }
        if (!response.ok) {
          const detail = payload?.detail ?? payload ?? {};
          const code = String(detail.code || response.statusText || "APPLICATION_ERROR").toUpperCase();
          if (publicAuthRoute) {
            setBootstrapState("PUBLIC_READY");
            setBootstrapError("");
            setSession(null);
            setAuthStatus("signed-out");
            clearNovaCodeProSessionState();
            return;
          }
          const normalizedFailure = normalizeApiError(detail, response);
          setBootstrapErrorReference(getCorrelationId(normalizedFailure) || createClientReferenceId());
          if (response.status === 401 || code.includes("SESSION_EXPIRED") || code.includes("SESSION_REQUIRED")) {
            setBootstrapState("SESSION_EXPIRED");
            setBootstrapError("Your session expired. Please sign in again.");
            setSession(null);
            setAuthStatus("signed-out");
            clearNovaCodeProSessionState();
            if (currentPathname !== ROUTES.home) {
              navigateTo(ROUTES.loginWithReason("session_expired", resolveSafeReturnTo(currentPathname, "")), { replace: true });
            }
            return;
          }
          if (response.status === 403) {
            setBootstrapState("FORBIDDEN");
            setBootstrapError(userSafeText(detail.message, "Access denied."));
            return;
          }
          if (response.status === 409) {
            setBootstrapState(String(detail.code || "WORKSPACE_REQUIRED").toUpperCase());
            setBootstrapError(userSafeText(detail.message, "Workspace or tenant context is required."));
            return;
          }
          if (response.status >= 500) {
            setBootstrapState("API_UNAVAILABLE");
            setBootstrapError(userSafeText(detail.message, "Bootstrap service unavailable."));
            return;
          }
          setBootstrapState("APPLICATION_ERROR");
          setBootstrapError(userSafeText(detail.message, "Unable to initialize the workspace."));
          return;
        }

        if (publicAuthRoute && !payload?.authenticated) {
          setBootstrapState("PUBLIC_READY");
          setBootstrapError("");
          setSession(null);
          setAuthStatus("signed-out");
          clearNovaCodeProSessionState();
          return;
        }
        const normalized = normalizeBootstrapResponse(payload);
        if (!normalized.authenticated) {
          setBootstrapState("SESSION_EXPIRED");
          setBootstrapError("Authentication is required.");
          setSession(null);
          setAuthStatus("signed-out");
          clearNovaCodeProSessionState();
          if (currentPathname !== ROUTES.home) {
            navigateTo(ROUTES.loginWithReason("session_expired", resolveSafeReturnTo(currentPathname, "")), { replace: true });
          }
          return;
        }
        setBootstrapContext(normalized);
        const nextSession = buildSessionFromAuthPayload(normalized, normalized.roles?.[0] ?? "PLATFORM_ADMIN", loginEmail);
        setSession(nextSession);
        setRoleId(resolveProfileIdForRole(normalized.roles?.[0] ?? "PLATFORM_ADMIN"));
        setEnvironment(normalized.workspace?.selected_environment ?? "Production");
        setAuthStatus("signed-in");
        setBootstrapState("READY");
        setBootstrapError("");
        setBootstrapErrorReference("");
        setLoginError("");
        setActiveWorkspaceSurfaceId("dashboard");
        const returnTo = resolveSafeReturnTo(new URLSearchParams(window.location.search).get("returnTo"), "");
        const bootstrapRoute = currentPathname === ROUTES.home
          ? ROUTES.home
          : returnTo ||
            (isSolutionRoute(currentPathname) || parseNovaCodeProRoute(currentPathname)
              ? currentPathname
              : normalized.default_route || ROUTES.roleDashboard(normalized.roles?.[0] ?? "ADMIN"));
        navigateTo(bootstrapRoute, { replace: true });
      } catch (error) {
        if (!active) {
          return;
        }
        if (error?.name === "AbortError") {
          return;
        }
        if (publicAuthRoute) {
          setBootstrapState("PUBLIC_READY");
          setBootstrapError("");
          setSession(null);
          setAuthStatus("signed-out");
          clearNovaCodeProSessionState();
          return;
        }
        const normalizedError = normalizeApiError(error);
        setBootstrapState("API_UNAVAILABLE");
        setBootstrapError(getUserSafeMessage(normalizedError));
        setBootstrapErrorReference(getCorrelationId(normalizedError) || createClientReferenceId());
        setSession(null);
        setAuthStatus("signed-out");
        clearNovaCodeProSessionState();
      }
    })();

    return () => {
      active = false;
      controller.abort();
    };
  }, [bootstrapAttempt, publicAuthRoute]);

  useEffect(() => {
    if (authStatus !== "signed-in" || !session) {
      setSessionWarning(false);
      return undefined;
    }
    const interval = window.setInterval(() => {
      const idleExpiresAt = Date.parse(session.idle_expires_at);
      if (Number.isNaN(idleExpiresAt)) {
        setSessionWarning(false);
        return;
      }
      setSessionWarning(idleExpiresAt - Date.now() <= AUTH_WARNING_MS);
    }, 15000);
    return () => window.clearInterval(interval);
  }, [authStatus, session]);

  useEffect(() => {
    if (authStatus !== "signed-in") {
      return undefined;
    }
    const interval = window.setInterval(() => {
      fetchBootstrap(AUTH_API_BASE, {})
        .then(({ response, payload }) => {
          if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
              throw new Error("session_expired");
            }
            throw new Error(response.statusText || "session_refresh_failed");
          }
          const normalized = normalizeBootstrapResponse(payload);
          const nextSession = buildSessionFromAuthPayload(normalized, normalized.roles?.[0] ?? loginRole, loginEmail);
          setSession(nextSession);
          setSessionWarning(Date.parse(nextSession.idle_expires_at) - Date.now() <= AUTH_WARNING_MS);
        })
        .catch((error) => {
          const normalizedError = normalizeApiError(error);
          const message = normalizedError.code === "SESSION_EXPIRED" ? "session_expired" : getUserSafeMessage(normalizedError);
          if (/session(_| )?(expired|required|revoked)/i.test(message)) {
            setBootstrapState("SESSION_EXPIRED");
            setBootstrapError("Your session expired. Please sign in again.");
            setSession(null);
            setAuthStatus("signed-out");
            setAccountMenuOpen(false);
            setShowRoleSwitcher(false);
            setSessionWarning(false);
            setRoleId(ROLE_PROFILES[0].id);
            clearNovaCodeProSessionState();
            navigateTo(ROUTES.loginWithReason("session_expired"), { replace: true });
            return;
          }
          setBootstrapState("DEGRADED");
          setBootstrapError(message);
        });
    }, 60000);
    return () => window.clearInterval(interval);
  }, [authStatus, loginEmail, loginRole]);

  const handleLogin = async (event, rememberDevice = false) => {
    event.preventDefault();
    setLoginError("");
    setLoginErrorReference("");
    if (!loginEmail.trim() || !loginPassword) {
      setLoginError("Enter your email or username and password.");
      return;
    }
    setLoginStatus("submitting");
    try {
      const response = await fetch(`${SESSION_API_BASE}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          email: loginEmail,
          password: loginPassword,
          role: loginRole,
          remember_device: Boolean(rememberDevice),
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw normalizeApiError(payload, response);
      }
      const loginSession = buildSessionFromAuthPayload(payload, loginRole, loginEmail);
      setSession(loginSession);
      setRoleId(resolveProfileIdForRole(loginSession.active_role ?? loginRole));
      setSelectedWindowId(resolveFirstWindowIdForRole(loginSession.active_role ?? loginRole));
      setEnvironment("Production");
      setAuthStatus("signed-in");
      setBootstrapState("READY");
      setBootstrapError("");
      setLoginPassword("");
      setAccountMenuOpen(false);
      setShowRoleSwitcher(false);
      setActiveWorkspaceSurfaceId("dashboard");
      const returnTo = resolveSafeReturnTo(new URLSearchParams(window.location.search).get("returnTo"), "");
      let nextRoute =
        returnTo ||
        (isSolutionRoute(currentPathname) ? currentPathname : ROUTES.roleDashboard(loginSession.active_role ?? loginRole));
      try {
        const { response: bootstrapResponse, payload: bootstrapPayload } = await fetchBootstrap(AUTH_API_BASE, {});
        if (bootstrapResponse.ok) {
          const normalized = normalizeBootstrapResponse(bootstrapPayload);
          const normalizedSession = buildSessionFromAuthPayload(
            normalized,
            normalized.roles?.[0] ?? loginSession.active_role ?? loginRole,
            normalized.user?.email ?? loginSession.email ?? loginEmail,
          );
          setBootstrapContext(normalized);
          setSession((current) => ({
            ...(current || {}),
            ...normalizedSession,
            email: normalizedSession.email ?? current?.email ?? loginEmail,
            display_name: normalizedSession.display_name ?? current?.display_name ?? loginSession.display_name,
            organization: normalized.organization?.id ?? current?.organization ?? loginSession.organization ?? null,
            active_role: normalized.roles?.[0] ?? current?.active_role ?? loginSession.active_role ?? loginRole,
            assigned_roles: normalized.roles ?? current?.assigned_roles ?? loginSession.assigned_roles ?? [loginRole],
          }));
          setRoleId(resolveProfileIdForRole(normalized.roles?.[0] ?? loginSession.active_role ?? loginRole));
          setEnvironment(normalized.workspace?.selected_environment ?? "Production");
          setBootstrapState("READY");
          setBootstrapError("");
          setBootstrapErrorReference("");
          nextRoute =
            returnTo ||
            (isSolutionRoute(currentPathname)
              ? currentPathname
              : normalized.default_route || ROUTES.roleDashboard(normalized.roles?.[0] ?? loginSession.active_role ?? loginRole));
        } else if (bootstrapResponse.status === 401 || bootstrapResponse.status === 403) {
          const detail = bootstrapPayload?.detail ?? bootstrapPayload ?? {};
          throw { ...normalizeApiError(detail, bootstrapResponse), code: "SESSION_EXPIRED" };
        } else {
          const detail = bootstrapPayload?.detail ?? bootstrapPayload ?? {};
          setBootstrapState("DEGRADED");
          setBootstrapError(userSafeText(detail.message, bootstrapResponse.statusText || "Bootstrap service unavailable."));
          setBootstrapErrorReference(getCorrelationId(normalizeApiError(detail, bootstrapResponse)) || createClientReferenceId());
        }
      } catch (bootstrapError) {
        const normalizedBootstrapError = normalizeApiError(bootstrapError);
        const message = normalizedBootstrapError.code === "SESSION_EXPIRED" ? "session_expired" : getUserSafeMessage(normalizedBootstrapError);
        if (/session(_| )?(expired|required|revoked)/i.test(message)) {
          throw new Error(message);
        }
        setBootstrapState("DEGRADED");
        setBootstrapError(message);
        setBootstrapErrorReference(getCorrelationId(normalizedBootstrapError) || createClientReferenceId());
      }
      const loginRoute =
        nextRoute;
      navigateTo(loginRoute, { replace: true });
    } catch (error) {
      const normalizedError = normalizeApiError(error);
      if (normalizedError.code === "SESSION_EXPIRED") {
        setBootstrapState("SESSION_EXPIRED");
        setBootstrapError("Your session expired. Please sign in again.");
      }
      clearNovaCodeProSessionState();
      setLoginPassword("");
      setLoginError(getUserSafeMessage(normalizedError));
      setLoginErrorReference(getCorrelationId(normalizedError) || createClientReferenceId());
      setAuthStatus("signed-out");
    } finally {
      setLoginStatus("idle");
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${SESSION_API_BASE}/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch {
      // ignore logout transport failures; local state still clears
    }
    clearNovaCodeProSessionState();
    setPlatformSummary(null);
    setSession(null);
    setAuthStatus("signed-out");
    setBootstrapState("SESSION_EXPIRED");
    setAccountMenuOpen(false);
    setShowRoleSwitcher(false);
    setSessionWarning(false);
    setLoginError("");
    setPaletteOpen(false);
    setSearch("");
    setComposerAttachments([]);
    setRoleId(ROLE_PROFILES[0].id);
    setSelectedWindowId(resolveFirstWindowIdForRole("ADMIN"));
    setActiveWorkspaceSurfaceId("dashboard");
    navigateTo(ROUTES.loginWithReason("session_expired"), { replace: true });
  };

  const handleStaySignedIn = async () => {
    try {
      const response = await fetch(`${SESSION_API_BASE}/refresh`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error("session refresh failed");
      }
      const payload = await response.json();
      setSession(payload.session);
      setSessionWarning(false);
    } catch {
      await handleLogout();
    }
  };

  const handleSwitchRole = async (role) => {
    try {
      const response = await fetch(`${AUTH_API_BASE}/v1/auth/switch-role`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ role }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw normalizeApiError(payload, response);
      }
      setSession(payload.session);
      setRoleId(resolveProfileIdForRole(role));
      setSelectedWindowId(resolveFirstWindowIdForRole(role));
      setActiveWorkspaceSurfaceId("dashboard");
      setAccountMenuOpen(false);
      setShowRoleSwitcher(false);
    } catch (error) {
      setLoginError(getUserSafeMessage(normalizeApiError(error)));
    }
  };

  const focusWorkspaceSurface = (surface) => {
    setActiveWorkspaceSurfaceId(surface.id);
    const target = document.getElementById(surface.anchorId);
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const authDisplayName = session?.display_name || "Djuma";
  const authDisplayRole = session?.active_role || loginRole;
  const authDisplayRoleLabel = resolveAuthRoleLabel(authDisplayRole);
  const authAssignedRoles = toArray(session?.assigned_roles);
  const safeAssignedRoles = authAssignedRoles.length ? authAssignedRoles : [loginRole];
  const authAssignedRoleOptions = safeAssignedRoles.map((role) => ({
    id: role,
    label: role.replaceAll("_", " "),
  }));

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
  const frontendRegistry = useMemo(() => {
    const registry = createDefaultProductFrontendRegistry();
    registerDefaultFrontendManifests(registry);
    return registry;
  }, []);
  const renderingRegistry = useMemo(() => {
    const registry = createDefaultRenderingRegistry();
    registerDefaultRenderingManifests(registry);
    return registry;
  }, []);
  const interactionRegistry = useMemo(() => {
    const registry = createDefaultInteractionRegistry();
    registerDefaultInteractionManifests(registry);
    return registry;
  }, []);
  const frontendProducts = frontendRegistry.list();
  const enabledFrontendProducts = frontendRuntimeConfig.enabledProducts.length
    ? frontendRuntimeConfig.enabledProducts
    : frontendProducts.map((product) => product.productCode);
  const renderingSnapshot = renderingRegistry.snapshot();
  const interactionSnapshot = interactionRegistry.snapshot();
  const requestSummary = useMemo(() => {
    const prompt = composerPrompt.trim();
    return prompt.length ? prompt : selectedRequest?.request || STARTER_REQUESTS[0];
  }, [composerPrompt, selectedRequest?.request]);
  const selectedMode = COMPOSER_MODES.find((mode) => mode.id === composerMode) ?? COMPOSER_MODES[0];

  const aiWorkspaceModel = useMemo(
    () =>
      buildUniversalAIWorkspaceModel({
        session,
        role: authDisplayRole,
        roleLabel: authDisplayRoleLabel,
        workspace: "Universal AI Workspace",
        project: activeProject?.name || selectedRequest?.title,
        tenant: activeTenant?.name || session?.tenant_id,
        organization: activeRole.organization || session?.organization,
        environment,
        route: currentPathname.replace("/novacodepro", "") || "/dashboard",
        modelLabel: `${NOVACODEPRO_BUILD_INFO.version} · ${NOVACODEPRO_BUILD_INFO.commit}`,
        statusLabel:
          frontendRuntimeState === "READY"
            ? "Frontend runtime loaded"
            : "Using fallback runtime config",
        connection: {
          connected: false,
          backend: false,
          runtime: true,
          reason: "No backend AI orchestration API is connected yet.",
          lastSyncedAt: runtime.auditTrail?.[0]?.at || null,
        },
        request: selectedRequest,
        requestState: selectedRequest?.status || "IDLE",
        requestSummary,
        requestConfidence: selectedRequest?.confidence ?? null,
        requestIntent: selectedRequest?.domain || selectedRequest?.templateId || "Unknown",
        requestOutcome: selectedRequest?.summary || selectedRequest?.request || "",
        requestScope: selectedRequest?.surfaces?.join(", ") || "Not connected",
        requestTools: [selectedMode?.label, selectedWindowId, selectedOutputTab].filter(Boolean),
        requestApprovals: runtime.approvalRoutes,
        requestQuestions: ["What outcome is required?", "Which approvals are mandatory?", "Which systems change?"],
        requestFiles: composerAttachments,
        requestArtifacts: selectedRequest?.artifacts || [],
        requestApprovalsState: (selectedRequest?.approvals || []).length ? "PENDING" : "NOT_REQUIRED",
        executionState: selectedRequest?.workflow?.[selectedRequest?.stageIndex ?? 0]?.status || selectedRequest?.status || "IDLE",
        knowledgeState: runtime.knowledgeGraph.length ? "PUBLISHED" : "DRAFT",
        currentAgentTasks:
          runtime.agentTeams.length > 0
            ? runtime.agentTeams.map((team) => ({
                id: team.id,
                name: team.title || team.name || "Agent team",
                role: team.role || "Agent team",
                currentTask: team.summary || "Coordinated AI workstream",
                state: team.status || "RUNNING",
                progress: team.progress || 0,
                startedAt: team.startedAt || team.createdAt || null,
                completedAt: team.completedAt || null,
                outputs: team.outputs || [],
                errors: team.errors || [],
                evidence: team.evidence || [],
                handoffTarget: team.handoffTarget || "",
              }))
            : (composerAgents || []).map((agent, index) => ({
                id: `${agent}-${index}`,
                name: agent,
                role: agent,
                currentTask: `Waiting for backend orchestration for ${agent}`,
                state: "NOT_CONNECTED",
                progress: 0,
                startedAt: null,
                completedAt: null,
                outputs: [],
                errors: [],
                evidence: [],
                handoffTarget: "NovaAI backend",
              })),
        conversations: runtime.collaborationThreads,
        savedPrompts: runtime.commandHistory,
        approvedSolutions: runtime.solutionRequests.filter((request) => request.status === "operating"),
        sharedConversations: runtime.collaborationThreads.filter((thread) => thread.shared),
        recentRequests: runtime.solutionRequests.slice(0, 5),
        suggestedPrompts: activeRole.actions.slice(0, 6),
        artifacts: selectedRequest?.artifacts || [],
        timeline: runtime.auditTrail.map((entry) => ({
          id: entry.id,
          timestamp: entry.at,
          actor: entry.actor,
          agent: entry.service,
          tool: entry.service,
          status: entry.action,
          correlationId: entry.correlationId || entry.id,
          evidenceReference: entry.evidence,
          duration: entry.duration || "",
          severity: entry.severity || "info",
          summary: entry.action,
          error: entry.error || "",
          artifact: entry.subject,
          stage: currentStage?.label || "",
        })),
        approvals: runtime.approvalRoutes,
        evidence: runtime.evidenceBundles,
        knowledge: runtime.knowledgeGraph,
        policies: runtime.approvalPolicies,
        standards: runtime.neraArchitecture?.platformDomains || [],
        context: {
          customer: activeProject?.customer || "Customer",
          project: activeProject?.name || selectedRequest?.title || "NovaCodePro",
          repository: activeProject?.repository || "Not connected",
          branch: activeProject?.branch || "Not connected",
          commit: activeProject?.commit || NOVACODEPRO_BUILD_INFO.commit,
          frontendEnvironment: frontendRuntimeConfig.environment,
          frontendRegion: frontendRuntimeConfig.region,
          frontendReleaseVersion: frontendRuntimeConfig.releaseVersion,
          frontendBuildCommit: frontendRuntimeConfig.buildCommit,
          frontendApiBaseUrl: frontendRuntimeConfig.apiBaseUrl,
          frontendAuthBaseUrl: frontendRuntimeConfig.authBaseUrl,
          frontendEnabledProducts: enabledFrontendProducts,
          frontendConfigSource: frontendRuntimeConfig.source,
          activeArtifact: selectedRequest?.artifacts?.[0]?.title || activeKnowledgeNode?.title || "Not connected",
          planSummary: requestSummary,
          filesChanged: selectedRequest?.artifacts?.length || "Not connected",
          apisChanged: "Not connected",
          migrations: "Not connected",
          testsAdded: "Not connected",
          securityResult: runtime.riskRegister[0]?.status || "Not assessed",
          complianceResult: "Not assessed",
          rollbackPlan: "Revert via governed release rollback.",
          riskLevel: selectedRequest?.compliance || "medium",
          complianceImpact: selectedRequest?.compliance || "enterprise",
          currentStep: currentStage?.label || "Intent analysis",
          queuedSteps: selectedRequest?.workflow?.length ? selectedRequest.workflow.length - (selectedRequest.stageIndex ?? 0) : 0,
          failedSteps: selectedRequest?.workflow?.filter((stage) => stage.status === "failed").length || 0,
          cancelledSteps: selectedRequest?.workflow?.filter((stage) => stage.status === "cancelled").length || 0,
          retries: runtime.eventBus?.retryQueue || 0,
          estimatedRemaining: selectedRequest?.workflow?.length ? `${Math.max(1, selectedRequest.workflow.length - (selectedRequest.stageIndex ?? 0))} stages` : "Not connected",
        },
        metrics: {
          requests: runtime.solutionRequests.length,
          approvals: runtime.approvalRoutes.length,
          evidence: runtime.evidenceBundles.length,
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
      activeProject?.commit,
      activeProject?.customer,
      activeProject?.name,
      activeKnowledgeNode?.title,
      activeRole.actions,
      activeRole.organization,
      activeTenant?.name,
      authDisplayRole,
      authDisplayRoleLabel,
      composerAgents,
      composerAttachments,
      currentPathname,
      currentStage?.label,
      environment,
      requestSummary,
      runtime.auditTrail,
      runtime.approvalPolicies,
      runtime.approvalRoutes,
      runtime.commandCenterSnapshots,
      runtime.commandHistory,
      runtime.evidenceBundles,
      runtime.eventBus?.retryQueue,
      runtime.knowledgeGraph,
      runtime.neraArchitecture?.platformDomains,
      runtime.solutionRequests,
      runtime.agentTeams,
      runtime.collaborationThreads,
      selectedMode?.label,
      selectedOutputTab,
      selectedRequest,
      selectedWindowId,
      session,
      activeKnowledgeNode?.title,
      enabledFrontendProducts,
      frontendRuntimeConfig.apiBaseUrl,
      frontendRuntimeConfig.authBaseUrl,
      frontendRuntimeConfig.buildCommit,
      frontendRuntimeConfig.environment,
      frontendRuntimeConfig.region,
      frontendRuntimeConfig.releaseVersion,
      frontendRuntimeConfig.source,
      frontendRuntimeState,
      NOVACODEPRO_BUILD_INFO.commit,
      NOVACODEPRO_BUILD_INFO.version,
    ],
  );
  const renderBootstrapLoading = (title, message, code) => (
    <div className="auth-shell">
      <header className="auth-topbar">
        <div className="brand-block">
          <img className="brand-logo" src="/brand/NOVACODEPRO.webp" alt="NovaCodePro logo" />
          <div>
            <p className="eyebrow">NovaCodePro bootstrapping</p>
            <strong>NovaCodePro</strong>
          </div>
        </div>
      </header>
      <main className="auth-panel">
        <section className="auth-copy">
          <p className="section-label">Loading workspace</p>
          <h1>{title}</h1>
          <p className="hero-summary">{message}</p>
          <p className="auth-error">State: {code}</p>
          <p className="hero-summary">
            Version {NOVACODEPRO_BUILD_INFO.version} · Build {NOVACODEPRO_BUILD_INFO.build_id} · Commit{" "}
            {NOVACODEPRO_BUILD_INFO.commit}
          </p>
        </section>
        <div className="auth-form">
          <button type="button" className="secondary-action" onClick={() => window.location.replace(ROUTES.dashboard)}>
            Reload application
          </button>
        </div>
      </main>
    </div>
  );

  const renderBootstrapRecovery = (title, message, code) => (
    <div className="auth-shell">
      <header className="auth-topbar">
        <div className="brand-block">
          <img className="brand-logo" src="/brand/NOVACODEPRO.webp" alt="NovaCodePro logo" />
          <div>
            <p className="eyebrow">NovaCodePro recovery screen</p>
            <strong>NovaCodePro</strong>
          </div>
        </div>
      </header>
      <main className="auth-panel">
        <section className="auth-copy">
          <p className="section-label">Workspace unavailable</p>
          <h1>{title}</h1>
          <p className="hero-summary">{message}</p>
          <p className="auth-error">State: {code}</p>
          {bootstrapErrorReference ? <p className="hero-summary">Diagnostic reference: {bootstrapErrorReference}</p> : null}
          <p className="hero-summary">
            Version {NOVACODEPRO_BUILD_INFO.version} · Build {NOVACODEPRO_BUILD_INFO.build_id} · Commit{" "}
            {NOVACODEPRO_BUILD_INFO.commit}
          </p>
        </section>
        <div className="auth-form">
          <button
            type="button"
            className="novaid-button"
            onClick={() => {
              setBootstrapState("loading");
              setBootstrapError("");
              setBootstrapErrorReference("");
              setAuthStatus("checking");
              setBootstrapAttempt((value) => value + 1);
            }}
          >
            Retry
          </button>
          <button type="button" className="secondary-action" onClick={() => window.location.replace(ROUTES.dashboard)}>
            Reload application
          </button>
          <button
            type="button"
            className="secondary-action"
            onClick={() => {
              clearNovaCodeProSessionState();
              window.location.assign(ROUTES.loginWithReason("session_expired"));
            }}
          >
            Sign in again
          </button>
          <button
            type="button"
            className="secondary-action"
            onClick={async () => {
              try {
                await fetch(`${SESSION_API_BASE}/logout`, { method: "POST", credentials: "include" });
              } catch {
                // Ignore sign-out failures.
              }
              clearNovaCodeProSessionState();
              window.location.assign(ROUTES.loginWithReason("session_expired"));
            }}
          >
            Clear local session
          </button>
        </div>
      </main>
    </div>
  );

  const bootstrapLoadingScreen = renderBootstrapLoading(
    "Loading your NovaCodePro workspace.",
    "Resolving identity, tenant, workspace, and governance context.",
    "BOOTSTRAP_LOADING",
  );
  const bootstrapRecoveryScreen = renderBootstrapRecovery(
    "NovaCodePro could not load this workspace.",
    bootstrapError || "A managed recovery state is required before the dashboard can render.",
    bootstrapState,
  );
  const deniedApplication = findNovaCodeProAppByPath(currentPathname);
  const forbiddenScreen = (
    <div className="auth-shell">
      <header className="auth-topbar">
        <div className="brand-block">
          <img className="brand-logo" src="/brand/NOVACODEPRO.webp" alt="NovaCodePro logo" />
          <div>
            <p className="eyebrow">NovaCodePro access control</p>
            <strong>NovaCodePro</strong>
          </div>
        </div>
      </header>

      <main className="auth-panel">
        <section className="auth-copy">
          <p className="section-label">Access denied</p>
          <h1>You do not have access to this area.</h1>
          <p className="hero-summary">
            Your authenticated session is valid, but the current workspace role does not grant this capability.
          </p>
          <p className="auth-error">State: FORBIDDEN</p>
          <p className="hero-summary">Workspace: {session?.workspace?.name || session?.workspace_id || "Not selected"}</p>
          <p className="hero-summary">Role: {session?.active_role || "Member"}</p>
          {deniedApplication?.requiredPermissions?.length ? <p className="hero-summary">Required capability: {deniedApplication.requiredPermissions.join(", ")}</p> : null}
        </section>
        <div className="auth-form">
          <button
            type="button"
            className="novaid-button"
            onClick={() => {
              setBootstrapState("loading");
              setBootstrapError("");
              setAuthStatus("checking");
              setBootstrapAttempt((value) => value + 1);
            }}
          >
            Recheck access
          </button>
          <button type="button" className="secondary-action" onClick={() => navigateTo(ROUTES.workspaceRoot, { replace: true })}>
            Return to workspace
          </button>
          <button type="button" className="secondary-action" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </main>
    </div>
  );
  const signedOutScreen = (
    <LoginPage
      email={loginEmail}
      password={loginPassword}
      role={loginRole}
      error={loginError || bootstrapError}
      errorReference={loginErrorReference}
      status={loginStatus}
      buildInfo={NOVACODEPRO_BUILD_INFO}
      onEmailChange={setLoginEmail}
      onPasswordChange={setLoginPassword}
      onRoleChange={setLoginRole}
      onSubmit={handleLogin}
      onHome={() => navigateTo(ROUTES.home)}
      onUnavailable={setLoginError}
    />
  );

  const activeAutomationTemplate =
    AUTOMATION_TEMPLATES.find((template) => template.id === automationTemplateId) ??
    AUTOMATION_TEMPLATES[0];
  const latestEvidenceBundle = runtime.evidenceBundles[0];
  const latestRiskItem = runtime.riskRegister[0];
  const latestApprovalRoute = runtime.approvalRoutes[0];
  const latestTwinScenario = runtime.digitalTwinScenarios[0];
  const latestExecutiveInsight = runtime.executiveInsights[0];
  const latestCommandSnapshot = runtime.commandCenterSnapshots[0];
  const workflowJourneyStages = selectedRequest?.workflow?.length ? selectedRequest.workflow : WORKFLOW_STAGES;
  const selectedJourneyStage =
    workflowJourneyStages.find((stage) => stage.id === selectedJourneyStageId) ??
    selectedRequest?.workflow?.[selectedRequest.stageIndex] ??
    workflowJourneyStages[0];

  const solutionBlueprint = useMemo(() => {
    const template =
      SOLUTION_TEMPLATES.find((item) => item.id === solutionTemplateId) ?? SOLUTION_TEMPLATES[0];
    return {
      template,
      title: solutionTitle || template.title,
      request: solutionRequest || template.request,
      domain: solutionDomain || template.domain,
      industry: solutionIndustry || template.domain,
      country: solutionCountry,
      budget: solutionBudget,
      timeline: solutionTimeline,
      stakeholders: solutionStakeholders,
      region: solutionRegion,
      compliance: solutionCompliance,
      surfaces: solutionSurfaces,
    };
  }, [
    solutionCompliance,
    solutionCountry,
    solutionDomain,
    solutionBudget,
    solutionIndustry,
    solutionStakeholders,
    solutionTimeline,
    solutionRegion,
    solutionRequest,
    solutionSurfaces,
    solutionTemplateId,
    solutionTitle,
  ]);

  const selectedWindow =
    activeRole.windows.find((window) => window.id === selectedWindowId) ?? activeRole.windows[0];

  const secondaryWindows = activeRole.windows.filter((window) => window.id !== selectedWindow.id);
  useEffect(() => {
    setToolView("ai");
  }, [roleId, selectedWindowId]);
  const localAdminSummary = useMemo(() => {
    const serviceRegistry = platformSummary?.service_registry ?? [];
    return {
      platform_health: platformSummary?.platform_health ?? "healthy",
      service_count: platformSummary?.service_count ?? serviceRegistry.length,
      tenant_count: platformSummary?.tenant_count ?? runtime.tenants.length,
      workflow_count: platformSummary?.workflow_count ?? runtime.solutionRequests.length,
      release_count: platformSummary?.release_count ?? runtime.automationRuns.length,
      deployment_count: platformSummary?.deployment_count ?? 0,
      approval_count: platformSummary?.approval_count ?? runtime.auditTrail.length,
      digital_twin_count: platformSummary?.digital_twin_count ?? 1,
      connected_integration_count:
        platformSummary?.connected_integration_count ?? runtime.connectedIntegrations.length,
      marketplace_count: platformSummary?.marketplace_count ?? AGENT_MARKETPLACE.length,
      audit_event_count: platformSummary?.audit_event_count ?? runtime.auditTrail.length,
      service_registry:
        serviceRegistry.length > 0
          ? serviceRegistry
              : [
                  { name: "NovaCodePro Gateway", status: "healthy", category: "control-plane" },
                  { name: "Workflow Service", status: "healthy", category: "orchestration" },
                  { name: "Agent Orchestrator", status: "healthy", category: "execution" },
                  { name: "Artifact Service", status: "healthy", category: "storage" },
                  { name: "Approval Service", status: "healthy", category: "governance" },
                  { name: "Policy Engine", status: "healthy", category: "routing" },
                  { name: "Release Factory", status: "healthy", category: "delivery" },
                  { name: "Digital Twin Engine", status: "healthy", category: "observability" },
        ],
    };
  }, [platformSummary, runtime.connectedIntegrations.length, runtime.auditTrail.length, runtime.solutionRequests.length, runtime.tenants.length]);

  const enterpriseCommandCenter = useMemo(() => {
    const securityEvents = runtime.auditTrail.filter((event) =>
      /security|policy|approval|compliance/i.test(`${event.action} ${event.service} ${event.subject}`),
    ).length;
    const releaseEvents = runtime.auditTrail.filter((event) =>
      /release|deploy|workflow/i.test(`${event.action} ${event.service} ${event.subject}`),
    ).length;
    const workflowHealth =
      selectedRequest?.workflow?.length
        ? Math.round(
            (selectedRequest.workflow.filter((stage) => stage.status === "completed").length /
              selectedRequest.workflow.length) *
              100,
          )
        : 0;

    return [
      {
        label: "Enterprise health score",
        value: platformSummary?.platform_health === "healthy" ? "99.98%" : "97.40%",
        note: "Aggregated from service, workflow, and audit signals.",
      },
      {
        label: "Operational readiness",
        value: `${Math.min(100, workflowHealth || 88)}%`,
        note: "Based on the currently selected governed solution.",
      },
      {
        label: "Trust score",
        value: `${Math.max(86, 100 - securityEvents * 2)}%`,
        note: "Approvals, evidence, and audit integrity are factored in.",
      },
      {
        label: "Risk score",
        value: `${Math.max(12, 40 - securityEvents - releaseEvents)}%`,
        note: "Higher numbers reflect more open risk on the active workspace.",
      },
      {
        label: "AI governance",
        value: `${runtime.automationRuns.length + runtime.knowledgeGraph.length}`,
        note: "Active automation runs and enterprise knowledge assets.",
      },
      {
        label: "Command readiness",
        value: "Mission control",
        note: "Cross-domain alerts, approvals, and recovery actions are available.",
      },
    ];
  }, [platformSummary?.platform_health, runtime.auditTrail, runtime.automationRuns.length, runtime.knowledgeGraph.length, selectedRequest?.workflow]);

  const uxOperatingSummary = useMemo(() => {
    const uxModel = runtime.uxOperatingSystem || UX_OPERATING_SYSTEM;
    const artifacts = runtime.uxArtifacts || [];
    const evidenceCount = artifacts.reduce((total, artifact) => total + (artifact.evidence?.length || 0), 0);
    const approvedComponents = (runtime.uxComponentRegistry || UX_COMPONENT_REGISTRY).filter(
      (component) => component.status === "APPROVED",
    ).length;
    return {
      model: uxModel,
      artifacts,
      evidenceCount,
      approvedComponents,
      serviceCount: (runtime.uxosRuntimeServices || UXOS_RUNTIME_SERVICES).length,
      serviceRecords: runtime.uxosServiceRecords || [],
      readiness: runtime.uxReleaseReadiness || { status: "EVIDENCE_PENDING", gaAllowed: false, missing: [] },
      visibleLifecycle: uxModel.lifecycle.slice(0, 8),
      approvalLifecycle: uxModel.stateModel.slice(-5),
    };
  }, [runtime.uxArtifacts, runtime.uxComponentRegistry, runtime.uxOperatingSystem, runtime.uxReleaseReadiness, runtime.uxosRuntimeServices, runtime.uxosServiceRecords]);

  const completionSummary = useMemo(() => {
    const dashboard = runtime.completionDashboard || {
      rows: COMPLETION_STANDARD.domains.map((domain) => ({
        domain,
        repository: domain !== "GA Promotion",
        operational: false,
        governance: "PENDING",
      })),
      gaAllowed: false,
      realPaymentsEnabled: false,
    };
    return {
      standard: runtime.completionStandard || COMPLETION_STANDARD,
      dashboard,
      assessment: runtime.completionAssessment || {
        level: "Repository Complete",
        repositoryComplete: true,
        operationalVerified: false,
        governanceApproved: false,
        productionReady: false,
        gaAllowed: false,
        realPaymentsEnabled: false,
        missingProductionGates: COMPLETION_STANDARD.productionReadyGates,
      },
    };
  }, [runtime.completionAssessment, runtime.completionDashboard, runtime.completionStandard]);

  const operationalReadinessSummary = useMemo(() => {
    return {
      program: runtime.operationalReadinessProgram || OPERATIONAL_READINESS_PROGRAM,
      assessment: runtime.operationalReadinessAssessment || {
        status: "OPERATIONAL_READINESS_BLOCKED",
        repositoryComplete: true,
        operationalVerified: false,
        governanceComplete: false,
        gaAllowed: false,
        realPaymentsEnabled: false,
      },
    };
  }, [runtime.operationalReadinessAssessment, runtime.operationalReadinessProgram]);

  useEffect(() => {
    setSelectedJourneyStageId(selectedRequest?.workflow?.[selectedRequest.stageIndex]?.id ?? workflowJourneyStages[0]?.id ?? "intent");
  }, [selectedRequest?.id, selectedRequest?.stageIndex, workflowJourneyStages]);

  useEffect(() => {
    setComposerEnvironment(environment);
  }, [environment]);

  const activeRequest = selectedRequest;
  const activeStage = activeRequest?.workflow?.[activeRequest.stageIndex];
  const workflowProgress = activeRequest?.workflow?.length
    ? Math.round(
        (activeRequest.workflow.filter((stage) => stage.status === "completed").length /
          activeRequest.workflow.length) *
          100,
      )
    : 0;
  const activeOutputTab = OUTPUT_TABS.includes(selectedOutputTab) ? selectedOutputTab : "Overview";

  const suggestedTitle = useMemo(() => {
    const source = requestSummary.split(/[.!?]/)[0].trim();
    if (!source) {
      return "NovaCodePro solution request";
    }
    return source.length > 64 ? `${source.slice(0, 61)}...` : source;
  }, [requestSummary]);

  const studioMenus = useMemo(
    () => [
      {
        id: "file",
        label: "File",
        shortcut: "Alt+F",
        items: [
          { id: "open-workspace", label: "Open workspace", description: "Go to the governed workspace hub", action: () => navigateTo(ROUTES.workspaceRoot) },
          { id: "open-solution", label: "Open solution engineering", description: "Switch to the solution engineering studio", action: () => navigateTo(ROUTES.solutionRoot) },
          { id: "save-draft", label: "Save draft", description: "Persist the current workspace draft", action: () => platformRuntime.runCommand("Save draft") },
          { id: "command-palette", label: "Command palette", description: "Search commands, requirements, tests, and files", action: () => setPaletteOpen(true) },
        ],
      },
      {
        id: "edit",
        label: "Edit",
        shortcut: "Alt+E",
        items: [
          { id: "undo", label: "Undo", description: "Undo the last local change", action: () => platformRuntime.runCommand("Undo") },
          { id: "redo", label: "Redo", description: "Redo the last local change", action: () => platformRuntime.runCommand("Redo") },
          { id: "search", label: "Search", description: "Search files, APIs, tests, and evidence", action: () => setFocusNav("Search") },
          { id: "format", label: "Format", description: "Format the current file or selection", action: () => platformRuntime.runCommand("Format selection") },
        ],
      },
      {
        id: "view",
        label: "View",
        shortcut: "Alt+V",
        items: [
          { id: "dashboard", label: "Dashboard", description: "Return to the main workspace overview", action: () => setFocusNav("Dashboard") },
          { id: "workspace", label: "Workspace", description: "Focus the workspace explorer", action: () => setFocusNav("Workspace") },
          { id: "ai", label: "AI workspace", description: "Focus NovaAI context and agents", action: () => setToolView("ai") },
          { id: "operations", label: "Operations", description: "Review live operations and signals", action: () => setFocusNav("Operations") },
        ],
      },
      {
        id: "build",
        label: "Build",
        shortcut: "Alt+B",
        items: [
          { id: "build", label: "Build", description: "Run the current governed build workflow", action: () => platformRuntime.runCommand("Build") },
          { id: "rebuild", label: "Rebuild", description: "Clean and rebuild the current target", action: () => platformRuntime.runCommand("Rebuild") },
          { id: "clean", label: "Clean", description: "Clean generated workspace artifacts", action: () => platformRuntime.runCommand("Clean") },
          { id: "validate", label: "Validate", description: "Run architecture and governance validation", action: () => platformRuntime.runCommand("Validate") },
        ],
      },
      {
        id: "run",
        label: "Run",
        shortcut: "Alt+R",
        items: [
          { id: "run", label: "Run", description: "Launch the selected target", action: () => platformRuntime.runCommand("Run") },
          { id: "stop", label: "Stop", description: "Stop the active session or process", action: () => platformRuntime.runCommand("Stop") },
          { id: "debug", label: "Debug", description: "Open debug controls", action: () => setFocusNav("Inspector") },
          { id: "restart", label: "Restart", description: "Restart the active workspace target", action: () => platformRuntime.runCommand("Restart") },
        ],
      },
      {
        id: "test",
        label: "Test",
        shortcut: "Alt+T",
        items: [
          { id: "test-all", label: "Run tests", description: "Execute the current validation suite", action: () => platformRuntime.runCommand("Run tests") },
          { id: "failed", label: "Run failed tests", description: "Re-run failed tests only", action: () => platformRuntime.runCommand("Run failed tests") },
          { id: "coverage", label: "Coverage", description: "Open coverage and quality findings", action: () => setSelectedOutputTab("Tests") },
          { id: "accessibility", label: "Accessibility", description: "Open accessibility validation", action: () => setFocusNav("Governance") },
        ],
      },
      {
        id: "git",
        label: "Git",
        shortcut: "Alt+G",
        items: [
          { id: "pull", label: "Pull", description: "Fetch and merge the latest remote changes", action: () => platformRuntime.runCommand("Pull") },
          { id: "push", label: "Push", description: "Push the current branch", action: () => platformRuntime.runCommand("Push") },
          { id: "sync", label: "Sync", description: "Synchronize the workspace branch", action: () => platformRuntime.runCommand("Sync") },
          { id: "commit", label: "Commit", description: "Open the commit flow", action: () => platformRuntime.runCommand("Commit") },
        ],
      },
      {
        id: "ai",
        label: "AI",
        shortcut: "Alt+I",
        items: [
          { id: "ask", label: "Ask NovaAI", description: "Open the governed AI workspace", action: () => setToolView("ai") },
          { id: "generate-tests", label: "Generate tests", description: "Ask NovaAI to generate test coverage", action: () => setComposerPrompt("Generate tests for the currently selected workspace context.") },
          { id: "refactor", label: "Refactor safely", description: "Request an impact-aware refactor plan", action: () => setComposerPrompt("Refactor safely with impact analysis, rollback steps, and test coverage.") },
          { id: "explain", label: "Explain selection", description: "Ask NovaAI to explain the current selection", action: () => setComposerPrompt("Explain the current selection with architecture, security, and performance context.") },
        ],
      },
      {
        id: "governance",
        label: "Governance",
        shortcut: "Alt+Shift+G",
        items: [
          { id: "review-security", label: "Security review", description: "Inspect governance and security findings", action: () => setFocusNav("Security") },
          { id: "traceability", label: "Traceability", description: "Open traceability and evidence links", action: () => setFocusNav("Traceability") },
          { id: "deploy", label: "Deploy", description: "Review deployment controls", action: () => setFocusNav("Deploy") },
          { id: "settings", label: "Settings", description: "Open workspace and policy settings", action: () => setFocusNav("Settings") },
        ],
      },
    ],
    [navigateTo, platformRuntime, setComposerPrompt, setFocusNav, setPaletteOpen, setSelectedOutputTab, setToolView],
  );

  const studioActivityItems = useMemo(
    () => [
      { id: "Dashboard", label: "Home", icon: "⌂", description: "Workspace overview and status" },
      { id: "Workspace", label: "Workspace", icon: "▣", description: "Current organization and workspace context" },
      { id: "Explorer", label: "Explorer", icon: "⟂", description: "Browse repositories, files, and artifacts" },
      { id: "Search", label: "Search", icon: "⌕", description: "Search files, APIs, requirements, and evidence" },
      { id: "Git", label: "Git", icon: "⎇", description: "Source control and branches" },
      { id: "Debug", label: "Debug", icon: "▶", description: "Run and debug workspace targets" },
      { id: "Testing", label: "Testing", icon: "🧪", description: "Test discovery and execution" },
      { id: "AI", label: "NovaAI", icon: "🤖", description: "Context-aware AI workspace" },
      { id: "Architecture", label: "Architecture", icon: "⌘", description: "Architecture and traceability views" },
      { id: "Design", label: "Design", icon: "◫", description: "Design studio and UI layout" },
      { id: "Database", label: "Database", icon: "▤", description: "Database and schema tooling" },
      { id: "API", label: "API", icon: "⇄", description: "API design and validation" },
      { id: "Security", label: "Security", icon: "🛡", description: "Security findings and controls" },
      { id: "Deploy", label: "Deploy", icon: "☁", description: "Deployment workflows and approvals" },
      { id: "Operate", label: "Operate", icon: "📈", description: "Operational dashboards and signals" },
      { id: "Governance", label: "Governance", icon: "⟡", description: "Governance, policy, and release gates" },
      { id: "Traceability", label: "Traceability", icon: "⟐", description: "Requirements-to-code-to-evidence links" },
      { id: "Settings", label: "Settings", icon: "⚙", description: "Workspace and policy preferences" },
    ],
    [],
  );

  const studioContextItems = useMemo(
    () => [
      { label: "Organisation", value: activeRole.organization || session?.organization?.name || "NovaTech" },
      { label: "Workspace", value: activeTenant?.name || session?.workspace?.name || "Workspace" },
      { label: "Project", value: activeProject?.name || selectedRequest?.title || "NovaCodePro" },
      { label: "Repository", value: activeProject?.repository || "Not connected" },
      { label: "Branch", value: activeProject?.branch || "Not connected" },
      { label: "Environment", value: environment },
      { label: "Trust", value: sessionWarning ? "Session expiring soon" : "Trusted workspace" },
      { label: "AI", value: toolView === "ai" ? "NovaAI active" : "NovaAI available" },
      { label: "Build", value: platformSummary?.platform_health || "healthy" },
      { label: "Git", value: selectedOutputTab || "Overview" },
    ],
    [
      activeProject?.branch,
      activeProject?.name,
      activeProject?.repository,
      activeRole.organization,
      activeTenant?.name,
      environment,
      platformSummary?.platform_health,
      selectedOutputTab,
      selectedRequest?.title,
      session?.organization?.name,
      session?.workspace?.name,
      sessionWarning,
      toolView,
    ],
  );

  const studioStatusItems = useMemo(
    () => [
      { label: "Auth", value: authStatus === "signed-in" ? "Signed in" : authStatus, tone: authStatus === "signed-in" ? "success" : "warning" },
      { label: "Session", value: sessionWarning ? "Refreshing" : "Healthy", tone: sessionWarning ? "warning" : "success" },
      { label: "Connection", value: frontendRuntimeState === "READY" ? "Connected" : frontendRuntimeState.toLowerCase(), tone: frontendRuntimeState === "READY" ? "success" : "warning" },
      { label: "Environment", value: environment, tone: "info" },
      { label: "Role", value: authDisplayRoleLabel, tone: "info" },
      { label: "AI", value: toolView === "ai" ? "Active" : "Idle", tone: toolView === "ai" ? "success" : "info" },
    ],
    [authDisplayRoleLabel, authStatus, environment, frontendRuntimeState, sessionWarning, toolView],
  );

  const roleWorkspaceModel = useMemo(
    () =>
      buildRoleWorkspaceModel({
        activeRole,
        runtime,
        platformSummary,
        environment,
        activeTenant,
        activeProject,
        activeRequest,
        activeStage,
        workflowProgress,
        authDisplayName,
        authDisplayRoleLabel,
        selectedModeLabel: selectedMode?.label,
        requestSummary,
        suggestedTitle,
      }),
    [
      activeRole,
      activeTenant,
      activeProject,
      activeRequest,
      activeStage,
      authDisplayName,
      authDisplayRoleLabel,
      environment,
      platformSummary,
      requestSummary,
      runtime,
      selectedMode?.label,
      suggestedTitle,
      workflowProgress,
    ],
  );

  const toggleComposerContextSource = (source) => {
    setComposerContextSources((current) =>
      current.includes(source) ? current.filter((item) => item !== source) : [...current, source],
    );
  };

  const toggleComposerAgent = (agent) => {
    setComposerAgents((current) =>
      current.includes(agent) ? current.filter((item) => item !== agent) : [...current, agent],
    );
  };

  const runKnowledgeQuery = () => {
    setKnowledgeSearchResults(runtime.queryKnowledgeGraph(knowledgeQuery));
  };

  const refreshKnowledgeTrace = () => {
    setKnowledgeTracePath(runtime.traceKnowledgePath(activeKnowledgeNode.id, knowledgeTraceTargetId));
  };

  const runSharedInteraction = () => {
    const subject = activeRequest?.title || suggestedTitle;
    runtime.runEnterpriseInteraction({
      subject,
      actor: "NovaID",
      action: "enterprise.interaction.routed",
      policyId: "policy-prod-release",
      artifacts: activeRequest?.artifacts?.slice(0, 3).map((artifact) => artifact.id) ?? [],
      environment,
      region: activeTenant?.regions?.[0] || "Global",
      question: `What threatens ${subject}?`,
      summary: `Shared interaction bundle generated for ${subject}.`,
      scenarioTitle: `${subject} scenario`,
      expectedImpact: `${Math.max(2, (activeRequest?.workflow?.length || 4) - 2)} services`,
      revenueRisk: activeProject?.budget || "$0",
      recovery: "23 minutes",
      affectedCustomers: "3,212",
      likelihood: activeRequest?.compliance === "very high" ? "high" : "medium",
      impact: activeRequest?.compliance === "very high" ? "high" : "medium",
      exposure: activeRequest?.region === "Australia" ? "medium" : "high",
      owner: "Enterprise Risk",
      recommendations: [
        "Preserve approval gates and evidence capture.",
        "Correlate operations data with the knowledge graph.",
        "Update the command center snapshot after execution.",
      ],
    });
    setSelectedOutputTab("Evidence");
  };

  const handleAttachmentUpload = (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) {
      return;
    }
    const nextAttachments = files.map((file) => ({
      id: `attachment-${Math.random().toString(36).slice(2, 10)}`,
      name: file.name,
      type: file.type || "application/octet-stream",
      size: file.size,
      source: "Local upload",
      security: file.type.startsWith("image/") ? "scanned" : "queued",
      indexing: "pending",
    }));
    setComposerAttachments((current) => [...nextAttachments, ...current].slice(0, 10));
    event.target.value = "";
  };

  const removeComposerAttachment = (attachmentId) => {
    setComposerAttachments((current) => current.filter((attachment) => attachment.id !== attachmentId));
  };

  const submitComposer = (action) => {
    const prompt = composerPrompt.trim();
    if (!prompt) {
      return;
    }
    const template =
      SOLUTION_TEMPLATES.find((item) => prompt.toLowerCase().includes(item.domain)) ??
      SOLUTION_TEMPLATES[0];
    const request = platformRuntime.createSolution({
      title: suggestedTitle,
      request: prompt,
      mode: composerMode,
      domain: template.domain,
      industry: solutionIndustry || template.domain,
      country: solutionCountry,
      budget: solutionBudget,
      timeline: solutionTimeline,
      stakeholders: solutionStakeholders,
      region: environment,
      compliance: solutionCompliance,
      surfaces: composerMode === "ask" ? ["Conversation"] : solutionSurfaces,
      template,
      attachments: composerAttachments,
      contextSources: composerContextSources,
      selectedAgents: composerAgents,
      environment: composerEnvironment,
    });
    setSelectedOutputTab("Overview");
    setComposerPrompt("");
    setComposerAttachments([]);
    if (action === "Send and execute") {
      platformRuntime.advanceWorkflow(request.id);
    }
  };

  function renderOutputTabContent() {
    const currentArtifacts = activeRequest?.artifacts ?? [];
    const currentWorkflow = activeRequest?.workflow ?? [];

    switch (activeOutputTab) {
      case "Plan":
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Proposed execution plan</p>
              <strong>Discover, design, build, validate, secure, and release</strong>
              <div className="workflow-track compact">
                {currentWorkflow.map((stage, index) => (
                  <React.Fragment key={stage.id}>
                    <div className="workflow-step">
                      <span>{String(index + 1).padStart(2, "0")}</span>
                      <strong>{stage.label}</strong>
                      <em>{stage.status}</em>
                    </div>
                    {index < currentWorkflow.length - 1 ? <div className="workflow-arrow">→</div> : null}
                  </React.Fragment>
                ))}
              </div>
            </article>
            <div className="dual-grid">
              <article className="output-card">
                <p className="section-label">Recommended agents</p>
                <div className="chip-cloud">
                  {composerAgents.map((agent) => (
                    <span className="context-chip active" key={agent}>
                      {agent}
                    </span>
                  ))}
                </div>
              </article>
              <article className="output-card">
                <p className="section-label">Authority</p>
                <p className="studio-note">
                  The plan can execute automatically until a governance gate requires human approval.
                </p>
                <div className="artifact-list">
                  {["Requirements approval", "Architecture approval", "Security approval", "Release approval"].map((item) => (
                    <div className="artifact-row" key={item}>
                      <strong>{item}</strong>
                      <span>Controlled gate</span>
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </div>
        );
      case "Code":
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Implementation preview</p>
              <strong>Repository scaffold and governed changes</strong>
              <div className="code-block">
                <pre>{`apps/${suggestedTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "solution"}
  src/
  tests/
  docs/
  infra/`}</pre>
              </div>
            </article>
            <div className="dual-grid">
              <article className="output-card">
                <p className="section-label">Files</p>
                <div className="artifact-list">
                  {currentArtifacts.slice(0, 5).map((artifact) => (
                    <div className="artifact-row" key={artifact.id}>
                      <strong>{artifact.title}</strong>
                      <span>{artifact.stage}</span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="output-card">
                <p className="section-label">Generated output</p>
                <p className="studio-note">
                  Backend services, frontend surfaces, API contracts, and release assets are modelled as versioned artifacts.
                </p>
              </article>
            </div>
          </div>
        );
      case "Design":
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Suggested UX</p>
              <strong>Request composer, system output, approval rail, and evidence views</strong>
              <div className="chip-cloud">
                {solutionSurfaces.map((surface) => (
                  <span className="context-chip" key={surface}>
                    {surface}
                  </span>
                ))}
              </div>
            </article>
            <div className="dual-grid">
              <article className="output-card">
                <p className="section-label">Accessibility</p>
                <p className="studio-note">
                  Keyboard-first input, visible focus, live region updates, and colour-independent status markers are required.
                </p>
              </article>
              <article className="output-card">
                <p className="section-label">Responsive layouts</p>
                <p className="studio-note">
                  Desktop uses three columns, tablet collapses to a side sheet, and mobile becomes a single stream with a pinned composer.
                </p>
              </article>
            </div>
          </div>
        );
      case "Tests":
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Validation</p>
              <strong>Suites and coverage remain visible before delivery</strong>
              <div className="metric-grid compact">
                {[
                  ["Unit", "612 passed"],
                  ["Integration", "48 passed"],
                  ["UI", "24 passed"],
                  ["Security", "0 critical"],
                ].map(([label, value]) => (
                  <article className="metric-card" key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </article>
                ))}
              </div>
            </article>
            <article className="output-card">
              <p className="section-label">Evidence chain</p>
              <div className="artifact-list">
                {runtime.auditTrail.slice(0, 4).map((entry) => (
                  <div className="audit-row" key={entry.id}>
                    <span>{entry.at}</span>
                    <strong>{entry.action}</strong>
                    <p>{entry.service}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>
        );
      case "Security":
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Security findings</p>
              <strong>Threat model, dependency review, and approval gates remain enforced</strong>
              <div className="artifact-list">
                {runtime.riskRegister.slice(0, 3).map((risk) => (
                  <div className="artifact-row" key={risk.id}>
                    <strong>{risk.title}</strong>
                    <span>
                      {risk.likelihood} × {risk.impact} × {risk.exposure} = {risk.score}
                    </span>
                  </div>
                ))}
              </div>
            </article>
            <article className="output-card">
              <p className="section-label">Current approvals</p>
              <div className="artifact-list">
                {runtime.approvalRoutes.length ? (
                  runtime.approvalRoutes.slice(0, 4).map((route) => (
                    <div className="artifact-row" key={route.id}>
                      <strong>{route.subject}</strong>
                      <span>
                        {route.policyId} · {route.required.join(", ")}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="audit-row">
                    <strong>No approvals yet</strong>
                    <p>The workflow will request human approval at governance gates.</p>
                  </div>
                )}
              </div>
            </article>
          </div>
        );
      case "Architecture":
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Suggested architecture</p>
              <strong>Gateway, orchestrator, workflow engine, agents, storage, audit, deployment</strong>
              <div className="chip-cloud">
                {[
                  "NovaCodePro Gateway",
                  "Workflow Engine",
                  "Agent Orchestrator",
                  "Artifact Service",
                  "Audit Service",
                  "Deployment Service",
                ].map((item) => (
                  <span className="context-chip" key={item}>
                    {item}
                  </span>
                ))}
              </div>
            </article>
            <article className="output-card">
              <p className="section-label">Traceability</p>
              <p className="studio-note">
                Request, requirement, architecture, code, tests, release, deployment, and operations remain linked in the graph.
              </p>
            </article>
          </div>
        );
      case "Evidence":
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Evidence summary</p>
              <strong>Artifacts, approvals, and audit events are preserved for review</strong>
              <div className="artifact-list">
                {(runtime.evidenceBundles || []).slice(0, 4).map((bundle) => (
                  <div className="artifact-row" key={bundle.id}>
                    <strong>{bundle.summary}</strong>
                    <span>
                      {bundle.actor} · {bundle.policy}
                    </span>
                  </div>
                ))}
              </div>
            </article>
            <article className="output-card">
              <p className="section-label">Audit trail</p>
              <div className="artifact-list">
                {runtime.auditTrail.slice(0, 6).map((entry) => (
                  <div className="audit-row" key={entry.id}>
                    <span>{entry.at}</span>
                    <strong>{entry.action}</strong>
                    <p>{entry.subject}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>
        );
      case "Deployment":
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Deployment recommendation</p>
              <strong>{composerEnvironment} deployment path with gated promotion</strong>
              <div className="workflow-track compact">
                {["Development", "Test", "Pilot", "Staging", "Production"].map((stage, index) => (
                  <React.Fragment key={stage}>
                    <div className="workflow-step">
                      <span>{String(index + 1).padStart(2, "0")}</span>
                      <strong>{stage}</strong>
                    </div>
                    {index < 4 ? <div className="workflow-arrow">→</div> : null}
                  </React.Fragment>
                ))}
              </div>
            </article>
            <article className="output-card">
              <p className="section-label">Release readiness</p>
              <p className="studio-note">
                Build, test, sign, package, publish, deploy, and verify remain separate steps with their own evidence.
              </p>
            </article>
          </div>
        );
      case "Files":
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Attachments</p>
              <div className="artifact-list">
                {composerAttachments.length ? (
                  composerAttachments.map((attachment) => (
                    <div className="artifact-row" key={attachment.id}>
                      <strong>{attachment.name}</strong>
                      <span>
                        {attachment.source} · {attachment.security}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="audit-row">
                    <strong>No attachments yet</strong>
                    <p>Upload files, connect repositories, or attach design artefacts to enrich the request.</p>
                  </div>
                )}
              </div>
            </article>
            <article className="output-card">
              <p className="section-label">Solution artifacts</p>
              <div className="artifact-list">
                {currentArtifacts.map((artifact) => (
                  <div className="artifact-row" key={artifact.id}>
                    <strong>{artifact.title}</strong>
                    <span>{artifact.stage}</span>
                  </div>
                ))}
              </div>
            </article>
          </div>
        );
      case "Agent Activity":
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Active agents</p>
              <div className="chip-cloud">
                {composerAgents.map((agent) => (
                  <span className="context-chip active" key={agent}>
                    {agent}
                  </span>
                ))}
              </div>
            </article>
            <article className="output-card">
              <p className="section-label">Recent activity</p>
              <div className="artifact-list">
                {runtime.commandHistory.slice(0, 6).map((entry, index) => (
                  <div className="audit-row" key={`${entry}-${index}`}>
                    <strong>{entry}</strong>
                    <p>Command executed against the platform workspace.</p>
                  </div>
                ))}
              </div>
            </article>
          </div>
        );
      case "Overview":
      default:
        return (
          <div className="output-stack">
            <article className="output-card">
              <p className="section-label">Request summary</p>
              <strong>{activeRequest?.title || suggestedTitle}</strong>
              <p className="studio-note">{requestSummary}</p>
              <div className="chip-cloud">
                <span className="context-chip active">{selectedMode.label}</span>
                <span className="context-chip">{composerEnvironment}</span>
                <span className="context-chip">{workflowProgress}% complete</span>
                <span className="context-chip">{activeRequest?.status || "draft"}</span>
              </div>
            </article>
            <div className="dual-grid">
              <article className="output-card">
                <p className="section-label">Suggested solution</p>
                <div className="artifact-list">
                  {[
                    ["Scope", activeRequest?.domain || "Business solution"],
                    ["Region", activeRequest?.region || "Unspecified"],
                    ["Target", activeRequest?.surfaces?.join(", ") || "Workspace"],
                    ["Stage", activeStage?.label || "Intent Analysis"],
                    [
                      "Command center",
                      latestCommandSnapshot
                        ? `${latestCommandSnapshot.enterpriseHealth} / ${latestCommandSnapshot.trustScore} / ${latestCommandSnapshot.riskScore}`
                        : "Pending",
                    ],
                  ].map(([label, value]) => (
                    <div className="artifact-row" key={label}>
                      <strong>{label}</strong>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="output-card">
                <p className="section-label">Missing information</p>
                <p className="studio-note">
                  NovaCodePro will request clarification if any materially blocking detail is not supplied.
                </p>
                <div className="artifact-list">
                  {[
                    "User groups",
                    "Country and residency constraints",
                    "Deployment target",
                    "Approval authority",
                  ].map((item) => (
                    <div className="artifact-row" key={item}>
                      <strong>{item}</strong>
                      <span>Review if applicable</span>
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </div>
        );
    }
  }

  if (currentPathname === ROUTES.home) {
    return <PublicLandingPage session={session} onNavigate={(path) => navigateTo(path)} />;
  }
  if (publicAuthRoute && authStatus !== "signed-in") {
    return signedOutScreen;
  }
  if (bootstrapState === "loading") {
    return bootstrapLoadingScreen;
  }
  if (["API_UNAVAILABLE", "APPLICATION_ERROR", "WORKSPACE_REQUIRED", "TENANT_REQUIRED"].includes(bootstrapState)) {
    return bootstrapRecoveryScreen;
  }
  if (authStatus !== "signed-in") {
    return signedOutScreen;
  }
  if (currentPathname === ROUTES.dashboard) {
    return <DesignDashboard session={session} baseUrl={AUTH_API_BASE} onNavigate={(path) => navigateTo(path)} onLogout={handleLogout} />;
  }
  if (currentPathname === "/novacodepro/design/studio") {
    return <DesignStudioWorkspace session={session} baseUrl={AUTH_API_BASE} onNavigate={(path) => navigateTo(path)} />;
  }
  if (currentPathname === ROUTES.strategyRoot) {
    return (
      <Suspense fallback={<StudioSurfaceFallback />}>
        <LazyStrategyWorkspace
          session={session}
          pathname={currentPathname}
          navigate={(path, options) => navigateTo(path, options)}
          baseUrl={AUTH_API_BASE}
          onLogout={handleLogout}
        />
      </Suspense>
    );
  }
  if (["/novacodepro/design/research", "/novacodepro/design/personas", "/novacodepro/design/journeys", "/novacodepro/design/user-flows"].includes(currentPathname)) {
    const section = { research: "Research", personas: "Personas", journeys: "Journeys", "user-flows": "Flows" }[currentPathname.split("/").at(-1)];
    return <ExperienceMappingStudio session={session} baseUrl={AUTH_API_BASE} initialSection={section} onNavigate={(path) => navigateTo(path)} />;
  }
  if (["/novacodepro/design/components", "/novacodepro/design/design-system", "/novacodepro/design/brand-studio", "/novacodepro/design/templates"].includes(currentPathname)) {
    const section = { components: "Components", "design-system": "Design System", "brand-studio": "Brand Studio", templates: "Templates" }[currentPathname.split("/").at(-1)];
    return <DesignSystemStudio session={session} baseUrl={AUTH_API_BASE} initialSection={section} onNavigate={(path) => navigateTo(path)} />;
  }
  if (currentPathname === "/novacodepro/design/ai-designer") {
    return <AIDesignStudio session={session} baseUrl={AUTH_API_BASE} onNavigate={(path) => navigateTo(path)} />;
  }
  if (currentPathname === "/novacodepro/design/accessibility") {
    return <AccessibilityStudio session={session} baseUrl={AUTH_API_BASE} onNavigate={(path) => navigateTo(path)} />;
  }
  if (["/novacodepro/design/prototype", "/novacodepro/design/version-history"].includes(currentPathname)) {
    return <PrototypeCollaborationStudio session={session} baseUrl={AUTH_API_BASE} onNavigate={(path) => navigateTo(path)} />;
  }
  if (["/novacodepro/design/developer-handoff", "/novacodepro/design/reviews", "/novacodepro/design/approvals", "/novacodepro/design/export"].includes(currentPathname)) {
    const section = {"developer-handoff":"Developer Handoff",reviews:"Reviews",approvals:"Approvals",export:"Export"}[currentPathname.split("/").at(-1)];
    return <DeliveryGovernanceStudio session={session} baseUrl={AUTH_API_BASE} initialSection={section} onNavigate={(path)=>navigateTo(path)}/>;
  }
  if (isNovaCodeProRouteAccessible(currentPathname, session?.permissions || []) === false) {
    return forbiddenScreen;
  }
  if (parseNovaCodeProRoute(currentPathname)) {
    const parsedRoute = parseNovaCodeProRoute(currentPathname);
    const suspenseFallback = <StudioSurfaceFallback />;
    if (["workspace", "projects", "requests"].includes(parsedRoute.appId)) {
      return (
        <Suspense fallback={suspenseFallback}>
          <LazyNCP003Portal
            session={session}
            pathname={currentPathname}
            navigate={(path, options) => navigateTo(path, options)}
            baseUrl={AUTH_API_BASE}
            onLogout={handleLogout}
            onSessionChange={(result) => {
              const next = buildSessionFromAuthPayload(result, session?.active_role || loginRole, session?.email || loginEmail);
              setSession((current) => ({ ...(current || {}), ...next }));
              setBootstrapAttempt((value) => value + 1);
            }}
          />
        </Suspense>
      );
    }
    if (parsedRoute.appId === "product-factory") {
      return (
        <Suspense fallback={suspenseFallback}>
          <LazyProductFactoryPortal
            session={session}
            pathname={currentPathname}
            navigate={(path, options) => navigateTo(path, options)}
            baseUrl={AUTH_API_BASE}
            onLogout={handleLogout}
          />
        </Suspense>
      );
    }
    if (parsedRoute.appId === "strategy") {
      return (
        <Suspense fallback={suspenseFallback}>
          <LazyStrategyWorkspace
            session={session}
            pathname={currentPathname}
            navigate={(path, options) => navigateTo(path, options)}
            baseUrl={AUTH_API_BASE}
            onLogout={handleLogout}
          />
        </Suspense>
      );
    }
    if (parsedRoute.appId === "ai") {
      return (
        <Suspense fallback={suspenseFallback}>
          <LazyNCP004Portal
            session={session}
            pathname={currentPathname}
            navigate={(path, options) => navigateTo(path, options)}
            baseUrl={AUTH_API_BASE}
            onLogout={handleLogout}
          />
        </Suspense>
      );
    }
    if (["requirements", "knowledge"].includes(parsedRoute.appId)) {
      return (
        <Suspense fallback={suspenseFallback}>
          <LazyNCP005Portal
            session={session}
            pathname={currentPathname}
            navigate={(path, options) => navigateTo(path, options)}
            baseUrl={AUTH_API_BASE}
            onLogout={handleLogout}
          />
        </Suspense>
      );
    }
    if (parsedRoute.appId === "architecture") {
      return (
        <Suspense fallback={suspenseFallback}>
          <LazyNCP006APortal
            session={session}
            pathname={currentPathname}
            navigate={(path, options) => navigateTo(path, options)}
            baseUrl={AUTH_API_BASE}
            onLogout={handleLogout}
          />
        </Suspense>
      );
    }
    if (parsedRoute.appId === "design") {
      return (
        <Suspense fallback={suspenseFallback}>
          <LazyNCP006BPortal
            session={session}
            pathname={currentPathname}
            navigate={(path, options) => navigateTo(path, options)}
            baseUrl={AUTH_API_BASE}
            onLogout={handleLogout}
          />
        </Suspense>
      );
    }
    if (parsedRoute.appId === "development") {
      return (
        <Suspense fallback={suspenseFallback}>
          <LazyNCP007Portal
            session={session}
            pathname={currentPathname}
            navigate={(path, options) => navigateTo(path, options)}
            baseUrl={AUTH_API_BASE}
            onLogout={handleLogout}
          />
        </Suspense>
      );
    }
    if (parsedRoute.appId === "operations") {
      return (
        <Suspense fallback={suspenseFallback}>
          <LazyNCP008Portal
            session={session}
            pathname={currentPathname}
            navigate={(path, options) => navigateTo(path, options)}
            baseUrl={AUTH_API_BASE}
            onLogout={handleLogout}
          />
        </Suspense>
      );
    }
    return (
      <Suspense fallback={suspenseFallback}>
        <LazyNovaCodeProWorkspaceHub
          session={session}
          pathname={currentPathname}
          navigate={(path, options) => navigateTo(path, options)}
          baseUrl={AUTH_API_BASE}
          onLogout={handleLogout}
        />
      </Suspense>
    );
  }
  if (isSolutionRoute(currentPathname)) {
    return (
      <Suspense fallback={<StudioSurfaceFallback />}>
        <LazySolutionEngineeringPortal
          session={session}
          pathname={currentPathname}
          navigate={(path, options) => navigateTo(path, options)}
          baseUrl={AUTH_API_BASE}
          onLogout={handleLogout}
        />
      </Suspense>
    );
  }

  return (
    <div className="app-shell studio-shell">
      <header className="topbar">
        <div className="brand-block">
          <img className="brand-logo" src="/brand/NOVACODEPRO.webp" alt="NovaCodePro logo" />
          <div>
            <p className="eyebrow">NovaTech enterprise workspace</p>
            <strong>NovaCodePro</strong>
            <div className="topbar-context">
              <span>{activeRole.organization || session?.organization?.name || "NovaTech"}</span>
              <span>{activeTenant?.name || session?.workspace?.name || "Workspace"}</span>
              <span>{activeProject?.name || selectedRequest?.title || "Workspace"}</span>
              <span>{activeProject?.repository || "Repository not connected"}</span>
              <span>{activeProject?.branch || "main"}</span>
              <span>{environment}</span>
            </div>
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
          <button type="button" className="toolbar-chip" onClick={() => navigateTo(ROUTES.workspaceRoot)}>
            Workspace Hub
          </button>
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
          <div className="account-menu-wrap">
            <button
              type="button"
              className="account-chip"
              onClick={() => setAccountMenuOpen((value) => !value)}
            >
              {authDisplayName} ▼
            </button>
            {accountMenuOpen ? (
              <div className="account-menu" role="menu">
                {[
                  "My Profile",
                  "Switch Role",
                  "Security Settings",
                  "Active Sessions",
                  "Notifications",
                  "Help",
                ].map((item) => (
                  <button
                    key={item}
                    type="button"
                    className="account-menu-item"
                    onClick={() => {
                      if (item === "Switch Role") {
                        setShowRoleSwitcher((value) => !value);
                      }
                      setAccountMenuOpen(false);
                    }}
                  >
                    {item}
                  </button>
                ))}
                <button type="button" className="account-menu-item danger" onClick={handleLogout}>
                  Sign Out
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </header>

      <StudioChrome
        title="NovaCodePro Studio"
        subtitle={`${activeRole.label} · ${activeProject?.name || selectedRequest?.title || "Workspace"} · ${environment}`}
        menus={studioMenus}
        activityItems={studioActivityItems}
        contextItems={studioContextItems}
        statusItems={studioStatusItems}
        primaryAction={() => setFocusNav("Dashboard")}
        primaryActionLabel="Workspace overview"
      onOpenPalette={() => setPaletteOpen(true)}
      onActivityChange={(item) => setFocusNav(item.id)}
      activeActivityId={focusNav}
      >
      {focusNav === "Explorer" ? (
        <Suspense fallback={<StudioSurfaceFallback />}>
          <LazyStudioExplorer
            session={session}
            environment={environment}
            activeRole={activeRole}
            activeProject={activeProject}
            baseUrl={AUTH_API_BASE}
            navigate={(path, options) => navigateTo(path, options)}
            onOpenPalette={() => setPaletteOpen(true)}
            onFocusNav={(id) => setFocusNav(id)}
          />
        </Suspense>
      ) : (
        <>
      {sessionWarning ? (
        <div className="session-warning">
          <span>Your session will expire in 2 minutes.</span>
          <div className="session-warning-actions">
            <button type="button" className="secondary-action" onClick={handleStaySignedIn}>
              Stay Signed In
            </button>
            <button type="button" className="danger-action" onClick={handleLogout}>
              Sign Out
            </button>
          </div>
        </div>
      ) : null}

      <UniversalAIWorkspace
        model={aiWorkspaceModel}
        requestValue={composerPrompt}
        onRequestChange={setComposerPrompt}
        attachments={composerAttachments}
        onAttachmentUpload={handleAttachmentUpload}
        onRemoveAttachment={removeComposerAttachment}
        selectedMode={composerMode}
        onModeChange={setComposerMode}
        selectedAgents={composerAgents}
        onToggleAgent={toggleComposerAgent}
        selectedContextSources={composerContextSources}
        onToggleContextSource={toggleComposerContextSource}
        selectedProjectArtifact={selectedRequest?.artifacts?.[0]?.title || ""}
        selectedIncident={runtime.auditTrail[0]?.subject || ""}
        selectedRequirement={selectedRequest?.artifacts?.[0]?.title || ""}
        selectedToolContext={selectedOutputTab}
        onAction={{
          ask: () => setSelectedOutputTab("Overview"),
          plan: () => submitComposer("Plan only"),
          generate: () => submitComposer("Send and execute"),
          analyze: () => setSelectedOutputTab("Design"),
          review: () => setSelectedOutputTab("Evidence"),
          compare: () => setSelectedOutputTab("Files"),
          createWorkflow: () => platformRuntime.runCommand("Generate Workflow"),
          cancel: () => {
            setComposerPrompt("");
            setComposerAttachments([]);
            setSelectedOutputTab("Overview");
          },
          confirmInterpretation: () => setSelectedOutputTab("Overview"),
          correctInterpretation: () => setSelectedOutputTab("Plan"),
          addContext: () => setSelectedOutputTab("Files"),
          requestClarification: () => setSelectedOutputTab("Overview"),
          regeneratePlan: () => setSelectedOutputTab("Plan"),
          inspectAgentWork: (agent) => platformRuntime.runCommand(`Inspect ${agent?.name || "agent"}`),
          pauseAgent: (agent) => platformRuntime.runCommand(`Pause ${agent?.name || "agent"}`),
          cancelAgent: (agent) => platformRuntime.runCommand(`Cancel ${agent?.name || "agent"}`),
          retryAgent: (agent) => platformRuntime.runCommand(`Retry ${agent?.name || "agent"}`),
          reassignAgent: (agent) => platformRuntime.runCommand(`Reassign ${agent?.name || "agent"}`),
          requestAgentReview: (agent) => platformRuntime.runCommand(`Request review for ${agent?.name || "agent"}`),
          openAgentOutput: (agent) => platformRuntime.runCommand(`Open output for ${agent?.name || "agent"}`),
          openAgentEvidence: (agent) => platformRuntime.runCommand(`Open evidence for ${agent?.name || "agent"}`),
          openArtifact: (artifact) => platformRuntime.runCommand(`Open artifact ${artifact?.title || artifact?.id || ""}`),
          compareArtifact: (artifact) => platformRuntime.runCommand(`Compare artifact ${artifact?.title || artifact?.id || ""}`),
          reviewArtifact: (artifact) => platformRuntime.runCommand(`Review artifact ${artifact?.title || artifact?.id || ""}`),
          commentArtifact: (artifact) => platformRuntime.runCommand(`Comment on artifact ${artifact?.title || artifact?.id || ""}`),
          requestChangesArtifact: (artifact) => platformRuntime.runCommand(`Request changes for ${artifact?.title || artifact?.id || ""}`),
          approveArtifact: (artifact) => platformRuntime.runCommand(`Approve artifact ${artifact?.title || artifact?.id || ""}`),
          rejectArtifact: (artifact) => platformRuntime.runCommand(`Reject artifact ${artifact?.title || artifact?.id || ""}`),
          regenerateArtifact: (artifact) => platformRuntime.runCommand(`Regenerate artifact ${artifact?.title || artifact?.id || ""}`),
          exportArtifact: (artifact) => platformRuntime.runCommand(`Export artifact ${artifact?.title || artifact?.id || ""}`),
          openSpecializedTool: (artifact) => platformRuntime.runCommand(`Open specialized tool for ${artifact?.title || artifact?.id || ""}`),
          approveReview: () => platformRuntime.runCommand("Approve review"),
          rejectReview: () => platformRuntime.runCommand("Reject review"),
          requestReviewChanges: () => platformRuntime.runCommand("Request review changes"),
          editReview: () => platformRuntime.runCommand("Edit review"),
          askFollowUp: () => platformRuntime.runCommand("Ask follow-up"),
          sendToReviewer: () => platformRuntime.runCommand("Send to reviewer"),
          compareReviewVersion: () => platformRuntime.runCommand("Compare review version"),
          openEvidence: () => setSelectedOutputTab("Evidence"),
          approve: () => platformRuntime.runCommand("Approve"),
          reject: () => platformRuntime.runCommand("Reject"),
          requestChanges: () => platformRuntime.runCommand("Request changes"),
          delegate: () => platformRuntime.runCommand("Delegate"),
          openRelatedArtifact: () => platformRuntime.runCommand("Open related artifact"),
          openPolicy: () => platformRuntime.runCommand("Open policy"),
          pauseExecution: () => platformRuntime.runCommand("Pause execution"),
          resumeExecution: () => platformRuntime.runCommand("Resume execution"),
          cancelExecution: () => platformRuntime.runCommand("Cancel execution"),
          retryFailedStep: () => platformRuntime.runCommand("Retry failed step"),
          openLogs: () => platformRuntime.runCommand("Open logs"),
          openTraces: () => platformRuntime.runCommand("Open traces"),
          rollbackExecution: () => platformRuntime.runCommand("Rollback execution"),
          viewKnowledge: () => setSelectedOutputTab("Evidence"),
          publishKnowledge: () => platformRuntime.runCommand("Publish knowledge"),
          compareKnowledge: () => platformRuntime.runCommand("Compare knowledge"),
          supersedeKnowledge: () => platformRuntime.runCommand("Supersede knowledge"),
          linkKnowledgeToProject: () => platformRuntime.runCommand("Link knowledge to project"),
          createTemplate: () => platformRuntime.runCommand("Create template"),
        }}
        onChooseSuggestion={(suggestion) => setComposerPrompt(suggestion)}
        timelineFilters={{}}
        onTimelineFilterChange={() => {}}
      />

      <RoleWorkspaceWindows
        model={roleWorkspaceModel}
        activeSurfaceId={activeWorkspaceSurfaceId}
        onFocusSurface={focusWorkspaceSurface}
        onRunCommand={(command) => platformRuntime.runCommand(command)}
      />

      <div className="workspace-shell">
        <aside className="sidebar">
          <div className="sidebar-card identity-card">
            <p className="section-label">SIGNED IN</p>
            <strong>{authDisplayName}</strong>
            <span>{authDisplayRoleLabel}</span>
            <span>{session?.email || "djstrelly@gmail.com"}</span>
            <span>{session?.organization || "NovaTech"}</span>
            <div className="identity-meta">
              <span>Active role: {authDisplayRoleLabel}</span>
              <span>Session: Verified</span>
              <span>Environment: Production</span>
            </div>
          </div>

          <div className="sidebar-card frontend-runtime-card">
            <p className="section-label">Frontend platform</p>
            <strong>
              {frontendRuntimeConfig.environment} · {frontendRuntimeConfig.region}
            </strong>
            <span>
              Release {frontendRuntimeConfig.releaseVersion} · Commit {frontendRuntimeConfig.buildCommit}
            </span>
          <span>Source: {frontendRuntimeConfig.source}</span>
          <span>Products: {enabledFrontendProducts.join(", ")}</span>
          <div className="identity-meta">
            <span>API: {frontendRuntimeConfig.apiBaseUrl}</span>
            <span>Auth: {frontendRuntimeConfig.authBaseUrl}</span>
            <span>Rendering: {renderingSnapshot.productCount} product modules</span>
            <span>Interactions: {interactionSnapshot.interactionCount} governed actions</span>
          </div>
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
            {showRoleSwitcher ? (
              <div className="role-switcher-popover">
                {authAssignedRoleOptions.map((role) => (
                  <button
                    key={role.id}
                    type="button"
                    className="role-switch-item"
                    onClick={() => handleSwitchRole(role.id)}
                  >
                    {role.label}
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <div className="sidebar-card signout-card">
            <strong>{authDisplayName}</strong>
            <span>{authDisplayRoleLabel}</span>
            <button type="button" className="secondary-action" onClick={() => setShowRoleSwitcher(true)}>
              Switch Role
            </button>
            <button type="button" className="danger-action" onClick={handleLogout}>
              Sign Out
            </button>
          </div>
        </aside>

        <main className="content">
          <section className="hero-card request-console">
            <div className="console-main">
              <div className="console-intro">
                <p className="eyebrow">AI-native governed workspace</p>
                <h1>Universal AI Workspace</h1>
                <p className="hero-summary">
                  Ask NovaCodePro to reason over the current project, generate a plan, coordinate
                  agents, route approvals, execute governed work, verify outcomes, and capture evidence.
                </p>
                <div className="hero-badges">
                  <span className="badge">Organization: {activeRole.organization}</span>
                  <span className="badge">Environment: {environment}</span>
                  <span className="badge">Workspace: Universal AI</span>
                  <span className="badge">Tenant: {activeTenant.name}</span>
                  <span className="badge">Project: {activeProject.name}</span>
                  <span className="badge">Mode: {selectedMode.label}</span>
                  <span className="badge">Frontend: {frontendRuntimeConfig.environment}</span>
                </div>
              </div>

              <article className="output-card doctrine-card">
                <p className="section-label">AI doctrine</p>
                <strong>AI proposes. Policies constrain. Humans authorize. Systems execute.</strong>
                <p className="studio-note">
                  Evidence proves, operations verify, and governance supervises every protected action.
                </p>
              </article>

              {!composerPrompt.trim() ? (
                <article className="empty-console">
                  <strong>Start with a request</strong>
                  <p>
                    NovaCodePro will interpret the request, ask for the missing facts, propose a
                    plan, coordinate agents, and return a governed solution.
                  </p>
                  <div className="starter-grid">
                    {STARTER_REQUESTS.map((request) => (
                      <button
                        type="button"
                        key={request}
                        className="starter-card"
                        onClick={() => setComposerPrompt(request)}
                      >
                        {request}
                      </button>
                    ))}
                  </div>
                </article>
              ) : (
                <article className="output-card interpretation-card">
                  <p className="section-label">NovaCodePro interpretation</p>
                  <strong>{suggestedTitle}</strong>
                  <p className="studio-note">{requestSummary}</p>
                  <div className="chip-cloud">
                    <span className="context-chip active">{selectedMode.label}</span>
                    <span className="context-chip">{composerEnvironment}</span>
                    <span className="context-chip">{workflowProgress}% complete</span>
                    <span className="context-chip">{activeRequest?.status || "draft"}</span>
                  </div>
                </article>
              )}

              <div className="console-tabs" role="tablist" aria-label="Output views">
                {OUTPUT_TABS.map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    role="tab"
                    aria-selected={tab === activeOutputTab}
                    className={tab === activeOutputTab ? "workspace-tab active" : "workspace-tab"}
                    onClick={() => setSelectedOutputTab(tab)}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {renderOutputTabContent()}

              <form
                className="composer-panel"
                onSubmit={(event) => {
                  event.preventDefault();
                  submitComposer("Send and execute");
                }}
              >
                <label className="composer-field">
                  <span>Ask NovaCodePro to build, analyse, fix, test, secure, or deploy...</span>
                  <textarea
                    rows="5"
                    value={composerPrompt}
                    onChange={(event) => setComposerPrompt(event.target.value)}
                    placeholder="Build a modern customer-service portal with authentication, case management, analytics, and an AI support assistant."
                  />
                </label>

                <div className="composer-toolbar">
                  <input
                    ref={attachmentInputRef}
                    type="file"
                    hidden
                    multiple
                    onChange={handleAttachmentUpload}
                  />
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => attachmentInputRef.current?.click()}
                  >
                    Attach
                  </button>
                  <div className="segmented-control" role="group" aria-label="Execution mode">
                    {COMPOSER_MODES.map((mode) => (
                      <button
                        key={mode.id}
                        type="button"
                        className={mode.id === composerMode ? "segment active" : "segment"}
                        onClick={() => setComposerMode(mode.id)}
                        title={mode.description}
                      >
                        {mode.label}
                      </button>
                    ))}
                  </div>
                  <select
                    className="toolbar-select"
                    value={composerEnvironment}
                    onChange={(event) => setComposerEnvironment(event.target.value)}
                    aria-label="Target environment"
                  >
                    {["Local", "Development", "Test", "Internal QA", "Controlled Pilot", "Public Pilot", "Staging", "Production"].map(
                      (item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ),
                    )}
                  </select>
                </div>

                <div className="composer-toolbar wrap">
                  <div className="chip-cloud compact">
                    {COMPOSER_CONTEXT_SOURCES.map((source) => (
                      <button
                        type="button"
                        key={source}
                        className={
                          composerContextSources.includes(source)
                            ? "context-chip active"
                            : "context-chip"
                        }
                        onClick={() => toggleComposerContextSource(source)}
                      >
                        {source}
                      </button>
                    ))}
                  </div>
                  <div className="chip-cloud compact">
                    {COMPOSER_AGENTS.map((agent) => (
                      <button
                        type="button"
                        key={agent}
                        className={composerAgents.includes(agent) ? "context-chip active" : "context-chip"}
                        onClick={() => toggleComposerAgent(agent)}
                      >
                        {agent}
                      </button>
                    ))}
                  </div>
                </div>

                {composerAttachments.length ? (
                  <div className="attachment-strip">
                    {composerAttachments.map((attachment) => (
                      <span className="attachment-chip" key={attachment.id}>
                        {attachment.name}
                      </span>
                    ))}
                  </div>
                ) : null}

                <div className="composer-actions">
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => {
                      submitComposer("Plan only");
                    }}
                  >
                    Plan only
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => {
                      platformRuntime.runCommand("Save solution request as draft");
                    }}
                  >
                    Save draft
                  </button>
                  <button
                    type="submit"
                    className="primary-action"
                  >
                    Send and execute
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.runCommand("Create reusable workflow")}
                  >
                    Create workflow
                  </button>
                </div>
              </form>
            </div>

            <aside className="console-aside">
              <section className="console-card">
                <p className="section-label">Execution status</p>
                <strong>{activeRequest?.title || "New request"}</strong>
                <div className="metric-grid compact">
                  {[
                    ["Stage", activeStage?.label || "Intent Analysis"],
                    ["Status", activeRequest?.status || "draft"],
                    ["Artifacts", String(activeRequest?.artifacts?.length || 0)],
                    ["Approvals", String(activeRequest?.approvals?.length || 0)],
                  ].map(([label, value]) => (
                    <article className="metric-card" key={label}>
                      <span>{label}</span>
                      <strong>{value}</strong>
                    </article>
                  ))}
                </div>
              </section>

              <section className="console-card">
                <p className="section-label">Workflow monitor</p>
                <div className="workflow-rail compact">
                  {(activeRequest?.workflow || []).slice(0, 5).map((stage) => (
                    <button
                      key={stage.id}
                      type="button"
                      className={stage.id === activeStage?.id ? "workflow-node active" : "workflow-node"}
                      onClick={() => setSelectedOutputTab("Plan")}
                    >
                      <span>{stage.label}</span>
                      <strong>{stage.status}</strong>
                      <em>{stage.service}</em>
                    </button>
                  ))}
                </div>
              </section>

              <section className="console-card">
                <p className="section-label">Context</p>
                <div className="chip-cloud">
                  {composerContextSources.map((source) => (
                    <span className="context-chip active" key={source}>
                      {source}
                    </span>
                  ))}
                </div>
              </section>

              <section className="console-card">
                <p className="section-label">Attachments</p>
                <div className="artifact-list">
                  {composerAttachments.length ? (
                    composerAttachments.map((attachment) => (
                      <div className="artifact-row" key={attachment.id}>
                        <strong>{attachment.name}</strong>
                        <span>
                          {attachment.source} · {attachment.security}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="audit-row">
                      <strong>No attachments yet</strong>
                      <p>Upload files, connect a repository, or attach reference material.</p>
                    </div>
                  )}
                </div>
              </section>

              <section className="console-card">
                <p className="section-label">Approvals</p>
                <div className="artifact-list">
                  {activeRequest?.approvals?.length ? (
                    activeRequest.approvals.map((approval) => (
                      <div className="artifact-row" key={approval.id}>
                        <strong>{approval.gate}</strong>
                        <span>{approval.by}</span>
                      </div>
                    ))
                  ) : (
                    <div className="audit-row">
                      <strong>Human approval pending</strong>
                      <p>Architecture, security, compliance, and release gates stay explicit.</p>
                    </div>
                  )}
                </div>
              </section>
            </aside>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Solution journey</p>
                <h2>Business request to operating solution</h2>
              </div>
              <div className="layout-hint">
                <span>AI discovery first</span>
                <span>Human approval at sensitive gates</span>
              </div>
            </div>

            <div className="workflow-track" aria-label="End-to-end solution journey">
              {workflowJourneyStages.map((stage, index) => (
                <React.Fragment key={stage.id}>
                  <button
                    type="button"
                    className={
                      stage.id === selectedJourneyStage?.id ? "workflow-step active" : "workflow-step"
                    }
                    onClick={() => setSelectedJourneyStageId(stage.id)}
                  >
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <strong>{stage.label}</strong>
                    <em>{stage.output}</em>
                  </button>
                  {index < workflowJourneyStages.length - 1 ? <div className="workflow-arrow">→</div> : null}
                </React.Fragment>
              ))}
            </div>

            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Business request</p>
                <strong>{solutionBlueprint.title}</strong>
                <p className="studio-note">{solutionBlueprint.request}</p>
                <div className="field-grid">
                  <label className="field">
                    <span>Solution name</span>
                    <input value={solutionTitle} onChange={(event) => setSolutionTitle(event.target.value)} />
                  </label>
                  <label className="field">
                    <span>Industry</span>
                    <input value={solutionIndustry} onChange={(event) => setSolutionIndustry(event.target.value)} />
                  </label>
                </div>
                <div className="field-grid">
                  <label className="field">
                    <span>Country</span>
                    <input value={solutionCountry} onChange={(event) => setSolutionCountry(event.target.value)} />
                  </label>
                  <label className="field">
                    <span>Budget</span>
                    <input value={solutionBudget} onChange={(event) => setSolutionBudget(event.target.value)} />
                  </label>
                </div>
                <div className="field-grid">
                  <label className="field">
                    <span>Timeline</span>
                    <input value={solutionTimeline} onChange={(event) => setSolutionTimeline(event.target.value)} />
                  </label>
                  <label className="field">
                    <span>Stakeholders</span>
                    <input
                      value={solutionStakeholders}
                      onChange={(event) => setSolutionStakeholders(event.target.value)}
                    />
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
                      industry: solutionBlueprint.industry,
                      country: solutionBlueprint.country,
                      budget: solutionBlueprint.budget,
                      timeline: solutionBlueprint.timeline,
                      stakeholders: solutionBlueprint.stakeholders,
                      region: solutionBlueprint.region,
                      compliance: solutionBlueprint.compliance,
                      surfaces: solutionBlueprint.surfaces,
                      template: solutionBlueprint.template,
                    })
                  }
                >
                  Generate solution
                </button>
              </article>

              <article className="studio-card">
                <p className="section-label">AI discovery</p>
                <strong>Discovery interview</strong>
                <p className="studio-note">
                  NovaCodePro interviews the user before generating the requirements model.
                </p>
                <div className="artifact-list">
                  {DISCOVERY_PROMPTS.map((prompt) => (
                    <div className="audit-row" key={prompt}>
                      <strong>{prompt}</strong>
                    </div>
                  ))}
                </div>
                <div className="field-grid">
                  <label className="field">
                    <span>Users</span>
                    <textarea
                      rows="2"
                      value={discoveryAnswers.users}
                      onChange={(event) =>
                        setDiscoveryAnswers((current) => ({ ...current, users: event.target.value }))
                      }
                    />
                  </label>
                  <label className="field">
                    <span>Regions</span>
                    <textarea
                      rows="2"
                      value={discoveryAnswers.regions}
                      onChange={(event) =>
                        setDiscoveryAnswers((current) => ({ ...current, regions: event.target.value }))
                      }
                    />
                  </label>
                </div>
                <div className="field-grid">
                  <label className="field">
                    <span>Controls</span>
                    <textarea
                      rows="2"
                      value={discoveryAnswers.controls}
                      onChange={(event) =>
                        setDiscoveryAnswers((current) => ({ ...current, controls: event.target.value }))
                      }
                    />
                  </label>
                  <label className="field">
                    <span>Channels</span>
                    <textarea
                      rows="2"
                      value={discoveryAnswers.channels}
                      onChange={(event) =>
                        setDiscoveryAnswers((current) => ({ ...current, channels: event.target.value }))
                      }
                    />
                  </label>
                </div>
                <div className="field-grid">
                  <label className="field">
                    <span>Languages</span>
                    <textarea
                      rows="2"
                      value={discoveryAnswers.languages}
                      onChange={(event) =>
                        setDiscoveryAnswers((current) => ({ ...current, languages: event.target.value }))
                      }
                    />
                  </label>
                  <article className="metric-card">
                    <span>Understanding score</span>
                    <strong>
                      {Math.min(
                        100,
                        Object.values(discoveryAnswers).filter((value) => value.trim().length > 0).length * 20,
                      )}
                      %
                    </strong>
                  </article>
                </div>
                <button
                  type="button"
                  className="toolbar-chip"
                  onClick={() => platformRuntime.runCommand("Generate intent model")}
                >
                  Generate intent model
                </button>
              </article>

              <article className="studio-card">
                <p className="section-label">Workflow Monitor</p>
                <strong>{selectedJourneyStage?.label || "Workflow stage"}</strong>
                <p className="studio-note">
                  {selectedJourneyStage?.service || "Workflow service"} · {selectedJourneyStage?.ui || "Workspace"} ·{" "}
                  {selectedJourneyStage?.output || "Output"}
                </p>
                <dl className="service-meta">
                  <div>
                    <dt>API</dt>
                    <dd>{selectedJourneyStage?.api || "n/a"}</dd>
                  </div>
                  <div>
                    <dt>Storage</dt>
                    <dd>{selectedJourneyStage?.storage || "n/a"}</dd>
                  </div>
                  <div>
                    <dt>Audit</dt>
                    <dd>{selectedJourneyStage?.audit || "n/a"}</dd>
                  </div>
                  <div>
                    <dt>Kind</dt>
                    <dd>{selectedJourneyStage?.kind || "automation"}</dd>
                  </div>
                </dl>
                <div className="studio-actions">
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.advanceWorkflow(selectedRequest.id)}
                  >
                    Advance
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.approveGate(selectedRequest.id, "Approved in workflow monitor.")}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.pauseWorkflow(selectedRequest.id)}
                  >
                    Pause
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.resumeWorkflow(selectedRequest.id)}
                  >
                    Resume
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.retryWorkflow(selectedRequest.id)}
                  >
                    Retry
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.rejectWorkflow(selectedRequest.id)}
                  >
                    Reject
                  </button>
                </div>
              </article>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Operational Readiness Program</p>
                <h2>Live evidence and governance control production operation</h2>
              </div>
              <div className="layout-hint">
                <span>{operationalReadinessSummary.assessment.status}</span>
                <span>Payments {operationalReadinessSummary.assessment.realPaymentsEnabled ? "enabled" : "blocked"}</span>
              </div>
            </div>
            <div className="center-grid">
              {[
                ["Maturity layers", operationalReadinessSummary.program.maturityLayers.length, "Architecture, implementation, verification, approval, and production operation."],
                ["Studios", operationalReadinessSummary.program.studios.length, "EDOS studios own APIs, stores, events, evidence, governance, dashboards, and audit."],
                ["Payment providers", operationalReadinessSummary.program.paymentActivation.providers.length, "Provider connectors remain isolated from product deployment."],
                ["Telemetry stages", operationalReadinessSummary.program.telemetryPipeline.length, "Application telemetry feeds analytics, evidence, knowledge graph, and digital twin."],
              ].map(([label, value, note]) => (
                <article className="center-card" key={label}>
                  <p className="section-label">{label}</p>
                  <strong>{value}</strong>
                  <p>{note}</p>
                </article>
              ))}
            </div>
            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Readiness matrix</p>
                <strong>Repository credit without production claims</strong>
                <div className="artifact-list">
                  {operationalReadinessSummary.program.readinessMatrix.slice(0, 8).map((row) => (
                    <div className="artifact-row" key={row.capability}>
                      <strong>{row.capability}</strong>
                      <span>
                        Repository {row.repository ? "complete" : "open"} · Operational {row.operational ? "verified" : "pending"} · Governance {row.governance}
                      </span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">Payment activation</p>
                <strong>Sandbox and provider evidence before production payments</strong>
                <div className="compact-list">
                  {operationalReadinessSummary.program.paymentActivation.interface.map((operation) => (
                    <span className="compact-pill" key={operation}>
                      {operation}
                    </span>
                  ))}
                </div>
                <p className="studio-note">
                  GA allowed: {operationalReadinessSummary.assessment.gaAllowed ? "true" : "false"} · Real payments:
                  {" "}{operationalReadinessSummary.assessment.realPaymentsEnabled ? "true" : "false"}
                </p>
              </article>
              <article className="studio-card">
                <p className="section-label">Actions</p>
                <strong>Evaluate evidence-gated operation</strong>
                <div className="studio-actions">
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.evaluateOperationalReadiness({})}
                  >
                    Blocked state
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() =>
                      platformRuntime.evaluateOperationalReadiness({
                        evidence: {
                          designSync: "PASS",
                          visualRegression: "PASS",
                          accessibility: "PASS",
                          openTelemetry: "PASS",
                          analytics: "PASS",
                          digitalUxTwin: "PASS",
                          automatedPrr: "PASS",
                        },
                        approvals: {
                          ux: "APPROVED",
                          engineering: "APPROVED",
                          security: "APPROVED",
                          operations: "APPROVED",
                          compliance: "APPROVED",
                          prr: "APPROVED",
                          executive: "APPROVED",
                        },
                      })
                    }
                  >
                    GA only
                  </button>
                </div>
              </article>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Enterprise Completion Standard</p>
                <h2>Repository, operational, and governance status stay separate</h2>
              </div>
              <div className="layout-hint">
                <span>{completionSummary.assessment.level}</span>
                <span>GA {completionSummary.assessment.gaAllowed ? "allowed" : "blocked"}</span>
              </div>
            </div>
            <div className="center-grid">
              {[
                ["Repository", completionSummary.assessment.repositoryComplete ? "Complete" : "Open", "Code, tests, APIs, UI, SDK, automation, documentation, and evidence models."],
                ["Operational", completionSummary.assessment.operationalVerified ? "Verified" : "Pending", "Live telemetry, visual regression, accessibility, experiments, alerts, traces, and runtime evidence."],
                ["Governance", completionSummary.assessment.governanceApproved ? "Approved" : "Pending", "UX, engineering, security, operations, compliance, product, and executive approvals."],
                ["Production", completionSummary.assessment.productionReady ? "Ready" : "Blocked", "Production readiness requires every operational gate before GA can be considered."],
                ["GA", completionSummary.assessment.gaAllowed ? "Allowed" : "Blocked", "General Availability requires production readiness and executive authorization."],
                ["Real payments", completionSummary.assessment.realPaymentsEnabled ? "Enabled" : "Blocked", "Payment activation stays outside UXOS and requires financial authority."],
              ].map(([label, value, note]) => (
                <article className="center-card" key={label}>
                  <p className="section-label">{label}</p>
                  <strong>{value}</strong>
                  <p>{note}</p>
                </article>
              ))}
            </div>
            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Completion dashboard</p>
                <strong>Dimensional status by domain</strong>
                <div className="artifact-list">
                  {completionSummary.dashboard.rows.slice(0, 8).map((row) => (
                    <div className="artifact-row" key={row.domain}>
                      <strong>{row.domain}</strong>
                      <span>
                        Repository {row.repository ? "complete" : "open"} · Operational {row.operational ? "verified" : "pending"} · Governance {row.governance}
                      </span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">Production gates</p>
                <strong>{completionSummary.assessment.missingProductionGates.length} gates pending</strong>
                <div className="compact-list">
                  {completionSummary.assessment.missingProductionGates.slice(0, 9).map((gate) => (
                    <span className="compact-pill" key={gate}>
                      {gate}
                    </span>
                  ))}
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">Actions</p>
                <strong>Evaluate without conflating completion states</strong>
                <div className="studio-actions">
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() =>
                      platformRuntime.evaluateCompletionState({
                        repositoryComplete: true,
                        operationalVerified: false,
                        governanceApproved: false,
                      })
                    }
                  >
                    Repository complete
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() =>
                      platformRuntime.evaluateCompletionState({
                        repositoryComplete: true,
                        operationalVerified: true,
                        governanceApproved: true,
                        productionReadyGates: Object.fromEntries(
                          COMPLETION_STANDARD.productionReadyGates.map((gate) => [gate, true]),
                        ),
                        executiveAuthorized: false,
                      })
                    }
                  >
                    Production ready
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() =>
                      platformRuntime.evaluateCompletionState({
                        repositoryComplete: true,
                        operationalVerified: true,
                        governanceApproved: true,
                        productionReadyGates: Object.fromEntries(
                          COMPLETION_STANDARD.productionReadyGates.map((gate) => [gate, true]),
                        ),
                        executiveAuthorized: true,
                      })
                    }
                  >
                    Executive GA
                  </button>
                </div>
                <p className="studio-note">
                  These controls model approval state only. They do not enable real payments or bypass designated human authorities.
                </p>
              </article>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">29-window enterprise maturity model</p>
                <h2>One governed platform across identity, execution, governance, and command</h2>
              </div>
              <div className="layout-hint">
                <span>Window 16 is human review</span>
                <span>Window 26 is approval routing and policy orchestration</span>
              </div>
            </div>

            <div className="maturity-grid">
              {ENTERPRISE_WINDOWS.map((window) => (
                <article className="maturity-card" key={window.id}>
                  <p className="section-label">{window.label}</p>
                  <strong>{window.title}</strong>
                  <span>{window.phase}</span>
                  <p>{window.summary}</p>
                  <div className="chip-cloud compact">
                    <span className="context-chip">{window.service}</span>
                    <span className="context-chip">Evidence producing</span>
                  </div>
                </article>
              ))}
            </div>
          </section>

          {LEADERSHIP_ROLE_IDS.has(activeRole.id) ? (
            <section className="surface-band">
              <div className="band-header">
                <div>
                  <p className="section-label">Governance model</p>
                  <h2>Strategy, governance, risk, and enterprise performance</h2>
                </div>
                <div className="layout-hint">
                  <span>Board oversees strategy</span>
                  <span>Executives manage performance</span>
                </div>
              </div>

              <div className="studio-grid">
                <article className="studio-card">
                  <p className="section-label">Responsibilities</p>
                  <strong>{activeRole.label}</strong>
                  <p className="studio-note">
                    The current workspace is intentionally read-mostly for governance and leadership decision making.
                  </p>
                  <div className="artifact-list">
                    {activeRole.actions.map((action) => (
                      <div className="artifact-row" key={action}>
                        <strong>{action}</strong>
                        <span>Leadership action</span>
                      </div>
                    ))}
                  </div>
                </article>

                <article className="studio-card">
                  <p className="section-label">Governance matrix</p>
                  <strong>Board, executive, and operational decision boundaries</strong>
                  <div className="artifact-list">
                    {GOVERNANCE_MATRIX.map(([decision, board, ceo, cto, ciso, platformAdmin]) => (
                      <div className="audit-row" key={decision}>
                        <strong>{decision}</strong>
                        <p>
                          Board: {board} · CEO: {ceo} · CTO: {cto} · CISO: {ciso} · Platform Admin: {platformAdmin}
                        </p>
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            </section>
          ) : null}

          {activeRole.id === "platform-admin" ? (
            <section className="surface-band">
              <div className="band-header">
                <div>
                  <p className="section-label">Platform administration center</p>
                  <h2>Health, governance, security, and lifecycle controls</h2>
                </div>
                <div className="layout-hint">
                  <span>{localAdminSummary.platform_health === "healthy" ? "Platform healthy" : "Platform attention required"}</span>
                  <span>{platformSummary ? "Backend summary" : "Local fallback summary"}</span>
                </div>
              </div>

              <div className="metric-grid">
                {[
                  ["Platform health", localAdminSummary.platform_health],
                  ["Services", String(localAdminSummary.service_count)],
                  ["Tenants", String(localAdminSummary.tenant_count)],
                  ["Workflows", String(localAdminSummary.workflow_count)],
                  ["Approvals", String(localAdminSummary.approval_count)],
                  ["Marketplace", String(localAdminSummary.marketplace_count)],
                ].map(([label, value]) => (
                  <article className="metric-card" key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </article>
                ))}
              </div>

              <div className="service-grid compact">
                {PLATFORM_ADMIN_SECTIONS.map((section) => (
                  <article className="service-card" key={section.title}>
                    <p className="section-label">Platform admin</p>
                    <strong>{section.title}</strong>
                    <p>{section.summary}</p>
                    <div className="chip-cloud">
                      {section.bullets.map((bullet) => (
                        <span className="context-chip" key={bullet}>
                          {bullet}
                        </span>
                      ))}
                    </div>
                    <button
                      type="button"
                      className="toolbar-chip"
                      onClick={() => runtime.runCommand(section.command)}
                    >
                      {section.command}
                    </button>
                  </article>
                ))}
              </div>

              <div className="studio-grid">
                <article className="studio-card">
                  <p className="section-label">Service registry</p>
                  <strong>Core platform services</strong>
                  <p className="studio-note">
                    Backend summary from the NovaCodePro platform service, with a local fallback when the API is not reachable.
                  </p>
                  <div className="artifact-list">
                    {localAdminSummary.service_registry.map((service) => (
                      <div className="artifact-row" key={service.name}>
                        <strong>{service.name}</strong>
                        <span>{service.category}</span>
                        <span className="status-pill">{service.status}</span>
                      </div>
                    ))}
                  </div>
                </article>

                <article className="studio-card">
                  <p className="section-label">Governance queue</p>
                  <strong>Protected operational actions</strong>
                  <p className="studio-note">
                    Platform administrators oversee approvals, release readiness, policy controls, and emergency operations.
                  </p>
                  <div className="artifact-list">
                    {(platformSummary?.governance_queue || [
                      "Security review",
                      "Compliance review",
                      "Release approval",
                      "Policy review",
                    ]).map((item) => (
                      <div className="artifact-row" key={item}>
                        <strong>{item}</strong>
                        <span>Governed</span>
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            </section>
          ) : null}

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
          {toArray(selectedRequest?.workflow).map((stage) => (
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
          {toArray(selectedRequest?.artifacts).map((artifact) => (
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
                <p className="section-label">Enterprise knowledge graph</p>
                <h2>Traceability, impact analysis, and institutional memory across the lifecycle</h2>
              </div>
              <div className="layout-hint">
                <span>Window 11 service surface</span>
                <span>Shared evidence and graph mutations are auditable</span>
              </div>
            </div>
            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Graph service</p>
                <strong>{activeKnowledgeNode.label}</strong>
                <p className="studio-note">
                  Nodes remain traceable from the business request through deployment and audit evidence.
                </p>
                <div className="field-grid">
                  <label className="field">
                    <span>Search graph</span>
                    <input
                      value={knowledgeQuery}
                      onChange={(event) => setKnowledgeQuery(event.target.value)}
                      placeholder="Search requirements, release, audit..."
                    />
                  </label>
                  <label className="field">
                    <span>Trace to</span>
                    <select
                      value={knowledgeTraceTargetId}
                      onChange={(event) => setKnowledgeTraceTargetId(event.target.value)}
                    >
                      {runtime.knowledgeGraph.map((node) => (
                        <option key={node.id} value={node.id}>
                          {node.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="studio-actions">
                  <button type="button" className="toolbar-chip" onClick={runKnowledgeQuery}>
                    Run query
                  </button>
                  <button type="button" className="toolbar-chip" onClick={refreshKnowledgeTrace}>
                    Trace path
                  </button>
                </div>
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
                <div className="artifact-list">
                  <div className="artifact-row">
                    <strong>Owner</strong>
                    <span>{activeKnowledgeNode.owner || "Unassigned"}</span>
                  </div>
                  <div className="artifact-row">
                    <strong>Domain</strong>
                    <span>{activeKnowledgeNode.domain || "Lifecycle"}</span>
                  </div>
                  <div className="artifact-row">
                    <strong>Evidence</strong>
                    <span>{activeKnowledgeNode.evidence || "Linked evidence"}</span>
                  </div>
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">Search results</p>
                <strong>{knowledgeSearchResults.length} matches</strong>
                <div className="artifact-list">
                  {knowledgeSearchResults.slice(0, 6).map((node) => (
                    <button
                      type="button"
                      className={node.id === activeKnowledgeNode.id ? "artifact-row active" : "artifact-row"}
                      key={node.id}
                      onClick={() => runtime.focusKnowledgeNode(node.id)}
                    >
                      <strong>{node.label}</strong>
                      <span>
                        {node.type} · {node.links.length} links
                      </span>
                    </button>
                  ))}
                </div>
                <div className="articledivider" />
                <p className="section-label">Trace path</p>
                <div className="chip-cloud compact">
                  {knowledgeTracePath.map((nodeId) => {
                    const node = runtime.knowledgeGraph.find((item) => item.id === nodeId);
                    return (
                      <span className="context-chip active" key={nodeId}>
                        {node?.label || nodeId}
                      </span>
                    );
                  })}
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
                {activeAutomationTemplate.outcome ? <div className="automation-outcome"><span>Target outcome</span><strong>{activeAutomationTemplate.outcome}</strong></div> : null}
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
            {activeAutomationTemplate.phases?.length ? (
              <div className="mobile-lifecycle" aria-label={`${activeAutomationTemplate.title} lifecycle`}>
                {activeAutomationTemplate.phases.map((phase, index) => (
                  <article className="lifecycle-phase" key={phase.id}>
                    <div className="lifecycle-phase-header"><span>{String(index + 1).padStart(2, "0")}</span><div><p>{phase.owner}</p><h3>{phase.title}</h3></div></div>
                    <ul>{phase.tasks.map((task) => <li key={task}>{task}</li>)}</ul>
                    <div className="lifecycle-deliverables">{phase.deliverables.map((deliverable) => <span key={deliverable}>{deliverable}</span>)}</div>
                    <footer><span>Approval gate</span><strong>{phase.gate}</strong></footer>
                  </article>
                ))}
              </div>
            ) : null}
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Shared platform services</p>
                <h2>Every window depends on the same identity, workflow, policy, evidence, and graph services</h2>
              </div>
            </div>
            <div className="service-grid">
              {[
                ["Identity Service", "Authentication, sessions, trust, and verified actors."],
                ["Authorization Service", "RBAC, ABAC, and policy-aware access decisions."],
                ["Tenant Service", "Tenant isolation, quotas, residency, and entitlements."],
                ["Workspace Service", "Role-aware shells, layouts, memory, and collaboration."],
                ["Conversation Service", "Requests, streaming output, comments, and branches."],
                ["Agent Runtime", "Typed agent executions, budgets, tools, and checkpoints."],
                ["Workflow Engine", "Long-running orchestration, replays, compensations, and state."],
                ["Policy Engine", "Routing, quorum, separation of duties, and governance constraints."],
                ["Approval Engine", "Human authorizations, conditions, expiry, and evidence."],
                ["Knowledge Graph", "Traceability, impact analysis, and institutional memory."],
                ["Evidence Service", "Immutable proof bundles across tests, releases, and operations."],
                ["Audit Ledger", "Append-only event history with actor, action, and service provenance."],
                ["Risk Engine", "Risk scoring, treatment plans, and enterprise monitoring."],
                ["Notification Service", "Approvals, incidents, tasks, and release alerts."],
                ["Search Service", "Semantic discovery across projects, artifacts, and evidence."],
                ["Artifact Registry", "Versioned storage for documents, code, builds, and releases."],
                ["Integration Hub", "Connectors to external systems and enterprise tools."],
                ["Observability Platform", "Metrics, logs, traces, alerts, and service health."],
                ["Digital Twin Engine", "Live system model, scenario simulation, and blast radius."],
                ["Billing Service", "Usage metering, entitlements, and subscription governance."],
              ].map(([title, summary]) => (
                <article className="service-card" key={title}>
                  <p className="section-label">Core service</p>
                  <strong>{title}</strong>
                  <p>{summary}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Shared interaction model</p>
                <h2>Identity, graph, policy, risk, approvals, evidence, twin, executive, command</h2>
              </div>
              <div className="layout-hint">
                <span>One flow across 29 windows</span>
                <span>Atomic service updates and audit trails</span>
              </div>
            </div>
            <div className="service-grid">
              <article className="service-card">
                <p className="section-label">Enterprise Knowledge Graph Service</p>
                <strong>Search and trace relationships</strong>
                <p>Locate ownership, dependencies, and impact paths before execution.</p>
                <div className="studio-actions">
                  <button type="button" className="toolbar-chip" onClick={runKnowledgeQuery}>
                    Run query
                  </button>
                  <button type="button" className="toolbar-chip" onClick={refreshKnowledgeTrace}>
                    Trace path
                  </button>
                </div>
              </article>
              <article className="service-card">
                <p className="section-label">Enterprise Evidence Engine</p>
                <strong>Bundle and verify proof</strong>
                <p>Every significant action emits immutable evidence and audit metadata.</p>
                <button type="button" className="toolbar-chip" onClick={runSharedInteraction}>
                  Generate evidence
                </button>
              </article>
              <article className="service-card">
                <p className="section-label">Enterprise Risk Engine</p>
                <strong>Score impact before action</strong>
                <p>Likelihood, impact, and exposure are scored before protected work continues.</p>
                <button type="button" className="toolbar-chip" onClick={runSharedInteraction}>
                  Evaluate risk
                </button>
              </article>
              <article className="service-card">
                <p className="section-label">Approval engine</p>
                <strong>Route to the right approvers</strong>
                <p>Policy, quorum, timeout, and escalation stay under governance control.</p>
                <button type="button" className="toolbar-chip" onClick={runSharedInteraction}>
                  Route approval
                </button>
              </article>
              <article className="service-card">
                <p className="section-label">Enterprise Digital Twin</p>
                <strong>Simulate operational impact</strong>
                <p>Forecast service, revenue, and customer impact before rollout or recovery.</p>
                <button type="button" className="toolbar-chip" onClick={runSharedInteraction}>
                  Simulate twin
                </button>
              </article>
              <article className="service-card">
                <p className="section-label">Executive AI Services</p>
                <strong>Explain threats and options</strong>
                <p>Strategy, operations, and finance consume the same governed evidence layer.</p>
                <button type="button" className="toolbar-chip" onClick={runSharedInteraction}>
                  Ask executive AI
                </button>
              </article>
              <article className="service-card">
                <p className="section-label">Command center</p>
                <strong>Refresh mission control</strong>
                <p>Situational awareness is recalculated from shared enterprise services.</p>
                <button type="button" className="toolbar-chip" onClick={runSharedInteraction}>
                  Refresh command center
                </button>
              </article>
            </div>
            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Latest evidence</p>
                <strong>{latestEvidenceBundle?.summary || "No evidence yet"}</strong>
                <p className="studio-note">
                  {latestEvidenceBundle ? `${latestEvidenceBundle.actor} · ${latestEvidenceBundle.policy}` : "Generate a bundle from the shared interaction model."}
                </p>
              </article>
              <article className="studio-card">
                <p className="section-label">Latest risk and route</p>
                <strong>{latestRiskItem?.title || "No risk evaluated"}</strong>
                <p className="studio-note">
                  {latestRiskItem
                    ? `${latestRiskItem.likelihood} × ${latestRiskItem.impact} × ${latestRiskItem.exposure} = ${latestRiskItem.score}`
                    : "Run the risk engine to create a scored item."}
                </p>
                <div className="chip-cloud compact">
                  <span className="context-chip">
                    {latestApprovalRoute?.policyId || "No approval route"}
                  </span>
                  <span className="context-chip">
                    {latestApprovalRoute?.required?.join(", ") || "No approvers"}
                  </span>
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">Twin, executive, command</p>
                <strong>{latestTwinScenario?.title || "No twin scenario"}</strong>
                <p className="studio-note">
                  {latestExecutiveInsight?.question || "Ask an executive question to generate a briefing."}
                </p>
                <div className="artifact-list">
                  <div className="artifact-row">
                    <strong>Enterprise health</strong>
                    <span>{latestCommandSnapshot?.enterpriseHealth || "n/a"}</span>
                  </div>
                  <div className="artifact-row">
                    <strong>Trust score</strong>
                    <span>{latestCommandSnapshot?.trustScore || "n/a"}</span>
                  </div>
                  <div className="artifact-row">
                    <strong>Risk score</strong>
                    <span>{latestCommandSnapshot?.riskScore || "n/a"}</span>
                  </div>
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
                <p className="section-label">Distributed platform</p>
                <h2>Backend services carry the state, workflows, evidence, and operations</h2>
              </div>
              <div className="layout-hint">
                <span>Persistent storage</span>
                <span>Auditable transitions</span>
              </div>
            </div>
            <div className="service-grid compact">
              {DISTRIBUTED_SERVICES.map(([service, detail]) => (
                <article className="service-card" key={service}>
                  <p className="section-label">Service</p>
                  <strong>{service}</strong>
                  <p>{detail}</p>
                </article>
              ))}
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

          <section className="workspace-band universal-tool-band">
            <div className="tool-header">
              <div className="tool-header-main">
                <p className="section-label">Tool Header</p>
                <strong>{selectedWindow.title}</strong>
                <span>{activeProject.name}</span>
              </div>
              <div className="tool-header-meta">
                <span>Name: {selectedWindow.title}</span>
                <span>Project: {activeProject.name}</span>
                <span>Workspace: {activeRole.label}</span>
                <span>Environment: {environment}</span>
                <span>AI: Enabled</span>
                <span>Status: {selectedWindow.status}</span>
                <span>User: {authDisplayName}</span>
              </div>
            </div>

            <div className="tool-tabs" role="tablist" aria-label="Tool views">
              {[
                ["main", "Main Workspace"],
                ["ai", "AI Assistant"],
                ["collaboration", "Collaboration"],
                ["activity", "Activity"],
              ].map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={toolView === id}
                  className={toolView === id ? "tool-tab active" : "tool-tab"}
                  onClick={() => setToolView(id)}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="tool-workspace-grid">
              <article className="tool-main-pane">
                <div className="tool-pane-head">
                  <div>
                    <p className="section-label">Main Workspace</p>
                    <h3>{selectedWindow.title}</h3>
                  </div>
                  <span className="status-pill">{selectedWindow.status}</span>
                </div>
                <div className="tool-pane-body">
                  <p>{selectedWindow.summary}</p>
                  <div className="bullet-grid">
                    {selectedWindow.bullets.map((bullet) => (
                      <span className="bullet" key={bullet}>
                        {bullet}
                      </span>
                    ))}
                  </div>
                </div>
                {toolView === "ai" ? (
                  <div className="tool-pane-panel">
                    <p className="section-label">AI Assistant</p>
                    <p className="studio-note">
                      NovaAI can reason over context, generate plans, summarize history, and propose governed actions.
                    </p>
                    <div className="chip-cloud">
                      {["Analyze", "Explain", "Generate", "Refactor", "Review", "Automate"].map((item) => (
                        <button
                          key={item}
                          type="button"
                          className="context-chip"
                          onClick={() => setSmartCommand(item)}
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                    <div className="tool-output-grid">
                      <article className="tool-mini-card">
                        <strong>Long-term memory</strong>
                        <span>Projects, decisions, preferences, and approvals persist across sessions.</span>
                      </article>
                      <article className="tool-mini-card">
                        <strong>Research mode</strong>
                        <span>Sources, comparison, risks, and recommendations are attached to the reply.</span>
                      </article>
                    </div>
                  </div>
                ) : null}
                {toolView === "collaboration" ? (
                  <div className="tool-pane-panel">
                    <p className="section-label">Collaboration</p>
                    <div className="tool-output-grid">
                      <article className="tool-mini-card">
                        <strong>Comments</strong>
                        <span>Shared review threads with mentions, approvals, and task handoff.</span>
                      </article>
                      <article className="tool-mini-card">
                        <strong>Multi-agent teams</strong>
                        <span>Architect, developer, QA, security, legal, compliance, and risk agents can coordinate.</span>
                      </article>
                    </div>
                  </div>
                ) : null}
                {toolView === "activity" ? (
                  <div className="tool-pane-panel">
                    <p className="section-label">Activity</p>
                    <div className="tool-output-grid">
                      {selectedWindow.bullets.slice(0, 3).map((item) => (
                        <article className="tool-mini-card" key={item}>
                          <strong>{item}</strong>
                          <span>Recent tool activity and context are available for review.</span>
                        </article>
                      ))}
                    </div>
                  </div>
                ) : null}
                <div className="tool-pane-panel">
                  <p className="section-label">Enterprise foundation</p>
                  <div className="tool-output-grid">
                    <article className="tool-mini-card">
                      <strong>NEAF</strong>
                      <span>
                        {runtime.enterpriseArchitectureFramework.models.neaf.sequence.length} enterprise planes align
                        governance, intelligence, execution, products, and infrastructure.
                      </span>
                    </article>
                    <article className="tool-mini-card">
                      <strong>NERA</strong>
                      <span>
                        {runtime.neraArchitecture.layers.length} stable architecture layers with governance, platform,
                        knowledge, products, operations, services, and infrastructure separated.
                      </span>
                    </article>
                    <article className="tool-mini-card">
                      <strong>Framework views</strong>
                      <span>
                        {Object.keys(runtime.enterpriseArchitectureFramework.models).length} coordinated views across
                        reference architecture, capability, operating, data, knowledge, AI, and twin models.
                      </span>
                    </article>
                    <article className="tool-mini-card">
                      <strong>EROS</strong>
                      <span>
                        {runtime.erosManifest.coreViews.length} governed twin views, authority levels, recovery
                        services, and an optimize loop for enterprise resilience.
                      </span>
                    </article>
                    <article className="tool-mini-card">
                      <strong>Knowledge graph</strong>
                      <span>
                        {runtime.knowledgeGraph.length} approved nodes and trace paths across requests, approvals,
                        deployments, and evidence.
                      </span>
                    </article>
                    <article className="tool-mini-card">
                      <strong>Approval objects</strong>
                      <span>
                        {runtime.approvalObjects.length} governed review objects with status, risk, and execution
                        readiness.
                      </span>
                    </article>
                    <article className="tool-mini-card">
                      <strong>Multi-agent teams</strong>
                      <span>
                        {runtime.agentTeams.length} coordinated solution teams assembled from architect, developer,
                        QA, security, compliance, and legal agents.
                      </span>
                    </article>
                    <article className="tool-mini-card">
                      <strong>Event bus</strong>
                      <span>
                        {runtime.eventBus.domainEvents} domain events, {runtime.eventBus.retryQueue} retries, and{" "}
                        {runtime.eventBus.deadLetterQueue} dead letters are tracked for replay and audit.
                      </span>
                    </article>
                  </div>
                </div>
              </article>

              <aside className="tool-side-pane">
                <div className="tool-side-panel">
                  <p className="section-label">Navigation</p>
                  <div className="tool-nav-list">
                    {activeRole.windows.map((window) => (
                      <button
                        key={window.id}
                        type="button"
                        className={window.id === selectedWindow.id ? "tool-nav-item active" : "tool-nav-item"}
                        onClick={() => setSelectedWindowId(window.id)}
                      >
                        {window.title}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="tool-side-panel">
                  <p className="section-label">AI Panel</p>
                  <p className="studio-note">
                    Chat, history, memory, files, code, knowledge, tasks, agents, and automation.
                  </p>
                </div>
              </aside>
            </div>

            <div className="smart-command-bar">
              <label className="smart-command-input">
                <span>What would you like to accomplish today?</span>
                <input
                  value={smartCommand}
                  onChange={(event) => setSmartCommand(event.target.value)}
                  placeholder="Generate payment microservice"
                />
              </label>
              <div className="smart-command-actions">
                {["Voice", "Files", "Search", "Agents", "Terminal", "History", "Automations"].map((item) => (
                  <button key={item} type="button" className="toolbar-chip">
                    {item}
                  </button>
                ))}
              </div>
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
                <p className="section-label">Enterprise UX Operating System</p>
                <h2>Governed design-to-operations lifecycle</h2>
              </div>
              <div className="layout-hint">
                <span>{uxOperatingSummary.model.status}</span>
                <span>{uxOperatingSummary.readiness.status}</span>
              </div>
            </div>
            <div className="center-grid">
              {[
                ["Studios", uxOperatingSummary.model.studios.length, "Coordinated UX studios own artifacts, approvals, metrics, and evidence."],
                ["Artifacts", uxOperatingSummary.artifacts.length, "Requirements, journeys, prototypes, reviews, handoff, and verification records."],
                ["Evidence", uxOperatingSummary.evidenceCount, "Evidence references linked to versioned UX artifacts."],
                ["Components", uxOperatingSummary.approvedComponents, "Approved enterprise component assets in the governed registry."],
                ["Services", uxOperatingSummary.serviceCount, "Runtime UXOS services for integration, regression, analytics, experiments, graph, and twin."],
                ["Service records", uxOperatingSummary.serviceRecords.length, "Evidence-pending records from UXOS service automation."],
              ].map(([label, value, note]) => (
                <article className="center-card" key={label}>
                  <p className="section-label">{label}</p>
                  <strong>{value}</strong>
                  <p>{note}</p>
                </article>
              ))}
            </div>
            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Lifecycle</p>
                <strong>From strategy to continuous optimization</strong>
                <div className="artifact-list">
                  {uxOperatingSummary.visibleLifecycle.map((stage, index) => (
                    <div className="artifact-row" key={stage}>
                      <strong>{String(index + 1).padStart(2, "0")} · {stage}</strong>
                      <span>Traceable design workstream stage</span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">Governed artifacts</p>
                <strong>Versioned UX assets with evidence</strong>
                <div className="artifact-list">
                  {uxOperatingSummary.artifacts.slice(0, 5).map((artifact) => (
                    <div className="artifact-row" key={artifact.id}>
                      <strong>{artifact.artifact}</strong>
                      <span>
                        {artifact.studio} · {artifact.approvalState} · {artifact.evidence?.length || 0} evidence refs
                      </span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">State gates</p>
                <strong>PRR and executive approval remain separate</strong>
                <div className="compact-list">
                  {uxOperatingSummary.approvalLifecycle.map((state) => (
                    <span className="compact-pill" key={state}>
                      {state}
                    </span>
                  ))}
                </div>
                <p className="studio-note">
                  GA allowed: {uxOperatingSummary.readiness.gaAllowed ? "true" : "false"} · Real payments remain
                  governed outside UX approval.
                </p>
              </article>
              <article className="studio-card">
                <p className="section-label">Service fabric</p>
                <strong>Runtime UXOS services publish evidence</strong>
                <div className="compact-list">
                  {(runtime.uxosRuntimeServices || UXOS_RUNTIME_SERVICES).slice(0, 8).map((service) => (
                    <span className="compact-pill" key={service}>
                      {service}
                    </span>
                  ))}
                </div>
                <div className="artifact-list">
                  {uxOperatingSummary.serviceRecords.slice(0, 3).map((record) => (
                    <div className="artifact-row" key={record.id}>
                      <strong>{record.subject}</strong>
                      <span>{record.kind} · {record.status}</span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">Actions</p>
                <strong>Capture, evidence, assess</strong>
                <div className="studio-actions">
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() =>
                      platformRuntime.createUxArtifact({
                        artifact: "New governed UX artifact",
                        artifactType: "wireframe",
                        studio: "Wireframe Studio",
                      })
                    }
                  >
                    Create artifact
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.attachUxEvidence(uxOperatingSummary.artifacts[0]?.id, "ux-review-evidence.yaml")}
                  >
                    Attach evidence
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.assessUxReleaseReadiness()}
                  >
                    Assess release
                  </button>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() =>
                      platformRuntime.recordUxosService("ux_visual_regression", {
                        subject: "Dashboard baseline comparison",
                        provider: "Chrome",
                      })
                    }
                  >
                    Record service
                  </button>
                </div>
              </article>
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
                <p className="section-label">NovaCodePro Experience Platform</p>
                <h2>One governed suite across web, mobile, inspector, desktop, CLI, and developer channels</h2>
              </div>
              <div className="layout-hint">
                <span>Web, mobile, and desktop share the same platform contract</span>
                <span>Inspector and developer channels stay evidence-driven</span>
              </div>
            </div>
            <div className="experience-suite-grid">
              {EXPERIENCE_CHANNELS.map((channel) => (
                <article className="experience-card" key={channel.id}>
                  <div className="experience-card-head">
                    <div>
                      <p className="section-label">{channel.title}</p>
                      <strong>{channel.domain}</strong>
                    </div>
                    <span className="status-pill">{channel.availability}</span>
                  </div>
                  <p className="studio-note">{channel.summary}</p>
                  <dl className="service-meta compact">
                    <div>
                      <dt>Auth</dt>
                      <dd>{channel.auth}</dd>
                    </div>
                    <div>
                      <dt>Version</dt>
                      <dd>{channel.version}</dd>
                    </div>
                    <div>
                      <dt>Region</dt>
                      <dd>{channel.region}</dd>
                    </div>
                    <div>
                      <dt>Evidence</dt>
                      <dd>{channel.evidence}</dd>
                    </div>
                  </dl>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => platformRuntime.runCommand(channel.command)}
                  >
                    {channel.command}
                  </button>
                </article>
              ))}
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Operational Verification</p>
                <h2>Configured, executed, verified, certified, and approved as distinct states</h2>
              </div>
              <div className="layout-hint">
                <span>Local UI state is not authoritative</span>
                <span>Evidence and approvals remain separate</span>
              </div>
            </div>
            <div className="verification-track">
              {OPERATIONAL_VERIFICATION_STEPS.map((step, index) => (
                <article className="verification-card" key={step.status}>
                  <p className="section-label">{String(index + 1).padStart(2, "0")}</p>
                  <strong>{step.status}</strong>
                  <p>{step.detail}</p>
                </article>
              ))}
            </div>
            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Developer portal</p>
                <strong>APIs, SDKs, tutorials, sandbox, auth, webhooks, changelog, and status</strong>
                <div className="artifact-list">
                  {DEVELOPER_SURFACES.map((surface) => (
                    <div className="artifact-row" key={surface.name}>
                      <strong>{surface.name}</strong>
                      <span>{surface.description}</span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">Product experiences</p>
                <strong>Public product landing pages share the same governed platform language</strong>
                <div className="compact-list">
                  {[
                    "NovaRide",
                    "NovaPay",
                    "NovaID",
                    "NovaTrust",
                    "NovaCloud",
                    "NovaGateway",
                    "NovaData",
                    "NovaConnect",
                    "NovaGov",
                  ].map((product) => (
                    <span className="compact-pill" key={product}>
                      {product}
                    </span>
                  ))}
                </div>
                <p className="studio-note">
                  Each product surface should keep availability, authentication, evidence, and lifecycle labels honest.
                </p>
              </article>
            </div>
          </section>

          <section className="surface-band">
            <div className="band-header">
              <div>
                <p className="section-label">Enterprise command center</p>
                <h2>Mission control for strategy, operations, risk, and recovery</h2>
              </div>
              <div className="layout-hint">
                <span>Window 29 service surface</span>
                <span>Authority-aware action execution</span>
              </div>
            </div>
            <div className="center-grid">
              {enterpriseCommandCenter.map((item) => (
                <article className="center-card" key={item.label}>
                  <p className="section-label">{item.label}</p>
                  <strong>{item.value}</strong>
                  <p>{item.note}</p>
                </article>
              ))}
            </div>
            <div className="studio-grid">
              <article className="studio-card">
                <p className="section-label">Situational awareness</p>
                <strong>Cross-domain operational state</strong>
                <div className="artifact-list">
                  {[
                    ["Security", "0 critical findings"],
                    ["Compliance", "Evidence chain current"],
                    ["Approvals", "No blocked gates"],
                    ["Operations", "Service health stable"],
                    ["Finance", "Usage within quota"],
                    ["Recovery", "Rollback path ready"],
                  ].map(([label, detail]) => (
                    <div className="artifact-row" key={label}>
                      <strong>{label}</strong>
                      <span>{detail}</span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="studio-card">
                <p className="section-label">Action queue</p>
                <strong>Ready-to-run enterprise actions</strong>
                <div className="studio-actions">
                  {[
                    "Open incident bridge",
                    "Review policy breach",
                    "Inspect deployment health",
                    "Escalate approval",
                    "Run recovery drill",
                    "Generate board brief",
                  ].map((action) => (
                    <button
                      type="button"
                      key={action}
                      className="toolbar-chip"
                      onClick={() => platformRuntime.runCommand(action)}
                    >
                      {action}
                    </button>
                  ))}
                </div>
              </article>
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
                <div className="metric-card">
                  <span>EROS</span>
                  <strong>{runtime.erosManifest.coreViews.length}</strong>
                </div>
              </div>
            </div>
          </section>
        </main>

        <aside className="context-rail">
          <section className="rail-card">
            <p className="section-label">Workspace context</p>
            <strong>{activeProject?.name || selectedRequest?.title || "NovaCodePro Studio"}</strong>
            <div className="signal-list">
              {[
                ["Organisation", activeRole.organization || session?.organization?.name || "NovaTech"],
                ["Workspace", activeTenant?.name || session?.workspace?.name || "Workspace"],
                ["Repository", activeProject?.repository || "Not connected"],
                ["Branch", activeProject?.branch || "main"],
                ["Environment", environment],
              ].map(([label, value]) => (
                <div className="signal-row" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="rail-card">
            <p className="section-label">Traceability</p>
            <strong>Requirements → code → tests → evidence</strong>
            <div className="chip-cloud compact">
              {[
                `Requirement ${selectedRequest?.id || "n/a"}`,
                `Commit ${NOVACODEPRO_BUILD_INFO.commit.slice(0, 8)}`,
                `Tests ${runtime.auditTrail.length}`,
                `Evidence ${runtime.evidenceBundles.length}`,
              ].map((item) => (
                <span className="context-chip" key={item}>
                  {item}
                </span>
              ))}
            </div>
            <p className="rail-note">
              The workspace keeps the active request, selected files, backend evidence, and audit trail visible together.
            </p>
          </section>

          <section className="rail-card">
            <p className="section-label">Security posture</p>
            <strong>{sessionWarning ? "Action required" : "Current workspace secured"}</strong>
            <div className="signal-list">
              {[
                ["Trust", sessionWarning ? "Session expiring" : "Trusted"],
                ["Auth", authStatus === "signed-in" ? "Signed in" : authStatus],
                ["Role", authDisplayRoleLabel],
                ["AI", toolView === "ai" ? "Active" : "Idle"],
              ].map(([label, value]) => (
                <div className="signal-row" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="rail-card">
            <p className="section-label">AI recommendations</p>
            <strong>Next governed actions</strong>
            <ul className="feed-list">
              {[
                "Review the current workspace summary and open files.",
                "Run the command palette for build, test, or deploy actions.",
                "Use NovaAI to generate tests, explain code, or propose a safe refactor.",
              ].map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

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
              {toPairArray(activeRole.signals).map(([label, value]) => (
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
              {toArray(activeRole.permissions).map((item) => (
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
              {toArray(activeRole.agents).map((item) => (
                <span className="context-chip" key={item}>
                  {item}
                </span>
              ))}
            </div>
          </section>

          <section className="rail-card">
            <p className="section-label">Notifications</p>
            <ul className="feed-list">
              {toArray(activeRole.notifications).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="rail-card">
            <p className="section-label">Recent activity</p>
            <ul className="feed-list">
              {toArray(activeRole.activity).map((item) => (
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
        </>
      )}
      </StudioChrome>

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
