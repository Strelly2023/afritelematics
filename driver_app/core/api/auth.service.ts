import { apiRequest } from "./client";
import { setAuthSession } from "./session";
import { ATTESTATION_POLICY, DEVICE_ID, ORGANIZATION_ID, TEST_MODE } from "../config/environment";
import { attestDevice } from "../../../afriride_system/mobile/shared/deviceAttestation";

type AuthRole = "CUSTOMER" | "DRIVER" | "OPERATOR";

type AuthResponse = {
  token: string;
};

type JwtPayload = {
  sub?: unknown;
  role?: unknown;
};

export function extractAuthIdentity(token: string, fallback = ""): string {
  try {
    const [, encodedPayload] = token.split(".");
    if (!encodedPayload) return fallback;
    const normalizedPayload = encodedPayload.replace(/-/g, "+").replace(/_/g, "/");
    const paddedPayload = normalizedPayload.padEnd(
      normalizedPayload.length + ((4 - (normalizedPayload.length % 4)) % 4),
      "=",
    );
    const decoder = (globalThis as { atob?: (value: string) => string }).atob;
    if (!decoder) return fallback;
    const payload = JSON.parse(decoder(paddedPayload)) as JwtPayload;
    const sub = typeof payload.sub === "string" ? payload.sub.trim() : "";
    return sub || fallback;
  } catch {
    return fallback;
  }
}

export async function loginPilot(
  userId: string,
  role: AuthRole,
  organizationId: string = ORGANIZATION_ID,
): Promise<string> {
  const attestation = await attestDevice({
    apiRequest,
    deviceId: DEVICE_ID,
    testMode: TEST_MODE,
    policy: ATTESTATION_POLICY,
  });
  const result = await apiRequest<AuthResponse>("/v1/auth/token", {
    method: "POST",
    body: {
      user_id: userId,
      role,
      organization_id: organizationId,
    },
  });

  const driverId = extractAuthIdentity(result.token, TEST_MODE ? userId : "");
  if (!driverId && !TEST_MODE) {
    throw new Error("Driver identity is unavailable. Sign in again.");
  }
  await setAuthSession(result.token, {
    driverId,
    role,
    organizationId,
    attestation_policy: ATTESTATION_POLICY,
    attestation_state: attestation.skipped ? "public_pilot_fallback" : "verified",
    attestation_reason: attestation.skipped ? attestation.reason : null,
  });
  return result.token;
}
