export type TrustLevel = "HIGH" | "MEDIUM" | "LOW" | "NEUTRAL";

export const trustColors = {
  HIGH: "#127c50",
  MEDIUM: "#a15c07",
  LOW: "#b42318",
  NEUTRAL: "#2457a6",
  BACKGROUND: "#f5f7f8",
  CARD: "#ffffff",
  TEXT: "#17212f",
  MUTED: "#5f7080",
  BORDER: "#ccd6dd",
  SOFT: "#e8eef2",
};

export const trustSpacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
};

export function trustLevelFromScore(score: number): TrustLevel {
  if (score >= 80) return "HIGH";
  if (score >= 60) return "MEDIUM";
  return "LOW";
}

export function trustLevelColor(score: number): string {
  return trustColors[trustLevelFromScore(score)];
}

export function trustLevelLabel(score: number): string {
  const level = trustLevelFromScore(score);
  if (level === "HIGH") return "High trust";
  if (level === "MEDIUM") return "Review";
  return "Blocked";
}
