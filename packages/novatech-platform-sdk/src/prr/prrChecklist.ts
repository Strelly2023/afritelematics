import type { ReadinessDomainId } from "../readiness/readinessDomains";

export type PRRChecklistItem = Readonly<{
  id: string;
  domain: ReadinessDomainId;
  description: string;
}>;

export const prrChecklist: readonly PRRChecklistItem[] = [
  { id: "PRR-ENG-001", domain: "Engineering", description: "Engineering readiness verified" },
  { id: "PRR-OPS-001", domain: "Operations", description: "Operations readiness verified" },
  { id: "PRR-GOV-001", domain: "Governance", description: "Governance readiness verified" },
  { id: "PRR-COM-001", domain: "Compliance", description: "Compliance readiness verified" },
  { id: "PRR-SEC-001", domain: "Security", description: "Security readiness verified" },
  { id: "PRR-CMR-001", domain: "Commercial", description: "Commercial readiness verified" },
  { id: "PRR-SUP-001", domain: "Support", description: "Support readiness verified" },
  { id: "PRR-DR-001", domain: "DisasterRecovery", description: "Disaster recovery readiness verified" },
] as const;

