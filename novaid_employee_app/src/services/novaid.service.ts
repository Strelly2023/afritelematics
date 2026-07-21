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

type RuntimeEnv = Record<string, string | undefined>;

type NovaIDRuntimeConfig = {
  apiBaseUrl: string;
  tenantId: string;
  accessToken: string | null;
  allowMockFallback: boolean;
  timeoutMs: number;
};

function readEnv(): RuntimeEnv {
  return (globalThis as { process?: { env?: RuntimeEnv } }).process?.env ?? {};
}

function readRuntimeConfig(): NovaIDRuntimeConfig {
  const env = readEnv();
  const apiBaseUrl = String(
    env.EXPO_PUBLIC_NOVAID_API_BASE_URL || env.EXPO_PUBLIC_API_BASE_URL || env.NOVAID_API_BASE_URL || "",
  ).replace(/\/+$/, "");
  const tenantId = String(env.EXPO_PUBLIC_NOVAID_TENANT_ID || env.NOVAID_TENANT_ID || appConfig.id);
  const accessToken = String(
    env.EXPO_PUBLIC_NOVAID_ACCESS_TOKEN || env.NOVAID_ACCESS_TOKEN || "",
  ).trim();
  const allowMockFallback = String(
    env.EXPO_PUBLIC_NOVAID_ALLOW_MOCK_FALLBACK || env.NOVAID_ALLOW_MOCK_FALLBACK || "true",
  ).toLowerCase() !== "false";
  const timeoutMs = Number(
    env.EXPO_PUBLIC_NOVAID_TIMEOUT_MS || env.NOVAID_TIMEOUT_MS || "12000",
  );
  return {
    apiBaseUrl,
    tenantId,
    accessToken: accessToken || null,
    allowMockFallback,
    timeoutMs: Number.isFinite(timeoutMs) && timeoutMs > 0 ? timeoutMs : 12000,
  };
}

function stableFingerprint(values: readonly string[]): string {
  const seed = [...values].sort().join("|");
  let hash = 2166136261;
  for (const char of seed) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

async function requestJson<T>(
  path: string,
  {
    method = "GET",
    body,
    auth = true,
  }: { method?: string; body?: unknown; auth?: boolean } = {},
): Promise<T> {
  const runtime = readRuntimeConfig();
  if (!runtime.apiBaseUrl) {
    throw new Error("NOVAID_API_BASE_URL_NOT_CONFIGURED");
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), runtime.timeoutMs);
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Tenant-Id": runtime.tenantId,
    "X-Correlation-Id": id("corr"),
    "X-Request-Id": id("req"),
  };
  if (auth && runtime.accessToken) {
    headers.Authorization = `Bearer ${runtime.accessToken}`;
  }

  try {
    const response = await fetch(`${runtime.apiBaseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
    const text = await response.text();
    const payload = text ? JSON.parse(text) : {};
    if (!response.ok) {
      const detail =
        payload && typeof payload === "object" && "detail" in payload
          ? String((payload as { detail?: unknown }).detail)
          : `novaid_request_failed_${response.status}`;
      throw new Error(detail);
    }
    return payload as T;
  } finally {
    clearTimeout(timer);
  }
}

function buildBackendProfile(
  me: Record<string, unknown>,
  sessions: Array<Record<string, unknown>>,
): IdentityProfile {
  const base = createMockIdentityProfile();
  const identityStatus = String(me.identity_status ?? me.session_status ?? base.verificationStatus).toLowerCase();
  const verificationStatus =
    identityStatus === "revoked"
      ? "revoked"
      : identityStatus === "pending" || identityStatus === "draft"
        ? "pending"
        : "verified";
  const trustLevel =
    verificationStatus === "verified"
      ? "High"
      : verificationStatus === "pending"
        ? "Basic"
        : "Unverified";
  const sessionCount = sessions.length;
  const summary = `NovaID backend synced for tenant ${String(me.tenant_id ?? appConfig.id)} · ${String(
    me.session_status ?? "unknown",
  )} session`;

  return {
    ...base,
    id: String(me.identity_id ?? base.id),
    trustLevel,
    verificationStatus,
    loginHistory: Math.max(base.loginHistory, sessionCount),
    connectedApps: Math.max(base.connectedApps, sessionCount),
    summary,
    events: [
      {
        id: id("event"),
        type: "support",
        title: "Backend profile synced",
        detail: summary,
        timestamp: now(),
        severity: "success",
      },
      ...base.events,
    ],
  };
}

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
  const runtime = readRuntimeConfig();
  if (runtime.apiBaseUrl && runtime.accessToken) {
    try {
      const [me, sessions] = await Promise.all([
        requestJson<Record<string, unknown>>("/v1/novaid/me"),
        requestJson<Array<Record<string, unknown>>>("/v1/novaid/sessions"),
      ]);
      return buildBackendProfile(me, sessions);
    } catch (error) {
      if (!runtime.allowMockFallback) {
        throw error;
      }
    }
  }
  return createMockIdentityProfile();
}

export async function beginVerificationFlow(profileId: string): Promise<VerificationRequest> {
  const runtime = readRuntimeConfig();
  if (runtime.apiBaseUrl && runtime.accessToken) {
    try {
      const options = await requestJson<Record<string, unknown>>("/v1/novaid/webauthn/registration/options", {
        method: "POST",
        body: { user_name: profileId },
      });
      const challenge = String(options.challenge_id ?? options.challengeId ?? id("verification"));
      return {
        id: challenge,
        profileId,
        step: "identity_request",
        status: "pending",
        requestedAt: now(),
        reviewedAt: null,
        documentCheck: {
          status: "pending",
          documentType: "NovaID backend challenge",
          country: "AU",
          checkedAt: now(),
        },
        biometricCheck: {
          status: "pending",
          method: "multi",
          confidence: 0,
          checkedAt: now(),
        },
        livenessCheck: {
          status: "pending",
          confidence: 0,
          challenge: challenge,
          checkedAt: now(),
        },
        policyEvaluation: {
          status: "pending",
          score: 0,
          reasons: [`Challenge issued by NovaID backend for ${profileId}`],
          evaluatedAt: now(),
        },
      };
    } catch (error) {
      if (!runtime.allowMockFallback) {
        throw error;
      }
    }
  }

  return {
    id: id("verification"),
    profileId,
    step: "identity_request",
    status: "pending",
    requestedAt: now(),
    reviewedAt: null,
    documentCheck: {
      status: "pending",
      documentType: "Local fallback challenge",
      country: "AU",
      checkedAt: now(),
    },
    biometricCheck: {
      status: "pending",
      method: "multi",
      confidence: 0,
      checkedAt: now(),
    },
    livenessCheck: {
      status: "pending",
      confidence: 0,
      challenge: "local-fallback",
      checkedAt: now(),
    },
    policyEvaluation: {
      status: "pending",
      score: 0,
      reasons: ["Local fallback verification request issued"],
      evaluatedAt: now(),
    },
  };
}

export async function buildAuditPackage(eventIds: string[]): Promise<AuditPackage> {
  const fingerprint = stableFingerprint(eventIds);
  return {
    id: `audit-${fingerprint}`,
    eventIds: [...eventIds],
    replayHash: `replay-${fingerprint}`,
    digitalSignature: `sig-${fingerprint}`,
    createdAt: now(),
  };
}
