import { designTokens, stateComponents, trustIndicators, accessibility } from "../../packages/novatech-design-system/src";

export const novatechDesignSystem = {
  product: "NovaID",
  tokens: designTokens,
  states: stateComponents,
  trustIndicators,
  accessibilityLabel: (action: string) => accessibility.labelFor("NovaID", action),
} as const;
