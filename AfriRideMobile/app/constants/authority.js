export const MOBILE_AUTHORITY_BOUNDARY = {
  backendProofDecides: true,
  replayVerifies: true,
  apiExposesConfirmedState: true,
  mobileDisplays: true,
  mobileInventsTruth: false,
  mobileInfersReplayValidity: false,
  mobileMutatesCanonicalState: false,
};

export const AUTHORITY_RULES = Object.freeze({
  MOBILE_IS_DISPLAY_SURFACE: true,
  BACKEND_IS_SOURCE_OF_TRUTH: true,
  REPLAY_REQUIRED_FOR_VALIDATION: true,
  UI_MUST_NOT_INFER_TRUTH: true,
  UI_MUST_DISPLAY_CONFIRMED_STATE_ONLY: true,
});

export function assertBackendConfirmed(response) {
  if (!response || response.error || response.status === "INVALID") {
    throw new Error("Backend confirmation required before display");
  }
  return response;
}
