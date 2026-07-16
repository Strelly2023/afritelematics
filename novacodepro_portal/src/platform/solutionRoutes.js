import { appPath } from "./routes.js";

export const SOLUTION_ROOT = appPath("/solutions");

export const SOLUTION_PROJECT_SECTIONS = [
  "dashboard",
  "discovery",
  "requirements",
  "business-analysis",
  "ux-ui",
  "architecture",
  "engineering",
  "quality",
  "security",
  "compliance-risk",
  "releases",
  "deployments",
  "acceptance",
  "operations",
  "support",
  "workflows",
  "approvals",
  "knowledge",
  "evidence",
];

export const SOLUTION_LANDING_SECTIONS = ["overview", "customers", "projects"];

export const SOLUTION_NAV_GROUP = [
  { id: "overview", label: "Overview", path: SOLUTION_ROOT },
  { id: "customers", label: "Customers", path: appPath("/solutions/customers") },
  { id: "projects", label: "Projects", path: appPath("/solutions/projects") },
  { id: "discovery", label: "Discovery", path: appPath("/solutions/projects") },
  { id: "requirements", label: "Requirements", path: appPath("/solutions/projects") },
  { id: "business-analysis", label: "Business Analysis", path: appPath("/solutions/projects") },
  { id: "ux-ui", label: "UX/UI", path: appPath("/solutions/projects") },
  { id: "architecture", label: "Architecture", path: appPath("/solutions/projects") },
  { id: "engineering", label: "Engineering", path: appPath("/solutions/projects") },
  { id: "quality", label: "Quality", path: appPath("/solutions/projects") },
  { id: "security", label: "Security", path: appPath("/solutions/projects") },
  { id: "compliance-risk", label: "Compliance & Risk", path: appPath("/solutions/projects") },
  { id: "releases", label: "Releases", path: appPath("/solutions/projects") },
  { id: "deployments", label: "Deployments", path: appPath("/solutions/projects") },
  { id: "acceptance", label: "Acceptance", path: appPath("/solutions/projects") },
  { id: "operations", label: "Operations", path: appPath("/solutions/projects") },
  { id: "support", label: "Support & Evolution", path: appPath("/solutions/projects") },
  { id: "workflows", label: "Workflow Fabric", path: appPath("/solutions/projects") },
  { id: "approvals", label: "Approvals", path: appPath("/solutions/projects") },
  { id: "knowledge", label: "Knowledge", path: appPath("/solutions/projects") },
  { id: "evidence", label: "Evidence", path: appPath("/solutions/projects") },
];

const CUSTOMER_ROLES = new Set(["CUSTOMER", "CLIENT", "PARTNER", "CUSTOMER_APPROVER"]);
const BUILDER_ROLES = new Set([
  "BUSINESS_ANALYST",
  "PRODUCT_MANAGER",
  "PROJECT_MANAGER",
  "UI_UX_DESIGNER",
  "ARCHITECT",
  "DEVELOPER",
  "QA_ENGINEER",
]);
const ASSURANCE_ROLES = new Set([
  "SECURITY_ENGINEER",
  "PRIVACY_COMPLIANCE",
  "COMPLIANCE_TEAM",
  "RISK_MANAGEMENT",
  "AUDIT_TEAM",
  "DEVOPS_ENGINEER",
  "OPERATIONS_TEAM",
  "CUSTOMER_SUPPORT",
]);

export function isSolutionRoute(pathname) {
  return typeof pathname === "string" && pathname.startsWith("/novacodepro/solutions");
}

export function buildSolutionProjectPath(projectId, section = "dashboard") {
  const normalizedSection = SOLUTION_PROJECT_SECTIONS.includes(section) ? section : "dashboard";
  return appPath(`/solutions/projects/${encodeURIComponent(projectId)}/${normalizedSection}`);
}

export function parseSolutionRoute(pathname) {
  if (!isSolutionRoute(pathname)) {
    return null;
  }
  const normalized = String(pathname || "").replace(/\/+$/, "") || SOLUTION_ROOT;
  if (normalized === SOLUTION_ROOT) {
    return { kind: "landing", section: "overview", path: SOLUTION_ROOT };
  }
  const parts = normalized.split("/").filter(Boolean);
  if (parts.length === 3 && parts[2] === "customers") {
    return { kind: "landing", section: "customers", path: normalized };
  }
  if (parts.length === 3 && parts[2] === "projects") {
    return { kind: "landing", section: "projects", path: normalized };
  }
  if (parts.length >= 4 && parts[2] === "projects") {
    const projectId = decodeURIComponent(parts[3] || "");
    const section = parts[4] || "dashboard";
    return {
      kind: "project",
      projectId,
      section: SOLUTION_PROJECT_SECTIONS.includes(section) ? section : "dashboard",
      path: normalized,
    };
  }
  return { kind: "landing", section: "overview", path: normalized };
}

export function solutionSectionLabel(section) {
  const labels = {
    dashboard: "Dashboard",
    discovery: "Discovery",
    requirements: "Requirements",
    "business-analysis": "Business Analysis",
    "ux-ui": "UX/UI",
    architecture: "Architecture",
    engineering: "Engineering",
    quality: "Quality",
    security: "Security",
    "compliance-risk": "Compliance & Risk",
    releases: "Releases",
    deployments: "Deployments",
    acceptance: "Acceptance",
    operations: "Operations",
    support: "Support & Evolution",
    workflows: "Workflow Fabric",
    approvals: "Approvals",
    knowledge: "Knowledge",
    evidence: "Evidence",
  };
  return labels[section] || "Overview";
}

export function solutionNavigationForRole(role) {
  const roleName = String(role || "").toUpperCase();
  if (roleName === "ADMIN" || roleName === "PLATFORM_ADMIN" || roleName === "PLATFORM_OWNER" || roleName === "SUPER_ADMIN") {
    return SOLUTION_NAV_GROUP;
  }
  if (CUSTOMER_ROLES.has(roleName)) {
    return SOLUTION_NAV_GROUP.filter((item) =>
      ["overview", "customers", "projects", "discovery", "requirements", "approvals", "acceptance", "support", "knowledge", "evidence"].includes(item.id),
    );
  }
  if (BUILDER_ROLES.has(roleName)) {
    return SOLUTION_NAV_GROUP.filter((item) =>
      [
        "overview",
        "customers",
        "projects",
        "discovery",
        "requirements",
        "business-analysis",
        "ux-ui",
        "architecture",
        "engineering",
        "quality",
        "releases",
        "deployments",
        "workflows",
        "approvals",
        "knowledge",
        "evidence",
      ].includes(item.id),
    );
  }
  if (ASSURANCE_ROLES.has(roleName)) {
    return SOLUTION_NAV_GROUP.filter((item) =>
      [
        "overview",
        "customers",
        "projects",
        "architecture",
        "security",
        "compliance-risk",
        "deployments",
        "acceptance",
        "operations",
        "support",
        "workflows",
        "approvals",
        "knowledge",
        "evidence",
      ].includes(item.id),
    );
  }
  return SOLUTION_NAV_GROUP.filter((item) => ["overview", "projects", "knowledge", "evidence"].includes(item.id));
}

export function solutionRoleCanAccessSection(role, section) {
  const visible = solutionNavigationForRole(role).some((item) => item.id === section || (section === "dashboard" && item.id === "overview"));
  return visible;
}
