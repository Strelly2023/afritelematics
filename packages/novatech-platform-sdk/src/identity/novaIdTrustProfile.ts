export type NovaIDTrustProfile = Readonly<{
  identityStatus: "pending" | "verified" | "suspended" | "revoked";
  verificationLevel: number;
  emailVerified: boolean;
  phoneVerified: boolean;
  deviceTrust: "unknown" | "trusted" | "untrusted";
  biometricVerified: boolean;
  organizationVerified: boolean;
  roleVerified: boolean;
  complianceStatus: "pending" | "cleared" | "review" | "blocked";
  lastSecurityReview: string | null;
  riskScore: number;
  fraudRisk: "low" | "medium" | "high";
  operationalStatus: "active" | "limited" | "suspended";
}>;

export const novaIdTrustProfileFields = [
  "identityStatus",
  "verificationLevel",
  "emailVerified",
  "phoneVerified",
  "deviceTrust",
  "biometricVerified",
  "organizationVerified",
  "roleVerified",
  "complianceStatus",
  "lastSecurityReview",
  "riskScore",
  "fraudRisk",
  "operationalStatus",
] as const;

export const novaIdTrustProfileTemplate: NovaIDTrustProfile = {
  identityStatus: "pending",
  verificationLevel: 0,
  emailVerified: false,
  phoneVerified: false,
  deviceTrust: "unknown",
  biometricVerified: false,
  organizationVerified: false,
  roleVerified: false,
  complianceStatus: "pending",
  lastSecurityReview: null,
  riskScore: 0,
  fraudRisk: "low",
  operationalStatus: "limited",
};
