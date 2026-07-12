import React, { useEffect, useMemo, useRef, useState } from "react";

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

const OPERATING_WINDOWS = [
  {
    name: "Test Center",
    summary: "Unit, integration, UI, API, security, performance, and accessibility results stay visible.",
    action: "Open Test Center",
  },
  {
    name: "Security Center",
    summary: "Threat models, SBOMs, dependencies, secrets, policies, and risk scores are reviewed here.",
    action: "Open Security Center",
  },
  {
    name: "Compliance Center",
    summary: "ISO, SOC2, PCI, privacy, regional laws, and data residency posture are consolidated.",
    action: "Open Compliance Center",
  },
  {
    name: "Human Approval Center",
    summary: "Architecture, security, compliance, executive, and release approvals are captured with evidence.",
    action: "Open Approval Center",
  },
  {
    name: "Release Factory",
    summary: "Build, test, sign, package, publish, and verify release artifacts from one governed surface.",
    action: "Open Release Factory",
  },
  {
    name: "Deployment Center",
    summary: "Promotion across development, testing, staging, pilot, and production is managed here.",
    action: "Open Deployment Center",
  },
  {
    name: "Digital Twin",
    summary: "Services, clusters, databases, queues, users, transactions, and KPI health are modelled live.",
    action: "Open Digital Twin",
  },
  {
    name: "Operations Center",
    summary: "Logs, traces, metrics, incidents, alerts, uptime, and deployment health are monitored continuously.",
    action: "Open Operations Center",
  },
  {
    name: "Marketplace",
    summary: "Solution packs, templates, agents, governance packs, and integrations can be installed safely.",
    action: "Open Marketplace",
  },
  {
    name: "Executive Dashboard",
    summary: "Revenue, velocity, adoption, risk score, trust score, and release performance remain strategic.",
    action: "Open Executive Dashboard",
  },
  {
    name: "Continuous Improvement",
    summary: "Monitoring feeds back into AI analysis, issue detection, improvement, testing, and release.",
    action: "Open Improvement Loop",
  },
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

const DIGITAL_TWIN_LAYERS = [
  ["Australia", "Active region"],
  ["Africa", "Pilot region"],
  ["Europe", "Scaling region"],
  ["Asia", "Expansion region"],
  ["America", "Growth region"],
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

function App() {
  const attachmentInputRef = useRef(null);
  const runtime = usePlatformRuntime();
  const [platformSummary, setPlatformSummary] = useState(null);
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
  const [discoveryAnswers, setDiscoveryAnswers] = useState({
    users: "Customers, operations, and support teams.",
    regions: "Australia, Kenya, and DR Congo.",
    controls: "Regulated payments, privacy, and audit controls.",
    channels: "Mobile apps, web portal, partner APIs.",
    languages: "English, French, and Swahili.",
  });

  useEffect(() => {
    const controller = new AbortController();
    const baseUrl = import.meta.env.VITE_NOVACODEPRO_API_BASE_URL || "";

    fetch(`${baseUrl}/v1/novacodepro/admin/summary`, {
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
              { name: "Release Factory", status: "healthy", category: "delivery" },
              { name: "Digital Twin Engine", status: "healthy", category: "observability" },
            ],
    };
  }, [platformSummary, runtime.connectedIntegrations.length, runtime.auditTrail.length, runtime.solutionRequests.length, runtime.tenants.length]);

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

  const requestSummary = useMemo(() => {
    const prompt = composerPrompt.trim();
    return prompt.length ? prompt : activeRequest?.request || STARTER_REQUESTS[0];
  }, [activeRequest?.request, composerPrompt]);

  const suggestedTitle = useMemo(() => {
    const source = requestSummary.split(/[.!?]/)[0].trim();
    if (!source) {
      return "NovaCodePro solution request";
    }
    return source.length > 64 ? `${source.slice(0, 61)}...` : source;
  }, [requestSummary]);

  const selectedMode = COMPOSER_MODES.find((mode) => mode.id === composerMode) ?? COMPOSER_MODES[0];

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
    const currentApprovals = activeRequest?.approvals ?? [];
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
                {[
                  "Secrets scanned before release",
                  "Policy checks executed against the target environment",
                  "Production deployment remains approval-gated",
                ].map((item) => (
                  <div className="artifact-row" key={item}>
                    <strong>{item}</strong>
                    <span>Governed</span>
                  </div>
                ))}
              </div>
            </article>
            <article className="output-card">
              <p className="section-label">Current approvals</p>
              <div className="artifact-list">
                {currentApprovals.length ? (
                  currentApprovals.map((approval) => (
                    <div className="artifact-row" key={approval.id}>
                      <strong>{approval.gate}</strong>
                      <span>{approval.by}</span>
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
                {currentArtifacts.slice(0, 4).map((artifact) => (
                  <div className="artifact-row" key={artifact.id}>
                    <strong>{artifact.title}</strong>
                    <span>{artifact.stage}</span>
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
          <section className="hero-card request-console">
            <div className="console-main">
              <div className="console-intro">
                <p className="eyebrow">Business-first enterprise operating workflow</p>
                <h1>What would you like NovaCodePro to build or solve?</h1>
                <p className="hero-summary">
                  Describe a product, upload an existing project, report a problem, or ask
                  NovaCodePro to design, implement, test, secure, or deploy a governed solution.
                </p>
                <div className="hero-badges">
                  <span className="badge">Organization: {activeRole.organization}</span>
                  <span className="badge">Environment: {environment}</span>
                  <span className="badge">Workspace: Solution Studio</span>
                  <span className="badge">Tenant: {activeTenant.name}</span>
                  <span className="badge">Project: {activeProject.name}</span>
                  <span className="badge">Mode: {selectedMode.label}</span>
                </div>
              </div>

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
                <p className="section-label">Operating windows</p>
                <h2>Real workflow stages with tangible outputs</h2>
              </div>
              <div className="layout-hint">
                <span>All stages are navigable</span>
                <span>Each window maps to a real workflow stage</span>
              </div>
            </div>

            <div className="center-grid">
              {OPERATING_WINDOWS.map((window) => (
                <article className="center-card" key={window.name}>
                  <p className="section-label">{window.name}</p>
                  <p>{window.summary}</p>
                  <button
                    type="button"
                    className="toolbar-chip"
                    onClick={() => runtime.runCommand(window.action)}
                  >
                    {window.action}
                  </button>
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
