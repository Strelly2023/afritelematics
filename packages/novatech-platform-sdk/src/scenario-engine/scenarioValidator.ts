import { scenarioCoverageTargets } from "./scenarioTypes";
import type { Scenario } from "./scenarioTypes";

export type ScenarioValidationIssue = Readonly<{
  scenarioId?: string;
  message: string;
}>;

const requiredArrayFields = [
  "actors",
  "productsUsed",
  "sharedServicesUsed",
  "preconditions",
  "workflowSteps",
  "evidenceRequired",
  "policyChecks",
  "uiSurfaces",
  "apiSurfaces",
  "complianceTags",
] as const;

const requiredScalarFields = [
  "scenarioId",
  "domain",
  "title",
  "primaryProductOwner",
  "userStory",
  "expectedOutcome",
  "testType",
  "riskLevel",
  "independenceRule",
] as const;

export const validateScenarioRecord = (scenario: Scenario): ScenarioValidationIssue[] => {
  const issues: ScenarioValidationIssue[] = [];
  for (const field of requiredScalarFields) {
    const value = scenario[field];
    if (typeof value !== "string" || value.trim().length === 0) {
      issues.push({ scenarioId: scenario.scenarioId, message: `Missing scalar field: ${field}` });
    }
  }
  for (const field of requiredArrayFields) {
    const value = scenario[field];
    if (!Array.isArray(value) || value.length === 0) {
      issues.push({ scenarioId: scenario.scenarioId, message: `Missing array field: ${field}` });
    }
  }
  return issues;
};

export const validateScenarioCatalog = (catalog: readonly Scenario[]): ScenarioValidationIssue[] => {
  const issues: ScenarioValidationIssue[] = [];
  const ids = new Set<string>();
  for (const scenario of catalog) {
    if (ids.has(scenario.scenarioId)) {
      issues.push({ scenarioId: scenario.scenarioId, message: "Duplicate scenarioId" });
    }
    ids.add(scenario.scenarioId);
    issues.push(...validateScenarioRecord(scenario));
    if (scenario.productsUsed.includes("NovaRide") && !scenario.independenceRule.toLowerCase().includes("cross-product")) {
      issues.push({
        scenarioId: scenario.scenarioId,
        message: "NovaRide usage must be explicitly cross-product",
      });
    }
    if (scenario.sharedServicesUsed.includes("NovaAI") && !scenario.policyChecks.some((check) => check.toLowerCase().includes("advisory only"))) {
      issues.push({
        scenarioId: scenario.scenarioId,
        message: "NovaAI usage must remain advisory only",
      });
    }
  }
  for (const target of scenarioCoverageTargets) {
    const actual = catalog.filter((scenario) => scenario.domain === target.domain).length;
    if (actual < target.minimum) {
      issues.push({
        message: `Domain ${target.domain} below minimum coverage: ${actual}/${target.minimum}`,
      });
    }
  }
  return issues;
};
