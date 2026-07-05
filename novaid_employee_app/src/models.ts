export type AppVariantId =
  | "personal"
  | "business"
  | "employee"
  | "inspector"
  | "partner";

export type IdentityStatus =
  | "draft"
  | "pending"
  | "verified"
  | "rejected"
  | "revoked";

export type TrustLevel = "Unverified" | "Basic" | "Verified" | "High";

export interface IdentityProfile {
  id: string;
  appVariant: AppVariantId;
  displayName: string;
  trustLevel: TrustLevel;
  identityScore: number;
  credentialCount: number;
  trustedDevices: number;
  governmentIds: number;
  certificateCount: number;
  biometricVerified: boolean;
  passkeyEnabled: boolean;
  deviceTrustEnabled: boolean;
  recoveryEnabled: boolean;
  connectedApps: number;
  loginHistory: number;
  verificationStatus: IdentityStatus;
  walletLabel: string;
  summary: string;
  credentials: Credential[];
  devices: TrustedDevice[];
  consents: ConsentGrant[];
  certificates: DigitalCertificate[];
  events: IdentityEvent[];
}

export interface Credential {
  id: string;
  type:
    | "government_id"
    | "driver_licence"
    | "passport"
    | "student_card"
    | "employee_id"
    | "health_card"
    | "digital_certificate"
    | "business_registration"
    | "tax_profile"
    | "partner_credential"
    | "access_badge";
  label: string;
  issuer: string;
  status: IdentityStatus;
  issuedAt: string;
  expiresAt?: string | null;
  metadata?: Record<string, string>;
}

export interface DigitalCertificate {
  id: string;
  subjectId: string;
  title: string;
  issuer: string;
  issuedAt: string;
  sealHash: string;
  replayHash: string;
  status: IdentityStatus;
  scope: string[];
}

export interface TrustedDevice {
  id: string;
  deviceName: string;
  platform: "android" | "ios" | "web" | "desktop";
  lastSeenAt: string;
  trusted: boolean;
  biometricBound: boolean;
  passkeyBound: boolean;
  deviceTrustScore: number;
}

export interface ConsentGrant {
  id: string;
  subjectId: string;
  requester: string;
  credentialId: string;
  attributes: string[];
  grantedAt: string;
  revokedAt?: string | null;
  status: "active" | "revoked" | "expired";
}

export interface IdentityEvent {
  id: string;
  type:
    | "identity_created"
    | "verification"
    | "biometric_match"
    | "policy_validation"
    | "certificate_issued"
    | "consent_granted"
    | "consent_revoked"
    | "device_trust"
    | "offline_verify"
    | "oauth_client"
    | "inspection"
    | "support";
  title: string;
  detail: string;
  timestamp: string;
  severity: "info" | "success" | "warning" | "critical";
}

export interface VerificationRequest {
  id: string;
  profileId: string;
  step:
    | "identity_request"
    | "biometric_verification"
    | "document_validation"
    | "liveness_detection"
    | "policy_evaluation"
    | "approved"
    | "certificate_issued";
  status: IdentityStatus;
  requestedAt: string;
  reviewedAt?: string | null;
  documentCheck: DocumentCheck;
  biometricCheck: BiometricCheck;
  livenessCheck: LivenessCheck;
  policyEvaluation: PolicyEvaluation;
}

export interface BiometricCheck {
  status: IdentityStatus;
  method: "face" | "fingerprint" | "iris" | "multi";
  confidence: number;
  checkedAt: string;
}

export interface DocumentCheck {
  status: IdentityStatus;
  documentType: string;
  country: string;
  checkedAt: string;
}

export interface LivenessCheck {
  status: IdentityStatus;
  confidence: number;
  challenge: string;
  checkedAt: string;
}

export interface PolicyEvaluation {
  status: IdentityStatus;
  score: number;
  reasons: string[];
  evaluatedAt: string;
}

export interface OrganizationIdentity {
  id: string;
  legalName: string;
  registrationNumber: string;
  taxNumber: string;
  trustLevel: TrustLevel;
  certificateCount: number;
  directorCount: number;
  employeeCount: number;
}

export interface EmployeeIdentity {
  id: string;
  employeeNumber: string;
  role: string;
  accessLevel: string;
  attendanceStatus: "checked_out" | "checked_in" | "on_leave";
  walletBalance: string;
}

export interface PartnerClient {
  id: string;
  name: string;
  clientId: string;
  secretHint: string;
  webhookUrl: string;
  apiUsage: number;
  status: IdentityStatus;
}

export interface InspectionRecord {
  id: string;
  inspectorId: string;
  credentialId: string;
  result: "verified" | "rejected" | "queued";
  offlineMode: boolean;
  savedAt: string;
  syncedAt?: string | null;
}

export interface AuditPackage {
  id: string;
  eventIds: string[];
  replayHash: string;
  digitalSignature: string;
  createdAt: string;
}

export interface NovaAIIdentityRecommendation {
  id: string;
  title: string;
  detail: string;
  confidence: number;
}

export interface AppTab {
  key: string;
  label: string;
  description: string;
}

export interface AppAction {
  label: string;
  detail: string;
}

export interface AppConfig {
  id: AppVariantId;
  appName: string;
  packageId: string;
  tagline: string;
  trustTheme: string;
  tabs: AppTab[];
  actions: AppAction[];
  primaryFlow: string[];
  seed: {
    displayName: string;
    walletLabel: string;
    trustLevel: TrustLevel;
    identityScore: number;
    credentialCount: number;
    trustedDevices: number;
    governmentIds: number;
    certificateCount: number;
    biometricVerified: boolean;
    passkeyEnabled: boolean;
    deviceTrustEnabled: boolean;
    recoveryEnabled: boolean;
    connectedApps: number;
    loginHistory: number;
  };
}
