export type NovaTechThemeMode = "light" | "dark";
export type NovaTechAsyncState = "idle" | "loading" | "empty" | "error" | "success" | "offline";
export type NovaTechProductFamily = "NovaID" | "NovaPay" | "NovaRide" | "NovaTech Platform";

export const designTokens = {
  color: {
    light: {
      background: "#F6F8FB",
      surface: "#FFFFFF",
      surfaceAlt: "#EEF3F7",
      text: "#101820",
      muted: "#607080",
      border: "#D9E2EC",
      primary: "#155EEF",
      success: "#168A5A",
      warning: "#B7791F",
      danger: "#C93647",
      trust: "#087A50",
      identity: "#155EEF",
      payment: "#6E42D3",
      mobility: "#0F766E",
    },
    dark: {
      background: "#08111F",
      surface: "#111C2E",
      surfaceAlt: "#17243A",
      text: "#F7FAFC",
      muted: "#9FB0C7",
      border: "#2D3A4F",
      primary: "#7DA2FF",
      success: "#4AD08F",
      warning: "#F5B84B",
      danger: "#FF7A89",
      trust: "#4AD08F",
      identity: "#7DA2FF",
      payment: "#B69CFF",
      mobility: "#5EEAD4",
    },
  },
  typography: {
    fontFamily: "Inter, Segoe UI, Arial, sans-serif",
    display: 32,
    title: 24,
    heading: 20,
    body: 16,
    caption: 13,
    weightRegular: "400",
    weightMedium: "600",
    weightBold: "800",
  },
  spacing: {
    none: 0,
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    xxl: 32,
  },
  radius: {
    sm: 6,
    md: 8,
    lg: 12,
  },
  shadow: {
    card: "0 1px 2px rgba(16, 24, 40, 0.08)",
    elevated: "0 8px 20px rgba(16, 24, 40, 0.12)",
  },
} as const;

export const typography = designTokens.typography;
export const spacing = designTokens.spacing;
export const colors = designTokens.color;

export type NovaTechCardKind =
  | "standard"
  | "receipt"
  | "identity"
  | "ride"
  | "wallet"
  | "trust";

export const cardPrimitives = {
  standard: { borderRadius: designTokens.radius.md, padding: designTokens.spacing.lg },
  receiptCard: { kind: "receipt" as const, ariaRole: "summary", label: "Digital receipt card" },
  identityCard: { kind: "identity" as const, ariaRole: "summary", label: "Digital identity card" },
  rideCard: { kind: "ride" as const, ariaRole: "summary", label: "Ride status card" },
  walletCard: { kind: "wallet" as const, ariaRole: "summary", label: "Wallet balance card" },
};

export const buttonPrimitives = {
  primary: { minHeight: 44, borderRadius: designTokens.radius.md, accessibilityRole: "button" },
  secondary: { minHeight: 44, borderRadius: designTokens.radius.md, accessibilityRole: "button" },
  danger: { minHeight: 44, borderRadius: designTokens.radius.md, accessibilityRole: "button" },
};

export const statusBadges = {
  verified: { tone: "success", label: "Verified" },
  pending: { tone: "warning", label: "Pending" },
  failed: { tone: "danger", label: "Failed" },
  offline: { tone: "warning", label: "Offline" },
};

export const trustIndicators = {
  identityVerified: "NovaID verified identity",
  deviceTrusted: "Trusted device",
  paymentProtected: "NovaPay protected payment",
  rideEvidenceSigned: "NovaRide signed evidence",
  lowRisk: "Low risk",
};

export const stateComponents = {
  loading: { title: "Loading", accessibilityLabel: "Loading state" },
  empty: { title: "Nothing here yet", accessibilityLabel: "Empty state" },
  error: { title: "Something needs attention", accessibilityLabel: "Error state" },
  success: { title: "Completed", accessibilityLabel: "Success state" },
  offline: { title: "Offline", accessibilityLabel: "Offline state" },
} satisfies Record<Exclude<NovaTechAsyncState, "idle">, { title: string; accessibilityLabel: string }>;

export const accessibility = {
  minTouchTarget: 44,
  wcagVersion: "WCAG 2.2",
  labelFor(product: NovaTechProductFamily, action: string) {
    return `${product} ${action}`;
  },
  hintFor(action: string) {
    return `Activates ${action}`;
  },
};

export const receiptCard = cardPrimitives.receiptCard;
export const identityCard = cardPrimitives.identityCard;
export const rideCard = cardPrimitives.rideCard;
export const walletCard = cardPrimitives.walletCard;
