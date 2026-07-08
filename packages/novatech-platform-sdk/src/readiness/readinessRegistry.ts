import { readinessDomains } from "./readinessDomains";

export const readinessRegistry = {
  domains: readinessDomains,
  domainIds: readinessDomains.map((domain) => domain.domainId),
} as const;

