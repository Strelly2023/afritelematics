import { designTokens, stateComponents, trustIndicators, accessibility } from "../../packages/novatech-design-system/src";

export const novatechDesignSystem = {
  product: "NovaPay",
  tokens: designTokens,
  states: stateComponents,
  trustIndicators,
  accessibilityLabel: (action: string) => accessibility.labelFor("NovaPay", action),
} as const;
