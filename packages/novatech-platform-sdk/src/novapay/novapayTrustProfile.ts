export type NovapayTrustProfile = Readonly<{
  identityStatus: "pending" | "verified" | "suspended" | "revoked";
  verificationLevel: number;
  deviceTrust: "unknown" | "trusted" | "untrusted";
  complianceStatus: "pending" | "cleared" | "review" | "blocked";
  fraudRisk: "low" | "medium" | "high";
  operationalStatus: "active" | "limited" | "suspended";
  securityScore: number;
  walletStatus: "inactive" | "active" | "restricted";
  kycStatus: "not_started" | "basic" | "standard" | "enhanced";
  settlementStatus: "not_applicable" | "pending" | "approved" | "blocked";
  evidenceStatus: "required" | "collected" | "signed" | "archived";
  novaTrustEvidenceRequired: readonly string[];
}>;

export const novapayTrustProfileFields = [
  "identityStatus",
  "verificationLevel",
  "deviceTrust",
  "complianceStatus",
  "fraudRisk",
  "operationalStatus",
  "securityScore",
  "walletStatus",
  "kycStatus",
  "settlementStatus",
  "evidenceStatus",
  "novaTrustEvidenceRequired",
] as const;

export const novapayTrustProfileTemplate: NovapayTrustProfile = {
  identityStatus: "pending",
  verificationLevel: 0,
  deviceTrust: "unknown",
  complianceStatus: "pending",
  fraudRisk: "low",
  operationalStatus: "limited",
  securityScore: 0,
  walletStatus: "inactive",
  kycStatus: "not_started",
  settlementStatus: "not_applicable",
  evidenceStatus: "required",
  novaTrustEvidenceRequired: [
    "Identity Verified",
    "KYC Complete",
    "Ledger Entry",
    "Settlement Record",
    "Digital Signature",
    "Replay Evidence",
    "Audit Package",
    "PDF Receipt",
  ],
};
