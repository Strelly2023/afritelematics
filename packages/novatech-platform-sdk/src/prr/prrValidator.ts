import { validateReadiness } from "../readiness/readinessValidator";
import type { ReadinessDomainStatus } from "../readiness/readinessDomains";

export type PRRStatus = "NOT_READY" | "READY_FOR_REVIEW" | "APPROVED" | "REJECTED";

export type PRRRuntime = Readonly<{
  status: PRRStatus;
  readiness: Readonly<Record<string, ReadinessDomainStatus>>;
  approvedBy?: string;
  approvedAt?: string;
  notes?: string;
}>;

export type PRRValidationResult = Readonly<{
  status: PRRStatus;
  readyForReview: boolean;
  blockingIssues: readonly string[];
}>;

export const evaluatePRR = (runtime: PRRRuntime): PRRValidationResult => {
  const readinessIssues = validateReadiness(runtime.readiness);
  const blockingIssues = readinessIssues.map((issue) => issue.message);
  const readyForReview = blockingIssues.length === 0;
  return {
    status: readyForReview ? runtime.status : "NOT_READY",
    readyForReview,
    blockingIssues,
  };
};

