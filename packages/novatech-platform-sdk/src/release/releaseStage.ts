export type ReleaseStageId =
  | "PRIVATE_DEVELOPMENT"
  | "INTERNAL_QA"
  | "CONTROLLED_PILOT"
  | "PUBLIC_PILOT"
  | "PRODUCTION_READINESS_REVIEW"
  | "GENERAL_AVAILABILITY"
  | "REGIONAL_EXPANSION"
  | "GLOBAL_MULTI_REGION_PLATFORM";

export type ReleasePaymentMode = "SIMULATED" | "SANDBOX" | "PILOT_REAL_LIMITED" | "PILOT_REAL" | "REAL" | "DISABLED";

export type ReleaseStageDefinition = Readonly<{
  id: ReleaseStageId;
  name: string;
  description: string;
  entryCriteria: readonly string[];
  exitCriteria: readonly string[];
  requiredDomains: readonly string[];
  allowedActivationGates: readonly string[];
  allowedPaymentModes: readonly ReleasePaymentMode[];
  requiredGovernanceArtifacts: readonly string[];
}>;

export const releaseStageOrder: readonly ReleaseStageId[] = [
  "PRIVATE_DEVELOPMENT",
  "INTERNAL_QA",
  "CONTROLLED_PILOT",
  "PUBLIC_PILOT",
  "PRODUCTION_READINESS_REVIEW",
  "GENERAL_AVAILABILITY",
  "REGIONAL_EXPANSION",
  "GLOBAL_MULTI_REGION_PLATFORM",
] as const;

export const releaseStages: readonly ReleaseStageDefinition[] = [
  {
    id: "PRIVATE_DEVELOPMENT",
    name: "Private Development",
    description: "Feature construction, architecture validation, unit testing, and developer verification.",
    entryCriteria: ["Architecture available", "Developer-only environment", "No live payment authority"],
    exitCriteria: ["Development-ready software", "Unit tests passing", "Governance scaffolding present"],
    requiredDomains: ["Engineering", "Governance"],
    allowedActivationGates: [],
    allowedPaymentModes: ["SIMULATED", "SANDBOX", "DISABLED"],
    requiredGovernanceArtifacts: ["ADR", "Invariant", "Rule", "Guard"],
  },
  {
    id: "INTERNAL_QA",
    name: "Internal QA",
    description: "System, regression, integration, and security verification by internal staff only.",
    entryCriteria: ["Private development complete", "QA build available", "Sandbox identity available"],
    exitCriteria: ["Pilot candidate build", "Internal QA validations pass", "Release guards stable"],
    requiredDomains: ["Engineering", "Operations", "Governance", "Compliance", "Security"],
    allowedActivationGates: ["FEATURE_ACTIVATION"],
    allowedPaymentModes: ["SIMULATED", "SANDBOX", "DISABLED"],
    requiredGovernanceArtifacts: ["ADR", "Invariant", "Rule", "Guard", "Release Config"],
  },
  {
    id: "CONTROLLED_PILOT",
    name: "Controlled Pilot",
    description: "Approved participants only, limited geography, monitored and support-enabled.",
    entryCriteria: ["Internal QA complete", "Approved participants defined", "Pilot controls active"],
    exitCriteria: ["Controlled pilot tests passing", "Safety controls verified", "No critical defects"],
    requiredDomains: ["Engineering", "Operations", "Governance", "Compliance", "Security", "Support"],
    allowedActivationGates: ["FEATURE_ACTIVATION", "DRIVER_ACTIVATION", "AGENT_ACTIVATION", "MERCHANT_ACTIVATION"],
    allowedPaymentModes: ["SIMULATED", "SANDBOX", "DISABLED"],
    requiredGovernanceArtifacts: ["ADR", "Invariant", "Rule", "Guard", "Pilot Registry", "Exit Criteria"],
  },
  {
    id: "PUBLIC_PILOT",
    name: "Public Pilot",
    description: "Real users in approved regions with governed limits, monitoring, support, and PRR gating.",
    entryCriteria: ["Controlled pilot complete", "Pilot geography approved", "Support and monitoring active"],
    exitCriteria: ["Ready for PRR", "Population and geography validated", "Reconciliation and incident response complete"],
    requiredDomains: ["Engineering", "Operations", "Governance", "Compliance", "Security", "Support", "DisasterRecovery"],
    allowedActivationGates: ["PUBLIC_REGISTRATION", "PUBLIC_ONBOARDING", "FEATURE_ACTIVATION", "COUNTRY_ACTIVATION", "REAL_PAYMENTS"],
    allowedPaymentModes: ["PILOT_REAL_LIMITED", "SIMULATED", "SANDBOX", "DISABLED"],
    requiredGovernanceArtifacts: ["ADR", "Invariant", "Rule", "Binding", "Guard", "Approval", "Exit Report", "PRR Placeholder"],
  },
  {
    id: "PRODUCTION_READINESS_REVIEW",
    name: "Production Readiness Review",
    description: "Formal certification gate used to decide whether GA may be enabled.",
    entryCriteria: ["Public pilot ready for PRR", "Evidence packages complete", "All required domains passing"],
    exitCriteria: ["PRR approved or rejected", "GA remain blocked until approval"],
    requiredDomains: ["Engineering", "Operations", "Governance", "Compliance", "Security", "Commercial", "Support", "DisasterRecovery"],
    allowedActivationGates: ["FEATURE_ACTIVATION", "COUNTRY_ACTIVATION", "REAL_PAYMENTS"],
    allowedPaymentModes: ["PILOT_REAL_LIMITED", "PILOT_REAL", "REAL", "DISABLED"],
    requiredGovernanceArtifacts: ["PRR Checklist", "PRR Certificate", "Exit Report", "Governance Sign-off"],
  },
  {
    id: "GENERAL_AVAILABILITY",
    name: "General Availability",
    description: "Official market launch for approved regions and customer segments.",
    entryCriteria: ["PRR approved", "GA authorization granted", "Commercial readiness signed off"],
    exitCriteria: ["GA operating state active", "Public support and incident response live"],
    requiredDomains: ["Engineering", "Operations", "Governance", "Compliance", "Security", "Commercial", "Support"],
    allowedActivationGates: ["PUBLIC_REGISTRATION", "PUBLIC_ONBOARDING", "REAL_PAYMENTS", "COUNTRY_ACTIVATION", "FEATURE_ACTIVATION", "MERCHANT_ACTIVATION", "AGENT_ACTIVATION", "DRIVER_ACTIVATION"],
    allowedPaymentModes: ["REAL", "PILOT_REAL", "PILOT_REAL_LIMITED"],
    requiredGovernanceArtifacts: ["PRR Certificate", "GA Authorization", "Commercial Approval"],
  },
  {
    id: "REGIONAL_EXPANSION",
    name: "Regional Expansion",
    description: "Additional regions are activated under the GA governance model.",
    entryCriteria: ["GA active", "Expansion request approved", "Regional controls configured"],
    exitCriteria: ["New region operational", "Regional support and compliance active"],
    requiredDomains: ["Engineering", "Operations", "Governance", "Compliance", "Security", "Commercial", "Support"],
    allowedActivationGates: ["COUNTRY_ACTIVATION", "FEATURE_ACTIVATION", "REAL_PAYMENTS"],
    allowedPaymentModes: ["REAL", "PILOT_REAL", "PILOT_REAL_LIMITED"],
    requiredGovernanceArtifacts: ["Regional Approval", "Compliance Review", "Operational Runbook"],
  },
  {
    id: "GLOBAL_MULTI_REGION_PLATFORM",
    name: "Global Multi-Region Platform",
    description: "Multi-country operation with shared governance and region-specific controls.",
    entryCriteria: ["Regional expansion operational", "Cross-region controls validated", "Global support model approved"],
    exitCriteria: ["Global platform stable", "Multi-region governance active"],
    requiredDomains: ["Engineering", "Operations", "Governance", "Compliance", "Security", "Commercial", "Support", "DisasterRecovery"],
    allowedActivationGates: ["PUBLIC_REGISTRATION", "PUBLIC_ONBOARDING", "REAL_PAYMENTS", "COUNTRY_ACTIVATION", "FEATURE_ACTIVATION", "MERCHANT_ACTIVATION", "AGENT_ACTIVATION", "DRIVER_ACTIVATION"],
    allowedPaymentModes: ["REAL"],
    requiredGovernanceArtifacts: ["Global Governance Charter", "Region Matrix", "Cross-border Compliance"],
  },
] as const;

export const releaseStageById = (stageId: ReleaseStageId): ReleaseStageDefinition =>
  releaseStages.find((stage) => stage.id === stageId) ?? releaseStages[0];

export const releaseStageIndex = (stageId: ReleaseStageId): number =>
  releaseStageOrder.indexOf(stageId);

