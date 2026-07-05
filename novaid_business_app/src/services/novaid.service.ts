import { appConfig } from "../appConfig";
import {
  AuditPackage,
  Credential,
  DigitalCertificate,
  IdentityEvent,
  IdentityProfile,
  VerificationRequest,
} from "../models";

const now = () => new Date().toISOString();
const id = (prefix: string) => `${prefix}-${Math.random().toString(36).slice(2, 10)}`;

export const mockCredentials: Credential[] = [
  {
    id: "cred-gov-id",
    type: "government_id",
    label: "National ID",
    issuer: "Government Registry",
    status: "verified",
    issuedAt: now(),
    metadata: { region: "Primary" },
  },
  {
    id: "cred-passport",
    type: "passport",
    label: "Passport",
    issuer: "Passport Office",
    status: "verified",
    issuedAt: now(),
  },
  {
    id: "cred-health",
    type: "health_card",
    label: "Health Card",
    issuer: "Health Authority",
    status: "verified",
    issuedAt: now(),
  },
];

export const mockDevices = [
  {
    id: "device-personal-1",
    deviceName: "Primary Android",
    platform: "android" as const,
    lastSeenAt: now(),
    trusted: true,
    biometricBound: true,
    passkeyBound: false,
    deviceTrustScore: 96,
  },
  {
    id: "device-personal-2",
    deviceName: "Tablet",
    platform: "web" as const,
    lastSeenAt: now(),
    trusted: true,
    biometricBound: false,
    passkeyBound: false,
    deviceTrustScore: 88,
  },
];

export const mockCertificates: DigitalCertificate[] = [
  {
    id: "cert-personal-1",
    subjectId: "personal-subject",
    title: "Verified Identity Certificate",
    issuer: "NovaID Authority",
    issuedAt: now(),
    sealHash: "seal-5f2f0a8b",
    replayHash: "replay-2f9a4f1c",
    status: "verified",
    scope: ["identity", "consent", "device_trust"],
  },
];

export function createMockIdentityProfile(): IdentityProfile {
  return {
    id: "identity-personal-001",
    appVariant: appConfig.id,
    displayName: appConfig.seed.displayName,
    trustLevel: appConfig.seed.trustLevel,
    identityScore: appConfig.seed.identityScore,
    credentialCount: appConfig.seed.credentialCount,
    trustedDevices: appConfig.seed.trustedDevices,
    governmentIds: appConfig.seed.governmentIds,
    certificateCount: appConfig.seed.certificateCount,
    biometricVerified: appConfig.seed.biometricVerified,
    passkeyEnabled: appConfig.seed.passkeyEnabled,
    deviceTrustEnabled: appConfig.seed.deviceTrustEnabled,
    recoveryEnabled: appConfig.seed.recoveryEnabled,
    connectedApps: appConfig.seed.connectedApps,
    loginHistory: appConfig.seed.loginHistory,
    verificationStatus: "verified",
    walletLabel: appConfig.seed.walletLabel,
    summary: "Selective-disclosure identity, consent, and trust wallet.",
    credentials: [...mockCredentials],
    devices: [...mockDevices],
    consents: [],
    certificates: [...mockCertificates],
    events: [
      {
        id: id("event"),
        type: "identity_created",
        title: "Identity created",
        detail: "NovaID profile provisioned with trust and consent controls.",
        timestamp: now(),
        severity: "success",
      },
      {
        id: id("event"),
        type: "certificate_issued",
        title: "Certificate issued",
        detail: "Digital certificate available for verified sharing.",
        timestamp: now(),
        severity: "success",
      },
    ],
  };
}

export async function loadIdentityProfile(): Promise<IdentityProfile> {
  return createMockIdentityProfile();
}

export async function beginVerificationFlow(profileId: string): Promise<VerificationRequest> {
  return {
    id: id("verification"),
    profileId,
    step: "certificate_issued",
    status: "verified",
    requestedAt: now(),
    reviewedAt: now(),
    documentCheck: {
      status: "verified",
      documentType: "National ID",
      country: "AU",
      checkedAt: now(),
    },
    biometricCheck: {
      status: "verified",
      method: "multi",
      confidence: 0.98,
      checkedAt: now(),
    },
    livenessCheck: {
      status: "verified",
      confidence: 0.96,
      challenge: "blink-and-turn",
      checkedAt: now(),
    },
    policyEvaluation: {
      status: "verified",
      score: 98,
      reasons: ["Device trusted", "Document verified", "Biometric matched"],
      evaluatedAt: now(),
    },
  };
}

export async function buildAuditPackage(eventIds: string[]): Promise<AuditPackage> {
  return {
    id: id("audit"),
    eventIds,
    replayHash: "replay-" + Math.random().toString(36).slice(2, 10),
    digitalSignature: "sig-" + Math.random().toString(36).slice(2, 10),
    createdAt: now(),
  };
}
