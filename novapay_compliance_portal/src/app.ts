export const portal = {
  name: "NovaPay Compliance",
  route: "/compliance",
  role: "compliance_officer",
  features: ["KYC Review", "KYB Review", "AML Alerts", "Sanctions Checks", "Suspicious Activity Reports", "Risk Scoring", "Audit Packages", "Case Management"],
} as const;
export const reviewCase = (caseId: string, decision: "approve" | "escalate" | "reject") => ({ caseId, decision, auditEvent: `compliance.${decision}` });
export const render = () => `<main aria-label="${portal.name}"><h1>${portal.name}</h1>${portal.features.map((feature) => `<button aria-label="Open ${feature}">${feature}</button>`).join("")}</main>`;
