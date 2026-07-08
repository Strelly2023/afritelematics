import type { ReleaseStageId } from "../release/releaseStage";

export type ActivationGateId =
  | "PUBLIC_REGISTRATION"
  | "PUBLIC_ONBOARDING"
  | "REAL_PAYMENTS"
  | "COUNTRY_ACTIVATION"
  | "FEATURE_ACTIVATION"
  | "MERCHANT_ACTIVATION"
  | "AGENT_ACTIVATION"
  | "DRIVER_ACTIVATION";

export type ActivationGateDefinition = Readonly<{
  gateId: ActivationGateId;
  description: string;
  enabled: boolean;
  approvalRequired: boolean;
  requiredStage: ReleaseStageId;
  requiredDomains: readonly string[];
  requiredGuards: readonly string[];
  requiredEvidence: readonly string[];
}>;

export const activationGateDefinitions: readonly ActivationGateDefinition[] = [
  {
    gateId: "PUBLIC_REGISTRATION",
    description: "Allows public signup and account creation.",
    enabled: false,
    approvalRequired: true,
    requiredStage: "PUBLIC_PILOT",
    requiredDomains: ["Governance", "Compliance", "Operations"],
    requiredGuards: ["guard_release_stage", "guard_ga_enablement"],
    requiredEvidence: ["PRR certificate", "Approval artifact"],
  },
  {
    gateId: "PUBLIC_ONBOARDING",
    description: "Allows public onboarding flows for approved users.",
    enabled: false,
    approvalRequired: true,
    requiredStage: "PUBLIC_PILOT",
    requiredDomains: ["Governance", "Compliance", "Operations"],
    requiredGuards: ["guard_release_stage", "guard_activation_gate"],
    requiredEvidence: ["Region approval", "Monitoring evidence"],
  },
  {
    gateId: "REAL_PAYMENTS",
    description: "Allows real payment execution subject to pilot or GA approval.",
    enabled: false,
    approvalRequired: true,
    requiredStage: "PUBLIC_PILOT",
    requiredDomains: ["Compliance", "Security", "Operations", "Governance"],
    requiredGuards: ["guard_activation_gate", "guard_ga_enablement"],
    requiredEvidence: ["Payment approval", "Reconciliation evidence"],
  },
  {
    gateId: "COUNTRY_ACTIVATION",
    description: "Allows a specific country or region to be activated.",
    enabled: false,
    approvalRequired: true,
    requiredStage: "PUBLIC_PILOT",
    requiredDomains: ["Governance", "Operations", "Compliance"],
    requiredGuards: ["guard_release_stage", "guard_ga_enablement"],
    requiredEvidence: ["Country approval", "Geography approval"],
  },
  {
    gateId: "FEATURE_ACTIVATION",
    description: "Allows product-specific features to be turned on.",
    enabled: true,
    approvalRequired: true,
    requiredStage: "INTERNAL_QA",
    requiredDomains: ["Engineering", "Governance"],
    requiredGuards: ["guard_release_stage"],
    requiredEvidence: ["Feature flag review"],
  },
  {
    gateId: "MERCHANT_ACTIVATION",
    description: "Allows merchant onboarding and payment acceptance.",
    enabled: false,
    approvalRequired: true,
    requiredStage: "PUBLIC_PILOT",
    requiredDomains: ["Compliance", "Security", "Operations"],
    requiredGuards: ["guard_activation_gate", "guard_ga_enablement"],
    requiredEvidence: ["Merchant approval", "KYB evidence"],
  },
  {
    gateId: "AGENT_ACTIVATION",
    description: "Allows agent onboarding and cash-in/cash-out workflows.",
    enabled: false,
    approvalRequired: true,
    requiredStage: "PUBLIC_PILOT",
    requiredDomains: ["Compliance", "Security", "Operations"],
    requiredGuards: ["guard_activation_gate", "guard_ga_enablement"],
    requiredEvidence: ["Agent approval", "Cash procedure evidence"],
  },
  {
    gateId: "DRIVER_ACTIVATION",
    description: "Allows driver onboarding and dispatch access.",
    enabled: true,
    approvalRequired: true,
    requiredStage: "CONTROLLED_PILOT",
    requiredDomains: ["Operations", "Safety", "Governance"],
    requiredGuards: ["guard_activation_gate"],
    requiredEvidence: ["Driver approval", "Safety evidence"],
  },
] as const;

