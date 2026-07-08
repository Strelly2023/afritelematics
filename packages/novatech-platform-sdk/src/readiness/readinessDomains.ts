export type ReadinessDomainId =
  | "Engineering"
  | "Operations"
  | "Governance"
  | "Compliance"
  | "Commercial"
  | "Security"
  | "Support"
  | "DisasterRecovery";

export type ReadinessDomainStatus = "PASS" | "REVIEW" | "BLOCKED" | "FAIL";

export type ReadinessDomainDefinition = Readonly<{
  domainId: ReadinessDomainId;
  requiredChecks: readonly string[];
  status: ReadinessDomainStatus;
  blockingIssues: readonly string[];
  approvalAuthority: string;
}>;

export const readinessDomains: readonly ReadinessDomainDefinition[] = [
  {
    domainId: "Engineering",
    requiredChecks: ["Architecture", "Unit tests", "Integration tests", "Regression tests", "Performance"],
    status: "PASS",
    blockingIssues: [],
    approvalAuthority: "Engineering Leadership",
  },
  {
    domainId: "Operations",
    requiredChecks: ["Monitoring", "Alerting", "Incident response", "Runbooks", "On-call procedures"],
    status: "PASS",
    blockingIssues: [],
    approvalAuthority: "Operations Leadership",
  },
  {
    domainId: "Governance",
    requiredChecks: ["ADR", "Invariant", "Binding", "Rule", "Guard", "CI passing"],
    status: "PASS",
    blockingIssues: [],
    approvalAuthority: "Governance Council",
  },
  {
    domainId: "Compliance",
    requiredChecks: ["Identity verification", "Audit logging", "Privacy controls", "Financial controls", "Regulatory review"],
    status: "PASS",
    blockingIssues: [],
    approvalAuthority: "Compliance Leadership",
  },
  {
    domainId: "Commercial",
    requiredChecks: ["Pricing", "Customer support", "Partner readiness", "Sales readiness", "Marketing readiness"],
    status: "PASS",
    blockingIssues: [],
    approvalAuthority: "Commercial Leadership",
  },
  {
    domainId: "Security",
    requiredChecks: ["Threat model", "Auth controls", "Device trust", "Secrets handling", "Audit review"],
    status: "PASS",
    blockingIssues: [],
    approvalAuthority: "Security Leadership",
  },
  {
    domainId: "Support",
    requiredChecks: ["Support contacts", "Escalation paths", "Case handling", "User communications"],
    status: "PASS",
    blockingIssues: [],
    approvalAuthority: "Support Leadership",
  },
  {
    domainId: "DisasterRecovery",
    requiredChecks: ["Backup validation", "Restore validation", "Rollback plan", "Disaster simulation"],
    status: "PASS",
    blockingIssues: [],
    approvalAuthority: "Infrastructure Leadership",
  },
] as const;

