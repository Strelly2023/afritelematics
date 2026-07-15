import {
  AGENT_MARKETPLACE,
  AUTOMATION_TEMPLATES,
  COLLABORATION_THREADS,
  DEVELOPER_SURFACES,
  INTEGRATIONS,
  KNOWLEDGE_GRAPH,
  PLATFORM_CENTERS,
  PROJECTS,
  SERVICE_CATALOG,
  SOLUTION_TEMPLATES,
  TENANTS,
  WORKFLOW_SEQUENCE,
  WORKFLOW_STAGES,
} from "./catalog.js";

const STORAGE_KEY = "novacodepro.platform.runtime.v1";

const NERA_ARCHITECTURE = {
  id: "nera",
  name: "NovaTech Enterprise Reference Architecture",
  version: "2.0",
  status: "Enterprise Reference Standard",
  layers: [
    {
      id: "corporate-governance",
      name: "Corporate Governance",
      purpose: "Board, executive, and enterprise accountability.",
    },
    {
      id: "enterprise-governance",
      name: "Enterprise Governance Layer",
      purpose: "Identity, security, policy, risk, compliance, and audit.",
    },
    {
      id: "enterprise-platform",
      name: "Enterprise Platform Layer",
      purpose: "Reusable capabilities shared across all products.",
    },
    {
      id: "knowledge-intelligence",
      name: "Knowledge & Intelligence Plane",
      purpose: "Enterprise memory, reasoning, and digital twin intelligence.",
    },
    {
      id: "enterprise-ai",
      name: "Enterprise AI Plane",
      purpose: "Governed model, agent, reasoning, memory, and tool runtime.",
    },
    {
      id: "digital-twin-resilience",
      name: "Digital Twin & Resilience Plane",
      purpose: "Enterprise state, simulations, recovery planning, validation, replay, evidence, and scoring.",
    },
    {
      id: "business-products",
      name: "Business Product Plane",
      purpose: "Customer-facing and partner-facing products.",
    },
    {
      id: "enterprise-operations",
      name: "Enterprise Operations Layer",
      purpose: "Run-the-business operations and support functions.",
    },
    {
      id: "shared-enterprise-services",
      name: "Shared Enterprise Services",
      purpose: "Common services consumed by every product and platform domain.",
    },
    {
      id: "infrastructure",
      name: "Infrastructure Layer",
      purpose: "Cloud, networking, runtime, storage, and edge services.",
    },
  ],
  platformDomains: [
    "NovaWorkspace",
    "NovaProjects",
    "NovaAgents",
    "NovaExecution",
    "NovaReviews",
    "NovaApprovals",
    "NovaGovernance",
    "NovaKnowledge",
    "NovaAutomation",
    "NovaTesting",
    "NovaDeployments",
    "NovaObservability",
    "NovaReporting",
    "NovaAdministration",
  ],
  canonicalEnterpriseStructure: [
    "Corporate Governance",
    "Enterprise Governance Plane",
    "Enterprise Platform Plane",
    "Knowledge & Intelligence Plane",
    "Enterprise AI Plane",
    "Digital Twin & Resilience Plane",
    "Business Product Plane",
    "Enterprise Operations Plane",
    "Shared Enterprise Services",
    "Infrastructure & Regional Runtime",
  ],
  portalStates: ["Loading", "Ready", "Empty", "Degraded", "Unavailable", "Forbidden", "Error", "Recovery"],
};

const CANONICAL_STATE_VIEWS = [
  "Observed State",
  "Desired State",
  "Predicted State",
  "Simulated State",
  "Approved State",
  "Recovered State",
];

const AUTHORITY_LEVELS = [
  { level: 0, mode: "Observe" },
  { level: 1, mode: "Recommend" },
  { level: 2, mode: "Prepare" },
  { level: 3, mode: "Execute with Approval" },
  { level: 4, mode: "Execute under Pre-Approval" },
  { level: 5, mode: "Emergency Containment" },
];

const CAPABILITY_DOMAINS = [
  "Strategy, Governance & Leadership",
  "Enterprise Architecture & Transformation",
  "Product & Portfolio Management",
  "Customer, Partner & Market Management",
  "Software Engineering & Digital Delivery",
  "Platform, Cloud & Infrastructure",
  "Data, Knowledge & Intelligence",
  "Artificial Intelligence & Agent Operations",
  "Identity, Security, Trust & Privacy",
  "Risk, Compliance, Legal & Audit",
  "Enterprise Operations & Service Management",
  "Resilience, Continuity & Recovery",
  "Finance, Commercial & Procurement",
  "People, Workforce & Organization",
  "Sales, Marketing & Communications",
  "Ecosystem, Integration & Developer Enablement",
  "Industry Product Capabilities",
  "Enterprise Measurement & Improvement",
];

const NEAF_MODEL = {
  id: "neaf",
  name: "NovaTech Enterprise Plane Model",
  version: "1.0",
  sequence: [
    "Governance Plane",
    "Intelligence Plane",
    "Execution Plane",
    "Product Plane",
    "Infrastructure Plane",
  ],
  planes: [
    {
      id: "governance-plane",
      name: "Governance Plane",
      owner: "NovaGovernance",
      responsibilities: ["Trust", "Identity", "Security", "Policy", "Risk", "Compliance", "Audit", "Legal", "Privacy", "Authority"],
      platforms: ["NovaTrust", "NovaID", "NovaSecure", "NovaPolicy", "NovaRisk", "NovaCompliance", "NovaAudit", "NovaLegal", "NovaPrivacy", "NovaAuthority"],
    },
    {
      id: "intelligence-plane",
      name: "Intelligence Plane",
      owner: "NovaIntelligence",
      responsibilities: ["Knowledge", "Graph", "Memory", "Decision", "Insights", "Learning", "Digital Twin", "Search", "Reasoning"],
      platforms: ["NovaKnowledge", "NovaGraph", "NovaMemory", "NovaDecision", "NovaInsights", "NovaLearning", "NovaDigitalTwin", "NovaSearch", "NovaReasoning"],
    },
    {
      id: "execution-plane",
      name: "Execution Plane",
      owner: "NovaExecution",
      responsibilities: ["Workspace", "Projects", "Reviews", "Approvals", "Workflow", "Automation", "Deployments", "Testing", "Operations"],
      platforms: ["NovaCodePro", "NovaWorkspace", "NovaProjects", "NovaReviews", "NovaApprovals", "NovaWorkflow", "NovaAutomation", "NovaDeployments", "NovaTesting", "NovaOperations"],
    },
    {
      id: "product-plane",
      name: "Product Plane",
      owner: "NovaProducts",
      responsibilities: ["Customer value", "Modular product evolution", "Market differentiation", "Industry-specific solutions"],
      platforms: ["NovaRide", "NovaPay", "NovaHealth", "NovaCommerce", "NovaEducation", "NovaAgriculture", "NovaEnergy", "NovaInsurance", "NovaRealEstate", "NovaFood", "NovaGov", "NovaERP", "NovaCRM", "NovaAnalytics", "NovaLogistics"],
    },
    {
      id: "infrastructure-plane",
      name: "Infrastructure Plane",
      owner: "NovaInfrastructure",
      responsibilities: ["Cloud", "Gateway", "Events", "API", "Storage", "Network", "Regions", "Observability", "Monitoring", "Recovery"],
      platforms: ["NovaCloud", "NovaGateway", "NovaEvents", "NovaAPI", "NovaStorage", "NovaNetwork", "NovaRegions", "NovaObservability", "NovaMonitoring", "NovaRecovery"],
    },
  ],
  interactionModel: [
    "Governance -> Intelligence",
    "Intelligence -> Execution",
    "Execution -> Products",
    "Products -> Infrastructure",
    "Infrastructure -> Governance evidence and telemetry",
  ],
  enterpriseStateModels: ["Observed State", "Desired State", "Predicted State", "Simulated State", "Approved State", "Recovered State"],
  aiWorkforce: ["Executive Agents", "Architecture Agents", "Engineering Agents", "QA Agents", "Security Agents", "Compliance Agents", "Finance Agents", "Support Agents", "Operations Agents", "Research Agents"],
  reasoningDomains: ["Strategic Reasoning", "Operational Reasoning", "Financial Reasoning", "Security Reasoning", "Compliance Reasoning", "Architecture Reasoning", "Risk Reasoning", "Recovery Reasoning", "Executive Reasoning"],
};

const EROS_MANIFEST = {
  id: "eros",
  name: "NovaDigitalTwin Enterprise Resilience Operating System",
  version: "3.0",
  status: "Enterprise Reference Standard",
  coreViews: CANONICAL_STATE_VIEWS,
  authorityLevels: AUTHORITY_LEVELS,
  runtimeServices: [
    "Observation Engine",
    "State Intelligence Engine",
    "Dependency Intelligence Engine",
    "Risk Intelligence Engine",
    "Prediction Engine",
    "Twin Registry",
    "Twin State",
    "Twin Graph",
    "Simulation Engine",
    "Decision Intelligence Engine",
    "Recovery Planner",
    "Recovery Orchestrator",
    "Validation Engine",
    "Evidence Ledger",
    "Replay Engine",
    "Learning Engine",
    "Optimization Engine",
  ],
  lifecycle: [
    "Observe",
    "Understand",
    "Predict",
    "Simulate",
    "Recommend",
    "Approve",
    "Execute",
    "Validate",
    "Capture Evidence",
    "Learn",
    "Optimize",
  ],
  twinHierarchy: [
    "Enterprise Twin",
    "Organization Twins",
    "Business Unit Twins",
    "Capability Twins",
    "Product Twins",
    "Platform Twins",
    "Service Twins",
    "Application Twins",
    "Workflow Twins",
    "Data Twins",
    "Process Twins",
    "Infrastructure Twins",
    "Region Twins",
    "Financial Twins",
    "Security Twins",
    "Risk Twins",
    "Compliance Twins",
    "AI Twins",
  ],
  enterpriseMemory: [
    "Architecture Memory",
    "Operational Memory",
    "Governance Memory",
    "Product Memory",
    "Customer Memory",
    "Incident Memory",
    "Recovery Memory",
    "AI Memory",
    "Decision Memory",
    "Historical Memory",
  ],
  simulationClasses: [
    "Infrastructure failure",
    "Region outage",
    "Database failure",
    "Network partition",
    "Capacity exhaustion",
    "Cyberattack",
    "Identity compromise",
    "Certificate expiry",
    "Vendor outage",
    "Supply-chain disruption",
    "Regulatory change",
    "Financial stress",
    "Data corruption",
    "AI model degradation",
    "Product launch surge",
    "Organizational restructuring",
  ],
  recoveryValidation: ["Infrastructure Validation", "Application Validation", "Dependency Validation", "Business Validation", "Security Validation", "Data Integrity Validation", "Evidence Verification"],
};

const UX_OPERATING_SYSTEM = {
  id: "novacodepro-ux-os",
  name: "NovaCodePro Enterprise UX Operating System",
  status: "Implemented · Evidence pending",
  lifecycle: [
    "Business Strategy",
    "Requirements Engineering",
    "Research Intelligence",
    "Experience Strategy",
    "Information Architecture",
    "Journey Engineering",
    "Wireframe Studio",
    "Design System",
    "Visual Design",
    "Prototype Studio",
    "Accessibility Engine",
    "Usability Validation",
    "AI UX Review",
    "Design Governance",
    "Developer Handoff",
    "Implementation Verification",
    "Performance Validation",
    "Security Validation",
    "Operational Validation",
    "Production Readiness Review",
    "Executive Approval",
    "Continuous Optimization",
  ],
  stateModel: [
    "DRAFT",
    "RESEARCH_COMPLETE",
    "IA_APPROVED",
    "JOURNEYS_APPROVED",
    "WIREFRAME_APPROVED",
    "DESIGN_SYSTEM_APPROVED",
    "VISUAL_DESIGN_APPROVED",
    "PROTOTYPE_VALIDATED",
    "ACCESSIBILITY_APPROVED",
    "LOCALIZATION_APPROVED",
    "USABILITY_APPROVED",
    "HANDOFF_COMPLETE",
    "IMPLEMENTATION_VERIFIED",
    "PERFORMANCE_APPROVED",
    "SECURITY_APPROVED",
    "READY_FOR_PRR_APPROVAL",
    "PRR_APPROVED",
    "EXECUTIVE_APPROVED",
    "GENERAL_AVAILABILITY",
  ],
  studios: [
    "Requirements Studio",
    "Research Studio",
    "Journey Studio",
    "Wireframe Studio",
    "Prototype Studio",
    "Design System Studio",
    "Accessibility Studio",
    "Localization Studio",
    "Motion Studio",
    "Mobile Studio",
    "Desktop Studio",
    "Dashboard Studio",
    "AI Design Studio",
    "Component Studio",
    "Design Review Center",
    "Handoff Center",
    "Verification Center",
    "UX Analytics Center",
    "Experiment Center",
    "UX Governance Center",
  ],
  agents: [
    "Requirements Agent",
    "Research Agent",
    "Journey Agent",
    "Wireframe Agent",
    "Visual Design Agent",
    "Accessibility Agent",
    "Localization Agent",
    "Prototype Agent",
    "Design Review Agent",
    "Implementation Verification Agent",
    "Analytics Agent",
    "Optimization Agent",
  ],
  governance: {
    gaAllowed: false,
    realPaymentsEnabled: false,
    boundary: "UX approval does not approve PRR, executive authorization, payment activation, or GA.",
  },
};

const UX_COMPONENT_REGISTRY = [
  "Buttons",
  "Cards",
  "Forms",
  "Inputs",
  "Lists",
  "Maps",
  "Charts",
  "Dialogs",
  "Navigation",
  "Data Tables",
  "Date Pickers",
  "Media",
  "Notifications",
].map((component, index) => ({
  id: `ux-component-${component.toLowerCase().replaceAll(" ", "-")}`,
  component,
  version: `2026.${index + 1}.0`,
  owner: "NovaCodePro Design System",
  status: index < 8 ? "APPROVED" : "DRAFT",
  accessibility: index < 8 ? "WCAG 2.2 AA" : "Review pending",
  performance: index < 8 ? "Within budget" : "Budget pending",
}));

const UX_ARTIFACT_SEED = [
  {
    id: "uxart-requirements",
    artifact: "NovaRide booking requirements",
    artifactType: "requirement",
    studio: "Requirements Studio",
    owner: "Product",
    approvalState: "RESEARCH_COMPLETE",
    version: "v1",
    evidence: ["requirements-specification.yaml", "acceptance-criteria.yaml"],
  },
  {
    id: "uxart-prototype",
    artifact: "Rider booking prototype",
    artifactType: "prototype",
    studio: "Prototype Studio",
    owner: "UX",
    approvalState: "PROTOTYPE_VALIDATED",
    version: "v3",
    evidence: ["prototype-validation.yaml", "failure-simulation-report.yaml"],
  },
  {
    id: "uxart-accessibility",
    artifact: "Rider accessibility review",
    artifactType: "accessibility_review",
    studio: "Accessibility Studio",
    owner: "Accessibility",
    approvalState: "ACCESSIBILITY_APPROVED",
    version: "v2",
    evidence: ["accessibility-report.yaml", "assistive-tech-evidence/"],
  },
  {
    id: "uxart-verification",
    artifact: "Implementation verification",
    artifactType: "implementation_verification",
    studio: "Verification Center",
    owner: "Quality",
    approvalState: "IMPLEMENTATION_VERIFIED",
    version: "v1",
    evidence: ["ux-verification.yaml", "visual-regression/"],
  },
];

const UXOS_RUNTIME_SERVICES = [
  "UX Gateway",
  "UX Artifact Service",
  "Journey Service",
  "Design System Service",
  "Design Integration Service",
  "Accessibility Service",
  "Visual Regression Service",
  "Analytics Service",
  "Experiment Service",
  "Knowledge Graph Service",
  "Digital Twin Service",
  "Evidence Service",
  "Governance Service",
  "PRR Service",
  "Executive Approval Service",
];

const COMPLETION_STANDARD = {
  name: "NovaCodePro Enterprise Completion Standard",
  levels: [
    "Repository Complete",
    "Operationally Verified",
    "Governance Approved",
    "Production Ready",
    "General Availability",
  ],
  repositoryDeliverables: [
    "Architecture",
    "Domain Models",
    "Services",
    "Persistent Stores",
    "REST APIs",
    "SDKs",
    "Portal UI",
    "CLI",
    "Automation",
    "Documentation",
    "Evidence Models",
    "Governance Models",
    "Tests",
    "CI Validation",
  ],
  operationalVerifications: [
    "Design synchronization",
    "Visual regression",
    "Accessibility automation",
    "Telemetry collection",
    "Experiment execution",
    "Knowledge graph synchronization",
    "Digital twin simulation",
    "Container deployment",
    "Monitoring",
    "Alerting",
    "Tracing",
    "Runtime Performance",
  ],
  governanceApprovals: ["UX Lead", "Engineering Lead", "Security", "Operations", "Compliance", "Product", "Executive"],
  productionReadyGates: [
    "Evidence Complete",
    "Monitoring Healthy",
    "Alerts Verified",
    "Backups Verified",
    "Recovery Tested",
    "Observability Verified",
    "Performance Verified",
    "Security Verified",
    "Compliance Verified",
  ],
  domains: [
    "UXOS Services",
    "APIs",
    "Portal",
    "Design Integration",
    "Visual Regression",
    "Accessibility",
    "Analytics",
    "Experimentation",
    "Knowledge Graph",
    "Digital UX Twin",
    "PRR",
    "GA Promotion",
  ],
  invariants: {
    gaAllowed: false,
    realPaymentsEnabled: false,
  },
};

function buildCompletionDashboard() {
  return {
    status: "DIMENSIONAL_COMPLETION_DASHBOARD",
    columns: ["Repository", "Operational", "Governance"],
    rows: COMPLETION_STANDARD.domains.map((domain) => ({
      domain,
      repository: domain !== "GA Promotion",
      operational: false,
      governance: "PENDING",
    })),
    gaAllowed: false,
    realPaymentsEnabled: false,
  };
}

const OPERATIONAL_READINESS_PROGRAM = {
  name: "NovaCodePro Operational Readiness Program",
  maturityLayers: [
    "Enterprise Architecture",
    "Repository Implementation",
    "Operational Verification",
    "Governance Approval",
    "Production Operation",
  ],
  studios: [
    "Requirements Studio",
    "Architecture Studio",
    "UX Studio",
    "AI Engineering Studio",
    "API Studio",
    "Security Studio",
    "Build Studio",
    "Release Studio",
    "Deployment Studio",
    "Runtime Studio",
    "Verification Studio",
    "Replay Studio",
    "Observability Studio",
    "Evidence Studio",
    "Compliance Studio",
    "PRR Center",
    "Executive Approval Center",
    "GA Governance Center",
    "Enterprise Command Center",
  ],
  paymentActivation: {
    providers: ["Stripe", "Adyen", "PayPal", "Square", "Braintree", "Regional Providers", "Mobile Money Providers", "Bank Rails"],
    interface: ["Authorize", "Capture", "Refund", "Void", "Dispute", "Settlement", "Webhook", "Reconciliation"],
    requirements: ["sandboxCertification", "webhookVerification", "reconciliationValidation", "fraudControls", "failoverTesting"],
  },
  integrationFabric: {
    design: ["Figma", "Penpot", "Storybook", "Zeroheight", "Design Tokens"],
    engineering: ["GitHub", "CI/CD", "Package Registry", "Artifact Repository"],
    operations: ["Prometheus", "Grafana", "OpenTelemetry", "Alertmanager", "Cloud Monitoring"],
    accessibility: ["axe-core", "Pa11y", "Lighthouse", "Accessibility Insights"],
    knowledge: ["Requirements", "Architecture Decisions", "Pull Requests", "Tests", "Evidence", "Releases", "Runbooks"],
  },
  telemetryPipeline: ["Application", "OpenTelemetry", "Collector", "Metrics", "Logs", "Traces", "Analytics", "Evidence", "Knowledge Graph", "Digital Twin"],
  readinessMatrix: [
    ["UX Operating System", true, false, "PENDING"],
    ["AI Engineering", true, false, "PENDING"],
    ["Design Integration", true, false, "PENDING"],
    ["Visual Regression", true, false, "PENDING"],
    ["Accessibility Automation", true, false, "PENDING"],
    ["OpenTelemetry", true, false, "PENDING"],
    ["Production Analytics", true, false, "PENDING"],
    ["Digital UX Twin", true, false, "PENDING"],
    ["Automated PRR", true, false, "PENDING"],
    ["Executive Workflow", true, false, "PENDING"],
    ["Payment Sandbox", true, false, "PENDING"],
    ["Production Payments", false, false, "PENDING"],
    ["General Availability", false, false, "PENDING"],
  ].map(([capability, repository, operational, governance]) => ({ capability, repository, operational, governance })),
  invariants: {
    gaAllowed: false,
    realPaymentsEnabled: false,
  },
};

const NECM_MODEL = {
  id: "necm",
  name: "NovaTech Enterprise Capability Model",
  version: "2.0",
  capabilityDomains: CAPABILITY_DOMAINS,
  capabilities: CAPABILITY_DOMAINS,
  criticalityModel: ["TIER_0", "TIER_1", "TIER_2", "TIER_3", "TIER_4"],
  healthModel: ["HEALTHY", "DEGRADED", "AT_RISK", "UNAVAILABLE", "RECOVERING", "SUSPENDED", "RETIRED"],
};

const NEOM_MODEL = {
  id: "neom",
  name: "NovaTech Enterprise Operating Model",
  version: "2.0",
  people: ["Executives", "Product Managers", "Engineers", "Analysts", "Operators", "Legal", "Compliance"],
  roles: ["Owner", "Steward", "Approver", "Operator", "Agent", "Reviewer"],
  workspaces: ["NovaCodePro", "Customer Platforms", "Partner Platforms", "Enterprise Analytics"],
  deliveryModel: ["Describe", "Understand", "Architect", "Plan", "Assign", "Develop", "Review", "Test", "Govern", "Approve", "Release", "Deploy", "Verify", "Learn"],
};

const NEDM_MODEL = {
  id: "nedm",
  name: "NovaTech Enterprise Data Model",
  version: "2.0",
  dataPlanes: ["Master Data Plane", "Reference Data Plane", "Transactional Data Plane", "Operational Data Plane", "Event and Temporal Data Plane", "Analytical Data Plane", "Knowledge and Semantic Data Plane", "Digital Twin Data Plane", "AI and Agent Data Plane", "Governance and Evidence Data Plane", "Security and Privacy Data Plane", "External and Partner Data Plane"],
  classifications: ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "REGULATED", "SECRET"],
};

const NEKM_MODEL = {
  id: "nekm",
  name: "NovaTech Enterprise Knowledge Model",
  version: "2.0",
  knowledgeTypes: ["Descriptive", "Procedural", "Decision", "Experiential", "Regulatory", "Analytical", "AI"],
  memoryClasses: ["Working Memory", "Session Memory", "Workspace Memory", "Project Memory", "Product Memory", "Domain Memory", "Operational Memory", "Governance Memory", "Incident Memory", "Recovery Memory", "Decision Memory", "Architecture Memory", "AI Memory", "Historical Enterprise Memory"],
};

const NETM_MODEL = {
  id: "netm",
  name: "NovaTech Enterprise Technology Model",
  version: "2.0",
  technologyDomains: ["Enterprise Platform", "Application Platform", "AI Platform", "Identity Platform", "Integration Platform", "Data Platform", "Knowledge Platform", "Digital Twin Platform", "Cloud Platform", "Infrastructure Platform", "Security Platform", "Developer Platform", "DevSecOps Platform", "Observability Platform", "Automation Platform", "Resilience Platform"],
};

const NEGM_MODEL = {
  id: "negm",
  name: "NovaTech Enterprise Governance Model",
  version: "2.0",
  governanceChain: ["Identity", "Authentication", "Role and Attribute Resolution", "Policy Evaluation", "Risk Evaluation", "Compliance Evaluation", "Authority and Approval", "Execution", "Evidence and Audit"],
  authorityLevels: AUTHORITY_LEVELS,
};

const NEAM_MODEL = {
  id: "neam",
  name: "NovaTech Enterprise AI Model",
  version: "2.0",
  riskClasses: ["AI-0 Informational", "AI-1 Low Risk", "AI-2 Moderate Risk", "AI-3 High Risk", "AI-4 Critical"],
  authorityLevels: AUTHORITY_LEVELS,
};

const NEDTM_MODEL = {
  id: "nedtm",
  aliases: ["ndtm"],
  name: "NovaTech Enterprise Digital Twin Model",
  version: "2.0",
  stateViews: CANONICAL_STATE_VIEWS,
  capabilities: ["Twin registry", "Observation ingestion", "State reconciliation", "Relationship graph", "Snapshots", "Replay support", "Prediction", "Scenario simulation", "Cascading failure analysis", "Decision support", "Approved state transition", "Recovery planning", "Recovery execution", "Recovery validation", "Evidence capture", "RTO/RPO analysis", "Model drift detection", "Twin calibration"],
};

const NERM_MODEL = {
  id: "nerm",
  name: "NovaTech Enterprise Resilience Model",
  version: "2.0",
  objectives: ["RTO", "RPO", "MTD", "MBCO", "WRT", "Recovery capacity objective"],
  validationLayers: ["Infrastructure", "Application", "Dependency", "Data", "Security and compliance", "Business outcome"],
};

const ENTERPRISE_ARCHITECTURE_FRAMEWORK = {
  id: "natech-framework",
  name: "NovaTech AI-Native Enterprise Operating System Framework",
  version: "2.0",
  models: {
    neaf: NEAF_MODEL,
    nera: NERA_ARCHITECTURE,
    necm: NECM_MODEL,
    neom: NEOM_MODEL,
    nedm: NEDM_MODEL,
    nekm: NEKM_MODEL,
    netm: NETM_MODEL,
    negm: NEGM_MODEL,
    neam: NEAM_MODEL,
    nedtm: NEDTM_MODEL,
    ndtm: { ...NEDTM_MODEL, id: "ndtm", canonicalId: "nedtm", aliasFor: "nedtm" },
    nerm: NERM_MODEL,
  },
  modelRelationships: {
    NERA: "Defines enterprise structure",
    NECM: "Defines capabilities",
    NEOM: "Defines people, AI, and processes",
    NEDM: "Defines information and authoritative data",
    NEKM: "Defines knowledge, meaning, decisions, and memory",
    NETM: "Defines technologies and standards",
    NEGM: "Defines authority and control",
    NEAM: "Defines AI, models, agents, and human oversight",
    NEDTM: "Defines enterprise state",
    NERM: "Defines resilience and recovery",
    EROS: "Operationalizes resilience",
  },
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function nowIso() {
  return new Date().toISOString();
}

function createAuditEvent({ actor, action, service, subject, evidence, detail }) {
  return {
    id: `audit-${Math.random().toString(36).slice(2, 10)}`,
    at: nowIso(),
    actor,
    action,
    service,
    subject,
    evidence,
    detail,
  };
}

function buildStageState(stage, index, activeIndex = 0) {
  const status = index < activeIndex ? "completed" : index === activeIndex ? "in_progress" : "pending";
  return {
    ...stage,
    status,
    evidence: status === "completed" ? [stage.output, stage.api] : [],
    approvals: stage.kind === "human" ? [] : undefined,
  };
}

function templateFromRequest(requestText) {
  const normalized = requestText.toLowerCase();
  return (
    SOLUTION_TEMPLATES.find((template) => normalized.includes(template.domain)) ??
    SOLUTION_TEMPLATES[0]
  );
}

function createRequest(payload) {
  const template = payload.template ?? templateFromRequest(payload.request);
  const createdAt = nowIso();
  const workflow = WORKFLOW_STAGES.map((stage, index) => buildStageState(stage, index, 0));
  workflow[0].status = "in_progress";

  return {
    id: `req-${Math.random().toString(36).slice(2, 10)}`,
    title: payload.title || template.title,
    request: payload.request || template.request,
    mode: payload.mode || "full_solution",
    domain: payload.domain || template.domain,
    industry: payload.industry || template.domain,
    country: payload.country || "Australia",
    budget: payload.budget || "$0",
    timeline: payload.timeline || "TBD",
    stakeholders: payload.stakeholders || "",
    region: payload.region || "Australia",
    compliance: payload.compliance || "enterprise",
    attachments: payload.attachments || [],
    contextSources: payload.contextSources || [],
    selectedAgents: payload.selectedAgents || [],
    environment: payload.environment || "Production",
    surfaces: payload.surfaces?.length ? payload.surfaces : template.surfaces,
    templateId: template.id,
    stageIndex: 0,
    status: "active",
    createdAt,
    updatedAt: createdAt,
    approvals: [],
    artifacts: [
      {
        id: `art-${Math.random().toString(36).slice(2, 10)}`,
        kind: "intent-brief",
        title: "Intent brief",
        stage: "Intent Analysis",
        createdAt,
      },
    ],
    workflow,
    evidenceTrail: [],
  };
}

function seedState() {
  const first = createRequest({
    title: "Ride-hailing platform for Melbourne",
    request: "Build a ride-hailing platform for Melbourne.",
    mode: "full_solution",
    domain: "mobility",
    region: "Australia",
    surfaces: ["Rider app", "Driver app", "Operations dashboard", "Admin portal"],
    compliance: "high",
    template: SOLUTION_TEMPLATES[0],
  });

  return {
    activeRoleId: "platform-admin",
    environment: "Production",
    selectedWorkspace: "Solution Studio",
    selectedRequestId: first.id,
    activeTenantId: TENANTS[0].id,
    activeProjectId: PROJECTS[0].id,
    activeThreadId: COLLABORATION_THREADS[0].id,
    selectedKnowledgeNodeId: KNOWLEDGE_GRAPH[0].id,
    search: "",
    installedAgents: ["banking-agent", "healthcare-agent", "ride-hailing-agent"],
    connectedIntegrations: INTEGRATIONS.filter((integration) => integration.status === "connected").map(
      (integration) => integration.id,
    ),
    tenants: TENANTS,
    projects: PROJECTS,
    collaborationThreads: COLLABORATION_THREADS.map((thread, index) => ({
      ...thread,
      messages: [
        {
          id: `msg-${index + 1}`,
          author: "NovaCodePro",
          body: thread.message,
          at: createdAtMinus(index + 10),
        },
      ],
    })),
    knowledgeGraph: KNOWLEDGE_GRAPH,
    approvalObjects: [],
    agentTeams: [],
    eventBus: {
      domainEvents: 0,
      retryQueue: 0,
      deadLetterQueue: 0,
      projectionCheckpoints: 1,
    },
    automationRuns: [],
    enterpriseArchitectureFramework: ENTERPRISE_ARCHITECTURE_FRAMEWORK,
    erosManifest: EROS_MANIFEST,
    solutionRequests: [
      first,
      {
        ...createRequest({
          title: "Healthcare management system",
          request: "Build a hospital management system.",
          mode: "design",
          domain: "healthcare",
          region: "Australia",
          compliance: "very high",
          template: SOLUTION_TEMPLATES[1],
        }),
        stageIndex: 4,
        status: "review",
        workflow: WORKFLOW_STAGES.map((stage, index) => buildStageState(stage, index, 4)),
        approvals: [
          {
            id: "approval-architecture",
            gate: "Architecture Approval",
            by: "NovaTech Governance",
            at: createdAtMinus(1),
            evidence: "Architecture approved after controlled review.",
          },
        ],
        artifacts: [
          {
            id: "art-business",
            kind: "requirements",
            title: "Business requirements",
            stage: "Business Analysis",
            createdAt: createdAtMinus(2),
          },
          {
            id: "art-architecture",
            kind: "architecture",
            title: "Approved architecture",
            stage: "Architecture Approval",
            createdAt: createdAtMinus(1),
          },
        ],
      },
    ],
    auditTrail: [
      createAuditEvent({
        actor: "NovaID",
        action: "solution.request.created",
        service: "Solution Orchestrator Engine",
        subject: "Ride-hailing platform for Melbourne",
        evidence: "Intent brief stored in local solution repository.",
        detail: "Seeded solution request for enterprise demo.",
      }),
      createAuditEvent({
        actor: "NovaID",
        action: "solution.architecture.approved",
        service: "Human Review & Governance Engine",
        subject: "Healthcare management system",
        evidence: "Architecture approval recorded with governance evidence.",
        detail: "Seeded workflow at architecture approval gate.",
      }),
    ],
    evidenceBundles: [
      {
        id: "evidence-req-001",
        actor: "NovaID",
        action: "requirements.approved",
        timestamp: createdAtMinus(3),
        policy: "REQ-GOV-001",
        artifacts: ["art-business", "art-architecture"],
        hash: "ev-req-001",
        verified: true,
        summary: "Requirements and architecture evidence bundled for review.",
      },
      {
        id: "evidence-rel-001",
        actor: "NovaTech Governance",
        action: "release.prepared",
        timestamp: createdAtMinus(1),
        policy: "REL-PROD-001",
        artifacts: ["release-manifest", "test-report", "sbom"],
        hash: "ev-rel-001",
        verified: true,
        summary: "Release evidence bundle prepared for controlled promotion.",
      },
    ],
    riskRegister: [
      {
        id: "risk-deploy-001",
        title: "Unauthorized production access",
        likelihood: "medium",
        impact: "high",
        exposure: "medium",
        score: calculateRiskScore("medium", "high", "medium"),
        owner: "Security Team",
        treatment: ["MFA required", "Conditional access", "Audit monitoring"],
        status: "open",
      },
      {
        id: "risk-supply-001",
        title: "Supply chain dependency delay",
        likelihood: "medium",
        impact: "medium",
        exposure: "high",
        score: calculateRiskScore("medium", "medium", "high"),
        owner: "Platform Engineering",
        treatment: ["Secondary supplier", "Release buffer", "Dependency review"],
        status: "open",
      },
    ],
    approvalPolicies: [
      {
        id: "policy-prod-release",
        name: "Production Release",
        required: ["CTO", "Security Lead"],
        quorum: 2,
        timeout: "48h",
        escalation: "CEO",
      },
      {
        id: "policy-risk-acceptance",
        name: "Risk Acceptance",
        required: ["Risk Owner", "Security Lead"],
        quorum: 2,
        timeout: "24h",
        escalation: "CISO",
      },
    ],
    approvalRoutes: [
      {
        id: "route-prod-release",
        policyId: "policy-prod-release",
        subject: "NovaRide public pilot release",
        required: ["CTO", "Security Lead"],
        quorum: 2,
        timeout: "48h",
        escalation: "CEO",
        status: "ready",
        generatedAt: createdAtMinus(1),
      },
    ],
    digitalTwinScenarios: [
      {
        id: "twin-east-failure",
        title: "Region East Failure",
        expectedImpact: "8 services",
        revenueRisk: "$125,000",
        recovery: "23 minutes",
        affectedCustomers: "3,212",
        region: "East",
      },
    ],
    executiveInsights: [
      {
        id: "exec-q3-risk",
        question: "What threatens Q3 objectives?",
        risks: ["Deployment delays", "Vendor dependency", "Security remediation backlog"],
        recommendations: ["Increase staffing", "Prioritize release train", "Accelerate remediation"],
        generatedAt: createdAtMinus(2),
      },
    ],
    commandCenterSnapshots: [
      {
        id: "cmd-001",
        enterpriseHealth: "96",
        trustScore: "94",
        riskScore: "Medium",
        securityScore: "92",
        complianceScore: "98",
        deliveryScore: "89",
        incidentCount: 2,
        generatedAt: createdAtMinus(1),
      },
    ],
    commandHistory: [],
    neraArchitecture: NERA_ARCHITECTURE,
    uxOperatingSystem: UX_OPERATING_SYSTEM,
    uxComponentRegistry: UX_COMPONENT_REGISTRY,
    uxArtifacts: UX_ARTIFACT_SEED,
    uxEvidencePackages: [],
    uxosServiceRecords: [],
    uxosRuntimeServices: UXOS_RUNTIME_SERVICES,
    completionStandard: COMPLETION_STANDARD,
    completionDashboard: buildCompletionDashboard(),
    completionAssessment: {
      level: "Repository Complete",
      repositoryComplete: true,
      operationalVerified: false,
      governanceApproved: false,
      productionReady: false,
      gaAllowed: false,
      realPaymentsEnabled: false,
      missingProductionGates: [...COMPLETION_STANDARD.productionReadyGates],
    },
    operationalReadinessProgram: OPERATIONAL_READINESS_PROGRAM,
    operationalReadinessAssessment: {
      status: "OPERATIONAL_READINESS_BLOCKED",
      repositoryComplete: true,
      operationalVerified: false,
      governanceComplete: false,
      gaAllowed: false,
      realPaymentsEnabled: false,
    },
    uxReleaseReadiness: {
      status: "EVIDENCE_PENDING",
      gaAllowed: false,
      missing: ["PRR approval", "Executive approval", "Live production UX evidence"],
    },
    developerSurfaces: DEVELOPER_SURFACES,
  };
}

function createdAtMinus(minutes) {
  return new Date(Date.now() - minutes * 60_000).toISOString();
}

function loadState() {
  const base = seedState();
  if (typeof localStorage === "undefined") {
    return base;
  }
  const pickArray = (value, fallback) => (Array.isArray(value) ? value : fallback);
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return base;
    }
    const parsed = JSON.parse(raw);
    const parsedEnterpriseArchitectureFramework = parsed.enterpriseArchitectureFramework ?? {};
    const parsedEnterpriseArchitectureModels = parsedEnterpriseArchitectureFramework.models ?? {};
    const parsedErosManifest = parsed.erosManifest ?? {};
    return {
      ...base,
      ...parsed,
      solutionRequests: pickArray(parsed.solutionRequests, base.solutionRequests),
      auditTrail: pickArray(parsed.auditTrail, base.auditTrail),
      commandHistory: pickArray(parsed.commandHistory, base.commandHistory),
      tenants: pickArray(parsed.tenants, base.tenants),
      projects: pickArray(parsed.projects, base.projects),
      collaborationThreads: pickArray(parsed.collaborationThreads, base.collaborationThreads),
      knowledgeGraph: pickArray(parsed.knowledgeGraph, base.knowledgeGraph),
      approvalObjects: pickArray(parsed.approvalObjects, base.approvalObjects),
      agentTeams: pickArray(parsed.agentTeams, base.agentTeams),
      eventBus: pickArray(parsed.eventBus, base.eventBus),
      neraArchitecture: parsed.neraArchitecture ?? base.neraArchitecture,
      enterpriseArchitectureFramework: {
        ...base.enterpriseArchitectureFramework,
        ...parsedEnterpriseArchitectureFramework,
        models: {
          ...base.enterpriseArchitectureFramework.models,
          ...parsedEnterpriseArchitectureModels,
        },
      },
      erosManifest: {
        ...base.erosManifest,
        ...parsedErosManifest,
      },
      evidenceBundles: pickArray(parsed.evidenceBundles, base.evidenceBundles),
      riskRegister: pickArray(parsed.riskRegister, base.riskRegister),
      approvalPolicies: pickArray(parsed.approvalPolicies, base.approvalPolicies),
      approvalRoutes: pickArray(parsed.approvalRoutes, base.approvalRoutes),
      digitalTwinScenarios: pickArray(parsed.digitalTwinScenarios, base.digitalTwinScenarios),
      executiveInsights: pickArray(parsed.executiveInsights, base.executiveInsights),
      commandCenterSnapshots: pickArray(parsed.commandCenterSnapshots, base.commandCenterSnapshots),
      automationRuns: pickArray(parsed.automationRuns, base.automationRuns),
      connectedIntegrations: pickArray(parsed.connectedIntegrations, base.connectedIntegrations),
      installedAgents: pickArray(parsed.installedAgents, base.installedAgents),
      uxOperatingSystem: parsed.uxOperatingSystem ?? base.uxOperatingSystem,
      uxComponentRegistry: pickArray(parsed.uxComponentRegistry, base.uxComponentRegistry),
      uxArtifacts: pickArray(parsed.uxArtifacts, base.uxArtifacts),
      uxEvidencePackages: pickArray(parsed.uxEvidencePackages, base.uxEvidencePackages),
      uxosServiceRecords: pickArray(parsed.uxosServiceRecords, base.uxosServiceRecords),
      uxosRuntimeServices: pickArray(parsed.uxosRuntimeServices, base.uxosRuntimeServices),
      completionStandard: parsed.completionStandard ?? base.completionStandard,
      completionDashboard: parsed.completionDashboard ?? base.completionDashboard,
      completionAssessment: parsed.completionAssessment ?? base.completionAssessment,
      operationalReadinessProgram: parsed.operationalReadinessProgram ?? base.operationalReadinessProgram,
      operationalReadinessAssessment: parsed.operationalReadinessAssessment ?? base.operationalReadinessAssessment,
      uxReleaseReadiness: parsed.uxReleaseReadiness ?? base.uxReleaseReadiness,
      developerSurfaces: pickArray(parsed.developerSurfaces, base.developerSurfaces),
    };
  } catch {
    return base;
  }
}

function saveState(state) {
  if (typeof localStorage === "undefined") {
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function nextWorkflowIndex(request) {
  const current = request.stageIndex;
  return Math.min(current + 1, WORKFLOW_SEQUENCE.length - 1);
}

function withUpdatedRequest(state, requestId, updater) {
  const solutionRequests = state.solutionRequests.map((request) =>
    request.id === requestId ? updater(request) : request,
  );
  const selectedRequestId = state.selectedRequestId || requestId;
  return { ...state, solutionRequests, selectedRequestId };
}

function traceGraphPath(graph, startId, targetId) {
  if (!startId || !targetId || startId === targetId) {
    return [startId, targetId].filter(Boolean);
  }
  const visited = new Set([startId]);
  const queue = [[startId]];
  while (queue.length) {
    const path = queue.shift();
    const currentId = path[path.length - 1];
    const currentNode = graph.find((node) => node.id === currentId);
    if (!currentNode) {
      continue;
    }
    for (const nextId of currentNode.links || []) {
      if (visited.has(nextId)) {
        continue;
      }
      const nextPath = [...path, nextId];
      if (nextId === targetId) {
        return nextPath;
      }
      visited.add(nextId);
      queue.push(nextPath);
    }
  }
  return [startId, targetId];
}

function scaleRiskValue(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "critical") return 4;
  if (normalized === "high") return 3;
  if (normalized === "medium") return 2;
  if (normalized === "low") return 1;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
}

function calculateRiskScore(likelihood, impact, exposure) {
  return scaleRiskValue(likelihood) * scaleRiskValue(impact) * scaleRiskValue(exposure);
}

function createRuntime() {
  let state = loadState();
  const listeners = new Set();

  function emit(event) {
    if (event) {
      state = {
        ...state,
        auditTrail: [event, ...state.auditTrail].slice(0, 200),
      };
    }
    saveState(state);
    listeners.forEach((listener) => listener());
  }

  function appendAudit(payload) {
    return createAuditEvent(payload);
  }

  function setState(nextState) {
    state = nextState;
    saveState(state);
    listeners.forEach((listener) => listener());
  }

function createSolution(payload) {
    const request = createRequest(payload);
    const event = appendAudit({
      actor: "NovaID",
      action: "solution.request.created",
      service: "Solution Orchestrator Engine",
      subject: request.title,
      evidence: request.request,
      detail: "Solution request entered through Solution Studio.",
    });
    setState({
      ...state,
      solutionRequests: [request, ...state.solutionRequests],
      selectedRequestId: request.id,
      commandHistory: [request.request, ...state.commandHistory].slice(0, 30),
    });
    emit(event);
    return request;
  }

  function selectRequest(requestId) {
    setState({
      ...state,
      selectedRequestId: requestId,
    });
  }

  function switchTenant(tenantId) {
    const tenantProjects = state.projects.filter((project) => project.tenantId === tenantId);
    setState({
      ...state,
      activeTenantId: tenantId,
      activeProjectId: tenantProjects[0]?.id ?? state.activeProjectId,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workspace.tenant.switched",
        service: "Tenant Manager",
        subject: tenantId,
        evidence: `Tenant switched to ${tenantId}.`,
        detail: "Workspace context updated for the selected tenant.",
      }),
    );
  }

  function selectProject(projectId) {
    setState({
      ...state,
      activeProjectId: projectId,
    });
    const project = state.projects.find((item) => item.id === projectId);
    emit(
      appendAudit({
        actor: "NovaID",
        action: "project.selected",
        service: "Project Workspace",
        subject: project?.name || projectId,
        evidence: project?.solution || "Project selected from workspace catalog.",
        detail: "Project context activated in NovaCodePro.",
      }),
    );
  }

  function switchRole(roleId) {
    setState({
      ...state,
      activeRoleId: roleId,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workspace.role.switched",
        service: "Identity & Access",
        subject: roleId,
        evidence: `Role set to ${roleId}.`,
        detail: "Role-aware workspace assembly updated.",
      }),
    );
  }

  function setEnvironment(environment) {
    setState({
      ...state,
      environment,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workspace.environment.switched",
        service: "Environment Control",
        subject: environment,
        evidence: `Environment switched to ${environment}.`,
        detail: "Runtime context updated.",
      }),
    );
  }

  function installAgent(agentId) {
    if (state.installedAgents.includes(agentId)) {
      return;
    }
    setState({
      ...state,
      installedAgents: [agentId, ...state.installedAgents],
    });
    const agent = AGENT_MARKETPLACE.find((item) => item.id === agentId);
    emit(
      appendAudit({
        actor: "NovaID",
        action: "agent.installed",
        service: "Plugin Marketplace",
        subject: agent?.title || agentId,
        evidence: agent?.api || "No API metadata",
        detail: "Agent enabled in the active enterprise workspace.",
      }),
    );
  }

  function installIntegration(integrationId) {
    if (state.connectedIntegrations.includes(integrationId)) {
      return;
    }
    const integration = INTEGRATIONS.find((item) => item.id === integrationId);
    setState({
      ...state,
      connectedIntegrations: [integrationId, ...state.connectedIntegrations],
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "integration.connected",
        service: "Integration Hub",
        subject: integration?.name || integrationId,
        evidence: integration?.purpose || "Integration enabled.",
        detail: "External service connected to the enterprise platform.",
      }),
    );
  }

  function createProject(payload) {
    const project = {
      id: `project-${Math.random().toString(36).slice(2, 10)}`,
      name: payload.name,
      tenantId: payload.tenantId || state.activeTenantId,
      status: payload.status || "Discovery",
      owner: payload.owner || "NovaCodePro",
      solution: payload.solution || "Generated solution",
      region: payload.region || "Australia",
      budget: payload.budget || "$0",
    };
    setState({
      ...state,
      projects: [project, ...state.projects],
      activeProjectId: project.id,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "project.created",
        service: "Project Workspace",
        subject: project.name,
        evidence: project.solution,
        detail: "Project created through NovaCodePro governance flow.",
      }),
    );
  }

  function postComment(threadId, body) {
    const thread = state.collaborationThreads.find((item) => item.id === threadId);
    if (!thread) {
      return;
    }
    const updatedThread = {
      ...thread,
      messages: [
        {
          id: `msg-${Math.random().toString(36).slice(2, 10)}`,
          author: "NovaCodePro",
          body,
          at: nowIso(),
        },
        ...thread.messages,
      ],
      state: "active",
    };
    setState({
      ...state,
      activeThreadId: threadId,
      collaborationThreads: state.collaborationThreads.map((item) =>
        item.id === threadId ? updatedThread : item,
      ),
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "collaboration.comment.posted",
        service: "Collaboration Service",
        subject: thread.scope,
        evidence: body,
        detail: "Collaborative note captured and synchronized with the workspace.",
      }),
    );
  }

  function focusKnowledgeNode(nodeId) {
    setState({
      ...state,
      selectedKnowledgeNodeId: nodeId,
    });
    const node = state.knowledgeGraph.find((item) => item.id === nodeId);
    emit(
      appendAudit({
        actor: "NovaID",
        action: "knowledge.graph.focused",
        service: "Knowledge Graph",
        subject: node?.label || nodeId,
        evidence: node?.links?.join(", ") || "Knowledge node focused.",
        detail: "Enterprise knowledge graph inspected from the workspace.",
      }),
    );
  }

  function queryKnowledgeGraph(term) {
    const normalized = String(term || "").trim().toLowerCase();
    const matches = normalized
      ? state.knowledgeGraph.filter((node) => {
          const haystack = [node.id, node.label, node.type, node.domain, node.owner, node.evidence]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();
          return haystack.includes(normalized);
        })
      : state.knowledgeGraph;
    emit(
      appendAudit({
        actor: "NovaID",
        action: "knowledge.graph.queried",
        service: "Knowledge Graph",
        subject: normalized || "all nodes",
        evidence: matches.map((node) => node.label).join(", ") || "No match",
        detail: "Semantic discovery query executed against the enterprise graph.",
      }),
    );
    return matches;
  }

  function traceKnowledgePath(startId, targetId) {
    const path = traceGraphPath(state.knowledgeGraph, startId, targetId);
    emit(
      appendAudit({
        actor: "NovaID",
        action: "knowledge.graph.path.traced",
        service: "Knowledge Graph",
        subject: `${startId} -> ${targetId}`,
        evidence: path.join(" -> "),
        detail: "Traceability path reconstructed across the enterprise lifecycle.",
      }),
    );
    return path;
  }

  function createEvidenceBundle(input = {}) {
    const bundle = {
      id: `evidence-${Math.random().toString(36).slice(2, 10)}`,
      actor: input.actor || "NovaID",
      action: input.action || "evidence.created",
      timestamp: nowIso(),
      policy: input.policy || "UNSPECIFIED",
      artifacts: input.artifacts || [],
      hash: `hash-${Math.random().toString(36).slice(2, 10)}`,
      verified: true,
      summary: input.summary || "Immutable evidence bundle created from the shared interaction model.",
    };
    setState({
      ...state,
      evidenceBundles: [bundle, ...state.evidenceBundles],
    });
    emit(
      appendAudit({
        actor: bundle.actor,
        action: bundle.action,
        service: "Evidence Engine",
        subject: bundle.policy,
        evidence: bundle.artifacts.join(", ") || bundle.hash,
        detail: bundle.summary,
      }),
    );
    return bundle;
  }

  function evaluateRisk(input = {}) {
    const risk = {
      id: `risk-${Math.random().toString(36).slice(2, 10)}`,
      title: input.title || "Operational risk",
      likelihood: input.likelihood || "medium",
      impact: input.impact || "medium",
      exposure: input.exposure || "medium",
      score: calculateRiskScore(input.likelihood || "medium", input.impact || "medium", input.exposure || "medium"),
      owner: input.owner || "Risk Team",
      treatment: input.treatment || ["Review controls", "Attach evidence", "Escalate if needed"],
      status: input.status || "open",
    };
    setState({
      ...state,
      riskRegister: [risk, ...state.riskRegister],
    });
    emit(
      appendAudit({
        actor: "Risk Engine",
        action: "risk.evaluated",
        service: "Risk Engine",
        subject: risk.title,
        evidence: `${risk.likelihood} × ${risk.impact} × ${risk.exposure} = ${risk.score}`,
        detail: `Risk owned by ${risk.owner}.`,
      }),
    );
    return risk;
  }

  function routeApprovalPolicy(policyId, subject = "workflow", context = {}) {
    const policy = state.approvalPolicies.find((item) => item.id === policyId) ?? state.approvalPolicies[0];
    const route = {
      id: `route-${Math.random().toString(36).slice(2, 10)}`,
      policyId: policy?.id || policyId,
      subject,
      required: policy?.required || [],
      quorum: policy?.quorum || 1,
      timeout: policy?.timeout || "24h",
      escalation: policy?.escalation || "CEO",
      status: "ready",
      generatedAt: nowIso(),
      context,
    };
    setState({
      ...state,
      approvalRoutes: [route, ...state.approvalRoutes],
    });
    emit(
      appendAudit({
        actor: "Policy Engine",
        action: "approval.policy.routed",
        service: "Policy Engine",
        subject,
        evidence: `${route.required.join(", ")} | quorum ${route.quorum}`,
        detail: `Policy ${route.policyId} routed for authorization.`,
      }),
    );
    return route;
  }

  function simulateDigitalTwinScenario(input = {}) {
    const scenario = {
      id: `twin-${Math.random().toString(36).slice(2, 10)}`,
      title: input.title || "Operational scenario",
      expectedImpact: input.expectedImpact || "1 service",
      revenueRisk: input.revenueRisk || "$0",
      recovery: input.recovery || "5 minutes",
      affectedCustomers: input.affectedCustomers || "0",
      region: input.region || "Global",
      generatedAt: nowIso(),
    };
    setState({
      ...state,
      digitalTwinScenarios: [scenario, ...state.digitalTwinScenarios],
    });
    emit(
      appendAudit({
        actor: "Digital Twin Engine",
        action: "digital.twin.scenario.simulated",
        service: "Digital Twin Engine",
        subject: scenario.title,
        evidence: `${scenario.region} · ${scenario.expectedImpact}`,
        detail: `Estimated recovery ${scenario.recovery} for ${scenario.affectedCustomers} customers.`,
      }),
    );
    return scenario;
  }

  function askExecutiveAI(question) {
    const risks = state.riskRegister.slice(0, 3).map((risk) => risk.title);
    const recommendations = [
      "Increase operational capacity on the critical path.",
      "Prioritize the highest-scoring risk treatment.",
      "Maintain gated approvals for production changes.",
    ];
    const insight = {
      id: `exec-${Math.random().toString(36).slice(2, 10)}`,
      question,
      risks,
      recommendations,
      generatedAt: nowIso(),
    };
    setState({
      ...state,
      executiveInsights: [insight, ...state.executiveInsights],
    });
    emit(
      appendAudit({
        actor: "Executive AI Platform",
        action: "executive.ai.advised",
        service: "Executive AI Platform",
        subject: question,
        evidence: recommendations.join(" | "),
        detail: "Advisory output only. No authority to approve or deploy.",
      }),
    );
    return insight;
  }

  function refreshCommandCenter() {
    const openRisks = state.riskRegister.filter((risk) => risk.status === "open").length;
    const incidentCount = state.commandCenterSnapshots[0]?.incidentCount ?? 0;
    const snapshot = {
      id: `cmd-${Math.random().toString(36).slice(2, 10)}`,
      enterpriseHealth: String(Math.max(84, 100 - openRisks * 3)),
      trustScore: String(Math.max(88, 100 - openRisks * 2)),
      riskScore: openRisks > 2 ? "High" : openRisks > 0 ? "Medium" : "Low",
      securityScore: String(Math.max(90, 98 - openRisks)),
      complianceScore: "98",
      deliveryScore: String(Math.max(82, 92 - state.automationRuns.length)),
      incidentCount,
      generatedAt: nowIso(),
    };
    setState({
      ...state,
      commandCenterSnapshots: [snapshot, ...state.commandCenterSnapshots],
    });
    emit(
      appendAudit({
        actor: "Command Service",
        action: "command.center.refreshed",
        service: "Command Service",
        subject: "Enterprise command center",
        evidence: `${snapshot.enterpriseHealth}/${snapshot.trustScore}/${snapshot.riskScore}`,
        detail: "Mission-control snapshot recalculated from shared enterprise services.",
      }),
    );
    return snapshot;
  }

  function runEnterpriseInteraction(input = {}) {
    const subject = input.subject || "Enterprise request";
    const policy = state.approvalPolicies.find((item) => item.id === (input.policyId || "policy-prod-release")) ?? state.approvalPolicies[0];
    const evidence = {
      id: `evidence-${Math.random().toString(36).slice(2, 10)}`,
      actor: input.actor || "NovaID",
      action: input.action || "enterprise.interaction.routed",
      timestamp: nowIso(),
      policy: policy?.id || "UNSPECIFIED",
      artifacts: input.artifacts || [],
      hash: `hash-${Math.random().toString(36).slice(2, 10)}`,
      verified: true,
      summary: input.summary || `Evidence bundle generated for ${subject}.`,
    };
    const risk = {
      id: `risk-${Math.random().toString(36).slice(2, 10)}`,
      title: input.riskTitle || `${subject} risk`,
      likelihood: input.likelihood || "medium",
      impact: input.impact || "medium",
      exposure: input.exposure || "medium",
      score: calculateRiskScore(
        input.likelihood || "medium",
        input.impact || "medium",
        input.exposure || "medium",
      ),
      owner: input.owner || "Risk Team",
      treatment: input.treatment || ["Review controls", "Attach evidence", "Route approval"],
      status: "open",
    };
    const route = {
      id: `route-${Math.random().toString(36).slice(2, 10)}`,
      policyId: policy?.id || "policy-prod-release",
      subject,
      required: policy?.required || [],
      quorum: policy?.quorum || 1,
      timeout: policy?.timeout || "24h",
      escalation: policy?.escalation || "CEO",
      status: "ready",
      generatedAt: nowIso(),
      context: {
        environment: input.environment || "production",
        region: input.region || "global",
      },
    };
    const twin = {
      id: `twin-${Math.random().toString(36).slice(2, 10)}`,
      title: input.scenarioTitle || `${subject} scenario`,
      expectedImpact: input.expectedImpact || "4 services",
      revenueRisk: input.revenueRisk || "$0",
      recovery: input.recovery || "15 minutes",
      affectedCustomers: input.affectedCustomers || "0",
      region: input.region || "Global",
      generatedAt: nowIso(),
    };
    const insight = {
      id: `exec-${Math.random().toString(36).slice(2, 10)}`,
      question: input.question || `What threatens ${subject}?`,
      risks: [risk.title, ...state.riskRegister.slice(0, 2).map((item) => item.title)],
      recommendations: input.recommendations || [
        "Increase operational capacity on the critical path.",
        "Prioritize the highest-scoring risk treatment.",
        "Maintain gated approvals for production changes.",
      ],
      generatedAt: nowIso(),
    };
    const openRisks = [risk, ...state.riskRegister].filter((item) => item.status === "open").length;
    const snapshot = {
      id: `cmd-${Math.random().toString(36).slice(2, 10)}`,
      enterpriseHealth: String(Math.max(84, 100 - openRisks * 3)),
      trustScore: String(Math.max(88, 100 - openRisks * 2)),
      riskScore: openRisks > 2 ? "High" : openRisks > 0 ? "Medium" : "Low",
      securityScore: String(Math.max(90, 98 - openRisks)),
      complianceScore: "98",
      deliveryScore: String(Math.max(82, 92 - state.automationRuns.length)),
      incidentCount: state.commandCenterSnapshots[0]?.incidentCount ?? 0,
      generatedAt: nowIso(),
    };
    const approvalObject = {
      id: `approval-${Math.random().toString(36).slice(2, 10)}`,
      solutionId: subject,
      approvalType: "solution_review",
      status: route.required.length ? "REVIEWED" : "APPROVED",
      riskLevel: risk.score >= 18 ? "HIGH" : risk.score >= 8 ? "MEDIUM" : "LOW",
      approver: "NovaTech Governance",
      comments: ["Review package assembled from request, agents, and evidence."],
      approvedAt: route.required.length ? "" : nowIso(),
      version: 1,
      knowledgeCreated: route.required.length === 0,
      executionEnabled: route.required.length === 0,
      createdAt: nowIso(),
      updatedAt: nowIso(),
    };
    const agentTeam = {
      id: `team-${Math.random().toString(36).slice(2, 10)}`,
      subject,
      members: [
        "Architect Agent",
        "Developer Agent",
        "QA Agent",
        "Security Agent",
        "Compliance Agent",
      ].filter((item, index) => index < 3 || approvalObject.riskLevel !== "LOW"),
      stage: "review",
      updatedAt: nowIso(),
    };
    const eventBus = {
      domainEvents: state.auditTrail.length + 4,
      retryQueue: state.eventBus?.retryQueue ?? 0,
      deadLetterQueue: state.eventBus?.deadLetterQueue ?? 0,
      projectionCheckpoints: state.eventBus?.projectionCheckpoints ?? 1,
    };
    setState({
      ...state,
      evidenceBundles: [evidence, ...state.evidenceBundles],
      riskRegister: [risk, ...state.riskRegister],
      approvalRoutes: [route, ...state.approvalRoutes],
      approvalObjects: [approvalObject, ...state.approvalObjects],
      agentTeams: [agentTeam, ...state.agentTeams],
      digitalTwinScenarios: [twin, ...state.digitalTwinScenarios],
      executiveInsights: [insight, ...state.executiveInsights],
      commandCenterSnapshots: [snapshot, ...state.commandCenterSnapshots],
      eventBus,
    });
    emit(
      appendAudit({
        actor: evidence.actor,
        action: evidence.action,
        service: "Evidence Engine",
        subject,
        evidence: evidence.hash,
        detail: evidence.summary,
      }),
    );
    emit(
      appendAudit({
        actor: "Risk Engine",
        action: "risk.evaluated",
        service: "Risk Engine",
        subject: risk.title,
        evidence: `${risk.likelihood} × ${risk.impact} × ${risk.exposure} = ${risk.score}`,
        detail: `Risk owned by ${risk.owner}.`,
      }),
    );
    emit(
      appendAudit({
        actor: "Policy Engine",
        action: "approval.policy.routed",
        service: "Policy Engine",
        subject,
        evidence: `${route.required.join(", ")} | quorum ${route.quorum}`,
        detail: `Policy ${route.policyId} routed for authorization.`,
      }),
    );
    emit(
      appendAudit({
        actor: "Digital Twin Engine",
        action: "digital.twin.scenario.simulated",
        service: "Digital Twin Engine",
        subject: twin.title,
        evidence: `${twin.region} · ${twin.expectedImpact}`,
        detail: `Estimated recovery ${twin.recovery} for ${twin.affectedCustomers} customers.`,
      }),
    );
    emit(
      appendAudit({
        actor: "Executive AI Platform",
        action: "executive.ai.advised",
        service: "Executive AI Platform",
        subject: insight.question,
        evidence: insight.recommendations.join(" | "),
        detail: "Advisory output only. No authority to approve or deploy.",
      }),
    );
    emit(
      appendAudit({
        actor: "Command Service",
        action: "command.center.refreshed",
        service: "Command Service",
        subject: "Enterprise command center",
        evidence: `${snapshot.enterpriseHealth}/${snapshot.trustScore}/${snapshot.riskScore}`,
        detail: "Mission-control snapshot recalculated from shared enterprise services.",
      }),
    );
    return { evidence, risk, route, twin, insight, snapshot };
  }

  function runAutomationTemplate(templateId) {
    const template = AUTOMATION_TEMPLATES.find((item) => item.id === templateId);
    if (!template) {
      return;
    }
    const run = {
      id: `run-${Math.random().toString(36).slice(2, 10)}`,
      templateId: template.id,
      title: template.title,
      stages: template.stages,
      status: "queued",
      createdAt: nowIso(),
    };
    setState({
      ...state,
      automationRuns: [run, ...state.automationRuns],
      commandHistory: [template.title, ...state.commandHistory].slice(0, 30),
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "automation.template.run",
        service: "Workflow Engine",
        subject: template.title,
        evidence: template.stages.join(" → "),
        detail: "Reusable automation template started from the enterprise workspace.",
      }),
    );
  }

  function advanceWorkflow(requestId) {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    if (!currentStage) {
      return;
    }
    if (currentStage.kind === "human") {
      emit(
        appendAudit({
          actor: "NovaID",
          action: `${currentStage.id}.waiting-approval`,
          service: currentStage.service,
          subject: request.title,
          evidence: currentStage.output,
          detail: "Human approval gate is required before this request can advance.",
        }),
      );
      return;
    }

    const nextIndex = nextWorkflowIndex(request);
    const nextStage = request.workflow[nextIndex];

    const updatedRequest = {
      ...request,
      stageIndex: nextIndex,
      updatedAt: nowIso(),
      status: nextStage?.kind === "human" ? "waiting-approval" : nextIndex === WORKFLOW_SEQUENCE.length - 1 ? "operating" : "active",
      workflow: request.workflow.map((stage, index) =>
        index < nextIndex
          ? { ...stage, status: "completed" }
          : index === nextIndex
            ? { ...stage, status: nextStage?.kind === "human" ? "waiting-approval" : "in_progress" }
            : { ...stage, status: "pending" },
      ),
      artifacts: [
        ...request.artifacts,
        {
          id: `art-${Math.random().toString(36).slice(2, 10)}`,
          kind: currentStage.output,
          title: currentStage.output,
          stage: currentStage.label,
          createdAt: nowIso(),
        },
      ],
    };

    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });

    emit(
      appendAudit({
        actor: "Solution Engine",
        action: `${currentStage.id}.completed`,
        service: currentStage.service,
        subject: request.title,
        evidence: currentStage.output,
        detail: `Workflow advanced to ${nextStage ? nextStage.label : "complete"}.`,
      }),
    );
  }

  function approveGate(requestId, note = "Approved by governance.") {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    if (!currentStage || currentStage.kind !== "human") {
      return;
    }

    const nextIndex = nextWorkflowIndex(request);
    const nextStage = request.workflow[nextIndex];
    const updatedWorkflow = request.workflow.map((stage, index) =>
      index < request.stageIndex
        ? { ...stage, status: "completed" }
        : index === request.stageIndex
          ? { ...stage, status: "completed" }
          : index === nextIndex
            ? { ...stage, status: nextStage?.kind === "human" ? "waiting-approval" : "in_progress" }
            : { ...stage, status: "pending" },
    );

    const updatedRequest = {
      ...request,
      stageIndex: nextIndex,
      updatedAt: nowIso(),
      status: nextIndex === WORKFLOW_SEQUENCE.length - 1 ? "operating" : "active",
      approvals: [
        ...request.approvals,
        {
          id: `approval-${Math.random().toString(36).slice(2, 10)}`,
          gate: currentStage.label,
          by: "NovaTech Governance",
          at: nowIso(),
          evidence: note,
        },
      ],
      workflow: updatedWorkflow,
      artifacts: [
        ...request.artifacts,
        {
          id: `art-${Math.random().toString(36).slice(2, 10)}`,
          kind: "approval",
          title: `${currentStage.label} approved`,
          stage: currentStage.label,
          createdAt: nowIso(),
        },
      ],
    };

    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });

    emit(
      appendAudit({
        actor: "NovaTech Governance",
        action: `${currentStage.id}.approved`,
        service: currentStage.service,
        subject: request.title,
        evidence: note,
        detail: `Human gate approved and workflow advanced to ${nextStage ? nextStage.label : "complete"}.`,
      }),
    );
  }

  function pauseWorkflow(requestId, note = "Paused by operator.") {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    const updatedRequest = {
      ...request,
      status: "paused",
      updatedAt: nowIso(),
      workflow: request.workflow.map((stage, index) =>
        index === request.stageIndex ? { ...stage, status: "paused" } : stage,
      ),
      evidenceTrail: [
        ...request.evidenceTrail,
        {
          at: nowIso(),
          action: "paused",
          note,
        },
      ],
    };
    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workflow.paused",
        service: "Workflow Engine",
        subject: request.title,
        evidence: currentStage?.label || "workflow",
        detail: note,
      }),
    );
  }

  function resumeWorkflow(requestId, note = "Resumed by operator.") {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    const activeStatus = currentStage?.kind === "human" ? "waiting-approval" : "active";
    const updatedRequest = {
      ...request,
      status: activeStatus,
      updatedAt: nowIso(),
      workflow: request.workflow.map((stage, index) =>
        index === request.stageIndex
          ? { ...stage, status: currentStage?.kind === "human" ? "waiting-approval" : "in_progress" }
          : stage,
      ),
      evidenceTrail: [
        ...request.evidenceTrail,
        {
          at: nowIso(),
          action: "resumed",
          note,
        },
      ],
    };
    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workflow.resumed",
        service: "Workflow Engine",
        subject: request.title,
        evidence: currentStage?.label || "workflow",
        detail: note,
      }),
    );
  }

  function retryWorkflow(requestId, note = "Retry requested by operator.") {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    const updatedRequest = {
      ...request,
      status: currentStage?.kind === "human" ? "waiting-approval" : "active",
      retries: (request.retries || 0) + 1,
      updatedAt: nowIso(),
      workflow: request.workflow.map((stage, index) =>
        index === request.stageIndex
          ? { ...stage, status: currentStage?.kind === "human" ? "waiting-approval" : "in_progress" }
          : stage,
      ),
      evidenceTrail: [
        ...request.evidenceTrail,
        {
          at: nowIso(),
          action: "retried",
          note,
        },
      ],
    };
    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "workflow.retried",
        service: "Workflow Engine",
        subject: request.title,
        evidence: currentStage?.label || "workflow",
        detail: note,
      }),
    );
  }

  function rejectWorkflow(requestId, note = "Rejected by governance.") {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const currentStage = request.workflow[request.stageIndex];
    const updatedRequest = {
      ...request,
      status: "rejected",
      updatedAt: nowIso(),
      workflow: request.workflow.map((stage, index) =>
        index === request.stageIndex ? { ...stage, status: "rejected" } : stage,
      ),
      evidenceTrail: [
        ...request.evidenceTrail,
        {
          at: nowIso(),
          action: "rejected",
          note,
        },
      ],
    };
    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? updatedRequest : item)),
      selectedRequestId: requestId,
    });
    emit(
      appendAudit({
        actor: "NovaTech Governance",
        action: "workflow.rejected",
        service: "Workflow Engine",
        subject: request.title,
        evidence: currentStage?.label || "workflow",
        detail: note,
      }),
    );
  }

  function attachArtifact(requestId, artifact) {
    const request = state.solutionRequests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    const nextRequest = {
      ...request,
      artifacts: [artifact, ...request.artifacts],
      updatedAt: nowIso(),
    };
    setState({
      ...state,
      solutionRequests: state.solutionRequests.map((item) => (item.id === requestId ? nextRequest : item)),
      selectedRequestId: requestId,
    });
    emit(
      appendAudit({
        actor: "NovaCodePro",
        action: "artifact.archived",
        service: "Artifact Repository",
        subject: artifact.title,
        evidence: artifact.kind,
        detail: "Artifact stored and versioned in the workspace repository.",
      }),
    );
  }

  function createUxArtifact(input = {}) {
    const artifact = {
      id: `uxart-${Math.random().toString(36).slice(2, 10)}`,
      artifact: input.artifact || input.title || "New UX artifact",
      artifactType: input.artifactType || input.artifact_type || "design_artifact",
      studio: input.studio || "UX Governance Center",
      owner: input.owner || "NovaCodePro UX",
      approvalState: input.approvalState || "DRAFT",
      version: input.version || "v1",
      evidence: Array.isArray(input.evidence) ? input.evidence : [],
      traceability: input.traceability || {},
      createdAt: nowIso(),
    };
    setState({
      ...state,
      uxArtifacts: [artifact, ...state.uxArtifacts],
    });
    emit(
      appendAudit({
        actor: "NovaCodePro",
        action: "ux.artifact.created",
        service: "UX Governance Center",
        subject: artifact.artifact,
        evidence: artifact.version,
        detail: "UX artifact captured with owner, version, evidence, and traceability.",
      }),
    );
    return artifact;
  }

  function attachUxEvidence(artifactId, evidenceRef = "ux-evidence.yaml") {
    const artifact = state.uxArtifacts.find((item) => item.id === artifactId);
    if (!artifact) {
      return null;
    }
    const evidence = Array.from(new Set([...(artifact.evidence || []), evidenceRef]));
    const updatedArtifact = { ...artifact, evidence };
    const evidencePackage = {
      id: `uxevidence-${Math.random().toString(36).slice(2, 10)}`,
      artifactId,
      artifact: artifact.artifact,
      status: "EVIDENCE_CAPTURED",
      evidence,
      createdAt: nowIso(),
    };
    setState({
      ...state,
      uxArtifacts: state.uxArtifacts.map((item) => (item.id === artifactId ? updatedArtifact : item)),
      uxEvidencePackages: [evidencePackage, ...state.uxEvidencePackages],
    });
    emit(
      appendAudit({
        actor: "NovaTrust",
        action: "ux.evidence.attached",
        service: "Evidence Studio",
        subject: artifact.artifact,
        evidence: evidenceRef,
        detail: "UX evidence package linked to a governed design artifact.",
      }),
    );
    return evidencePackage;
  }

  function assessUxReleaseReadiness() {
    const requiredTypes = ["requirement", "prototype", "accessibility_review", "implementation_verification"];
    const missingTypes = requiredTypes.filter(
      (type) => !state.uxArtifacts.some((artifact) => artifact.artifactType === type),
    );
    const evidenceMissing = state.uxArtifacts.filter((artifact) => !(artifact.evidence || []).length);
    const readiness = {
      status: missingTypes.length || evidenceMissing.length ? "EVIDENCE_PENDING" : "READY_FOR_PRR_APPROVAL",
      gaAllowed: false,
      realPaymentsEnabled: false,
      artifactCount: state.uxArtifacts.length,
      evidencePackageCount: state.uxEvidencePackages.length,
      missing: [
        ...missingTypes.map((type) => `Missing ${type}`),
        ...evidenceMissing.map((artifact) => `Evidence pending: ${artifact.artifact}`),
        "PRR approval",
        "Executive approval",
      ],
      assessedAt: nowIso(),
    };
    setState({
      ...state,
      uxReleaseReadiness: readiness,
    });
    emit(
      appendAudit({
        actor: "NovaCodePro",
        action: "ux.release.assessed",
        service: "UX Verification Center",
        subject: "Production UX release",
        evidence: readiness.status,
        detail: "UX release readiness assessed while preserving PRR and executive approval gates.",
      }),
    );
    return readiness;
  }

  function recordUxosService(kind, input = {}) {
    const record = {
      id: `uxos-${Math.random().toString(36).slice(2, 10)}`,
      kind,
      subject: input.subject || kind,
      provider: input.provider || "",
      status: input.status || "EVIDENCE_PENDING",
      operationalComplete: false,
      gaAllowed: false,
      evidence: Array.isArray(input.evidence) ? input.evidence : [],
      createdAt: nowIso(),
    };
    setState({
      ...state,
      uxosServiceRecords: [record, ...state.uxosServiceRecords],
    });
    emit(
      appendAudit({
        actor: "NovaCodePro",
        action: `${kind}.recorded`,
        service: "UXOS Service Fabric",
        subject: record.subject,
        evidence: record.status,
        detail: "UXOS service record captured; live operational completion remains evidence-gated.",
      }),
    );
    return record;
  }

  function evaluateCompletionState(input = {}) {
    const gates = input.productionReadyGates || {};
    const repositoryComplete = Boolean(input.repositoryComplete);
    const operationalVerified = Boolean(input.operationalVerified);
    const governanceApproved = Boolean(input.governanceApproved);
    const productionReady = Boolean(
      repositoryComplete &&
        operationalVerified &&
        governanceApproved &&
        COMPLETION_STANDARD.productionReadyGates.every((gate) => gates[gate] === true),
    );
    const gaAllowed = Boolean(productionReady && input.executiveAuthorized === true);
    const assessment = {
      level: gaAllowed
        ? "General Availability"
        : productionReady
          ? "Production Ready"
          : governanceApproved
            ? "Governance Approved"
            : operationalVerified
              ? "Operationally Verified"
              : repositoryComplete
                ? "Repository Complete"
                : "Incomplete",
      repositoryComplete,
      operationalVerified,
      governanceApproved,
      productionReady,
      gaAllowed,
      realPaymentsEnabled: false,
      missingProductionGates: COMPLETION_STANDARD.productionReadyGates.filter((gate) => gates[gate] !== true),
      evaluatedAt: nowIso(),
    };
    setState({
      ...state,
      completionAssessment: assessment,
    });
    emit(
      appendAudit({
        actor: "NovaCodePro",
        action: "completion.standard.evaluated",
        service: "Enterprise Completion Dashboard",
        subject: assessment.level,
        evidence: gaAllowed ? "GA_ALLOWED" : "GA_BLOCKED",
        detail: "Completion evaluated across repository, operational, and governance dimensions without enabling real payments.",
      }),
    );
    return assessment;
  }

  function evaluateOperationalReadiness(input = {}) {
    const evidence = input.evidence || {};
    const approvals = input.approvals || {};
    const paymentEvidence = input.paymentEvidence || {};
    const requiredEvidence = [
      "designSync",
      "visualRegression",
      "accessibility",
      "openTelemetry",
      "analytics",
      "digitalUxTwin",
      "automatedPrr",
    ];
    const requiredApprovals = ["ux", "engineering", "security", "operations", "compliance", "prr", "executive"];
    const operationalVerified = requiredEvidence.every((key) => evidence[key] === "PASS");
    const governanceComplete = requiredApprovals.every((key) => approvals[key] === "APPROVED");
    const paymentVerified = OPERATIONAL_READINESS_PROGRAM.paymentActivation.requirements.every(
      (key) => paymentEvidence[key] === "PASS",
    );
    const gaAllowed = Boolean(operationalVerified && governanceComplete);
    const assessment = {
      status: gaAllowed ? "PRODUCTION_OPERATION_ALLOWED" : "OPERATIONAL_READINESS_BLOCKED",
      repositoryComplete: true,
      operationalVerified,
      governanceComplete,
      gaAllowed,
      realPaymentsEnabled: Boolean(gaAllowed && paymentVerified),
      missingEvidence: requiredEvidence.filter((key) => evidence[key] !== "PASS"),
      missingApprovals: requiredApprovals.filter((key) => approvals[key] !== "APPROVED"),
      missingPaymentEvidence: OPERATIONAL_READINESS_PROGRAM.paymentActivation.requirements.filter(
        (key) => paymentEvidence[key] !== "PASS",
      ),
      evaluatedAt: nowIso(),
    };
    setState({
      ...state,
      operationalReadinessAssessment: assessment,
    });
    emit(
      appendAudit({
        actor: "NovaCodePro",
        action: "operational.readiness.evaluated",
        service: "Operational Readiness Program",
        subject: assessment.status,
        evidence: assessment.realPaymentsEnabled ? "PAYMENTS_ALLOWED" : "PAYMENTS_BLOCKED",
        detail: "Operational readiness evaluated with separate live evidence, governance, and payment activation gates.",
      }),
    );
    return assessment;
  }

  function runCommand(command) {
    setState({
      ...state,
      commandHistory: [command, ...state.commandHistory].slice(0, 30),
    });
    emit(
      appendAudit({
        actor: "NovaID",
        action: "command.executed",
        service: "Universal Command Palette",
        subject: command,
        evidence: "Command captured in workspace history.",
        detail: "Natural-language command executed against the platform shell.",
      }),
    );
  }

  return {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    createSolution,
    selectRequest,
    switchTenant,
    selectProject,
    switchRole,
    setEnvironment,
    installAgent,
    installIntegration,
    createProject,
    postComment,
    focusKnowledgeNode,
    queryKnowledgeGraph,
    traceKnowledgePath,
    createEvidenceBundle,
    evaluateRisk,
    routeApprovalPolicy,
    simulateDigitalTwinScenario,
    askExecutiveAI,
    refreshCommandCenter,
    runEnterpriseInteraction,
    runAutomationTemplate,
    advanceWorkflow,
    approveGate,
    pauseWorkflow,
    resumeWorkflow,
    retryWorkflow,
    rejectWorkflow,
    attachArtifact,
    createUxArtifact,
    attachUxEvidence,
    assessUxReleaseReadiness,
    recordUxosService,
    evaluateCompletionState,
    evaluateOperationalReadiness,
    runCommand,
  };
}

export const createPlatformRuntime = createRuntime;
export const platformRuntime = createRuntime();

export {
  AGENT_MARKETPLACE,
  AUTOMATION_TEMPLATES,
  COLLABORATION_THREADS,
  DEVELOPER_SURFACES,
  INTEGRATIONS,
  ENTERPRISE_ARCHITECTURE_FRAMEWORK,
  KNOWLEDGE_GRAPH,
  NEAF_MODEL,
  EROS_MANIFEST,
  COMPLETION_STANDARD,
  OPERATIONAL_READINESS_PROGRAM,
  UX_OPERATING_SYSTEM,
  UX_COMPONENT_REGISTRY,
  UXOS_RUNTIME_SERVICES,
  PLATFORM_CENTERS,
  PROJECTS,
  SERVICE_CATALOG,
  SOLUTION_TEMPLATES,
  TENANTS,
  WORKFLOW_SEQUENCE,
  WORKFLOW_STAGES,
};
