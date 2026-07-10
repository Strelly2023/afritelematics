import { NativeModules, Platform } from "react-native";

let tokenProvider = null;

export function registerAttestationTokenProvider(provider) {
  tokenProvider = provider;
}

function canUsePublicPilotFallback(policy) {
  return policy === "public_pilot_fallback" || policy === "public_pilot_degraded";
}

export async function attestDevice({ apiRequest, deviceId, testMode, policy = "strict" }) {
  if (Platform.OS !== "android" && Platform.OS !== "ios") {
    if (canUsePublicPilotFallback(policy) || testMode) {
      return {
        trusted: false,
        skipped: true,
        reason: "unsupported_platform",
        policy,
      };
    }
    throw new Error("device_attestation_platform_required");
  }
  const nativeProvider =
    tokenProvider ||
    globalThis.__AFRIRIDE_DEVICE_ATTESTATION_TOKEN_PROVIDER__ ||
    (NativeModules.AfriRideIntegrity?.requestToken
      ? ({ nonce, cloudProjectNumber }) =>
          NativeModules.AfriRideIntegrity.requestToken(nonce, cloudProjectNumber)
      : null);
  if (!nativeProvider) {
    if (canUsePublicPilotFallback(policy) || testMode) {
      return {
        trusted: false,
        skipped: true,
        reason: canUsePublicPilotFallback(policy)
          ? "public_pilot_fallback_no_provider"
          : "test_attestation_provider_absent",
        policy,
      };
    }
    throw new Error("native_device_attestation_provider_required");
  }
  const challenge = await apiRequest("/v1/security/attestation/challenge", {
    method: "POST",
    body: { device_id: deviceId, platform: Platform.OS },
  });
  const token = await nativeProvider({
    platform: Platform.OS,
    nonce: challenge.nonce,
    cloudProjectNumber: challenge.cloud_project_number,
  });
  return apiRequest("/v1/security/attestation/verify", {
    method: "POST",
    body: {
      device_id: deviceId,
      platform: Platform.OS,
      nonce: challenge.nonce,
      token,
    },
  });
}
