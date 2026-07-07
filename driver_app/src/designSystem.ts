import { designTokens, stateComponents, trustIndicators, accessibility } from "../../packages/novatech-design-system/src";

export const novatechDesignSystem = {
  product: "NovaRide",
  tokens: designTokens,
  states: stateComponents,
  trustIndicators,
  accessibilityLabel: (action: string) => accessibility.labelFor("NovaRide", action),
} as const;
