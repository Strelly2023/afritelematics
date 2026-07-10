import {
  API_BASE_URL,
  API_HEALTH_PATH,
  APP_VERSION,
  RELEASE_CHANNEL,
  RUNTIME_ENVIRONMENT,
} from "./environment";

export const runtimeConfig = {
  appName: "NovaRide Rider",
  releaseVersion: APP_VERSION,
  versionCode: 5,
  releaseChannel: RELEASE_CHANNEL,
  environment: RUNTIME_ENVIRONMENT,
  apiBaseUrl: API_BASE_URL,
  apiHealthUrl: `${API_BASE_URL}${API_HEALTH_PATH}`,
  authenticationUrl: `${API_BASE_URL}/v1/auth/token`,
  buildTimestamp: process.env.EXPO_PUBLIC_NOVARIDE_BUILD_TIMESTAMP || "build-time-generated",
  gitCommit: process.env.EXPO_PUBLIC_NOVARIDE_GIT_COMMIT || "local",
  buildId: process.env.EXPO_PUBLIC_NOVARIDE_BUILD_ID || `novaride-rider-${APP_VERSION}`,
  apkSha256: process.env.EXPO_PUBLIC_NOVARIDE_APK_SHA256 || "published-with-release-manifest",
} as const;
