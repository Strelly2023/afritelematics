export type RiskIndicator = "low" | "medium" | "high" | "blocked";
export const assessRisk = (amount: number, offline: boolean): RiskIndicator => {
  if (amount >= 10000) return "high";
  if (offline || amount >= 5000) return "medium";
  return "low";
};
