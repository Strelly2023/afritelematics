import { accessibility, designTokens, stateComponents, trustIndicators } from "../../novatech-design-system/src";

export type ThemeMode = "light" | "dark";
export type AsyncViewState = "idle" | "loading" | "empty" | "error" | "success" | "offline";
export const NOVAPAY_COLOURS = {
  primary: designTokens.color.light.payment,
  success: designTokens.color.light.success,
  warning: designTokens.color.light.warning,
  danger: designTokens.color.light.danger,
  light: designTokens.color.light.background,
  dark: designTokens.color.dark.background,
} as const;
export const accessibilityLabel = (action: string) => `NovaPay ${action}`;
export const NOVAPAY_SHARED_DESIGN = {
  tokens: designTokens,
  states: stateComponents,
  trustIndicators,
  accessibilityLabel: (action: string) => accessibility.labelFor("NovaPay", action),
} as const;
