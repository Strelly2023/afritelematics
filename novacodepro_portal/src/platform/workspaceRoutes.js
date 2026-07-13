const WORKSPACE_ROUTE_TO_LOGIN_ROLE = {
  admin: "ADMIN",
  developer: "DEVELOPER",
  product: "PRODUCT_MANAGER",
  "business-analyst": "BUSINESS_ANALYST",
  design: "UI_UX_DESIGNER",
  "project-manager": "PROJECT_MANAGER",
  architect: "ARCHITECT",
  "qa-engineer": "QA_ENGINEER",
  "devops-engineer": "DEVOPS_ENGINEER",
  "customer-support": "CUSTOMER_SUPPORT",
  operations: "OPERATIONS_TEAM",
  brand: "BRAND_TEAM",
  compliance: "COMPLIANCE_TEAM",
  audit: "AUDIT_TEAM",
  security: "SECURITY_ENGINEER",
  "incident-response": "INCIDENT_RESPONSE_TEAM",
  "data-architect": "DATA_ARCHITECT",
  "data-engineering": "DATA_ENGINEER",
  "database-engineer": "DATABASE_ENGINEER",
  "ai-ml-engineer": "AI_ML_ENGINEER",
  "data-scientist": "DATA_SCIENTIST",
  "privacy-compliance": "PRIVACY_COMPLIANCE",
  risk: "RISK_MANAGEMENT",
  legal: "LEGAL",
  regulator: "EXTERNAL_REGULATOR",
};

export function resolveWorkspaceLoginRoleFromPathname(pathname) {
  if (typeof pathname !== "string") {
    return null;
  }
  const match = pathname.match(/^\/novacodepro\/workspace\/([^/?#]+)(?:\/dashboard)?(?:[/?#]|$)/);
  if (!match) {
    return null;
  }
  return WORKSPACE_ROUTE_TO_LOGIN_ROLE[match[1]] || null;
}

export function resolveWorkspaceSlugFromLoginRole(role) {
  const roleName = String(role || "").trim().toUpperCase();
  if (["ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(roleName)) {
    return "admin";
  }
  for (const [slug, mappedRole] of Object.entries(WORKSPACE_ROUTE_TO_LOGIN_ROLE)) {
    if (mappedRole === roleName) {
      return slug;
    }
  }
  return "workspace";
}
