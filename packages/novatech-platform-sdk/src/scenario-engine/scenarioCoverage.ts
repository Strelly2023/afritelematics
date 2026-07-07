import { scenarioCoverageTargets } from "./scenarioTypes";
import type { Scenario } from "./scenarioTypes";

export type ScenarioCoverageEntry = Readonly<{
  domain: string;
  minimum: number;
  actual: number;
  delta: number;
}>;

export const scenarioCoverage = (catalog: readonly Scenario[]): readonly ScenarioCoverageEntry[] =>
  scenarioCoverageTargets.map((target) => {
    const actual = catalog.filter((scenario) => scenario.domain === target.domain).length;
    return {
      domain: target.domain,
      minimum: target.minimum,
      actual,
      delta: actual - target.minimum,
    };
  });

export const scenarioCoverageSummary = (catalog: readonly Scenario[]) => {
  const coverage = scenarioCoverage(catalog);
  return {
    total: catalog.length,
    coverage,
    totalMinimum: scenarioCoverageTargets.reduce((sum, target) => sum + target.minimum, 0),
    domainsMet: coverage.filter((item) => item.actual >= item.minimum).length,
  } as const;
};
