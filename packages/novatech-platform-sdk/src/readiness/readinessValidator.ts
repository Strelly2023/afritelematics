import { readinessDomains, type ReadinessDomainStatus } from "./readinessDomains";

export type ReadinessRuntime = Readonly<Record<string, ReadinessDomainStatus>>;

export type ReadinessValidationIssue = Readonly<{
  domainId?: string;
  message: string;
}>;

export const validateReadiness = (readiness: ReadinessRuntime): ReadinessValidationIssue[] => {
  const issues: ReadinessValidationIssue[] = [];
  for (const definition of readinessDomains) {
    const value = readiness[definition.domainId];
    if (value !== "PASS") {
      issues.push({ domainId: definition.domainId, message: "readiness domain must be PASS" });
    }
  }
  return issues;
};

