import type { Scenario, ScenarioDomain, ScenarioRiskLevel, ScenarioTestType } from "./scenarioTypes";

export type ScenarioTemplate = Omit<Scenario, "scenarioId" | "domain">;

export const standardEvidence = [
  "Identity Verified",
  "KYC Complete",
  "AML Check",
  "Sanctions Check",
  "Device Trust",
  "Risk Score",
  "Ledger Entry",
  "Settlement Record",
  "Digital Signature",
  "Replay Evidence",
  "Audit Package",
  "PDF Receipt",
  "Customer Notification",
] as const;

export const standardPolicyChecks = [
  "KYC",
  "AML",
  "Sanctions",
  "Device Trust",
  "Transaction Limits",
  "Velocity",
] as const;

export const standardUiSurfaces = ["Mobile App", "Web Portal", "Operations Console"] as const;

export const standardApiSurfaces = ["Auth API", "Payments API", "Webhooks", "Audit API"] as const;

export const buildScenarioCatalog = (
  domain: ScenarioDomain,
  prefix: string,
  templates: readonly ScenarioTemplate[],
  count: number,
): readonly Scenario[] =>
  Array.from({ length: count }, (_, index) => {
    const template = templates[index % templates.length];
    const ordinal = String(index + 1).padStart(3, "0");
    return {
      ...template,
      scenarioId: `${prefix}-${ordinal}`,
      domain,
      title: `${template.title} ${ordinal}`,
      userStory: `${template.userStory} (${ordinal})`,
      expectedOutcome: `${template.expectedOutcome} (${ordinal})`,
      independenceRule: `${template.independenceRule} (${ordinal})`,
    };
  });

export const scenarioTemplate = (template: ScenarioTemplate): ScenarioTemplate => template;

export const chooseTestType = (index: number, values: readonly ScenarioTestType[]): ScenarioTestType =>
  values[index % values.length];

export const chooseRiskLevel = (index: number, values: readonly ScenarioRiskLevel[]): ScenarioRiskLevel =>
  values[index % values.length];
