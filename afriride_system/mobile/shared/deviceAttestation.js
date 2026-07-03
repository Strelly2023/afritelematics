import { NativeModules, Platform } from "react-native";

let tokenProvider = null;

export function registerAttestationTokenProvider(provider) {
  tokenProvider = provider;
}

export async function attestDevice({ apiRequest, deviceId, testMode }) {
  if (Platform.OS !== "android" && Platform.OS !== "ios") {
    if (testMode) return { trusted: false, skipped: true, reason: "unsupported_platform" };
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
    if (testMode) return { trusted: false, skipped: true, reason: "test_attestation_provider_absent" };
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
