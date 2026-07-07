import { accessibility, designTokens, stateComponents, trustIndicators } from "../../novatech-design-system/src";

export type ThemeMode = "light" | "dark";
export type SurfaceState = "empty" | "loading" | "error" | "success" | "offline";
export const TOKENS = {
  primary: designTokens.color.light.mobility,
  safety: designTokens.color.light.danger,
  trust: designTokens.color.light.trust,
  radius: designTokens.radius.md,
  spacing: designTokens.spacing.sm,
} as const;
export const accessibleRideLabel = (label: string) => `NovaRide ${label}`;
export const NOVARIDE_SHARED_DESIGN = {
  tokens: designTokens,
  states: stateComponents,
  trustIndicators,
  accessibilityLabel: (action: string) => accessibility.labelFor("NovaRide", action),
} as const;
