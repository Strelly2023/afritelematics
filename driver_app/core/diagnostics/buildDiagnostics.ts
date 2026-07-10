import { runtimeConfig } from "../config/runtimeConfig";
import type { DiagnosticCheck } from "./diagnosticTypes";

export function runBuildDiagnostics(): DiagnosticCheck[] {
  return [
    {
      key: "app_version",
      label: "App version",
      status: runtimeConfig.releaseVersion === "2026.1.3" ? "PASS" : "FAIL",
      safeSummary: `${runtimeConfig.appName} ${runtimeConfig.releaseVersion}`,
      technicalReference: `versionCode=${runtimeConfig.versionCode} buildId=${runtimeConfig.buildId}`,
    },
    {
      key: "release_channel",
      label: "Release channel",
      status: runtimeConfig.releaseChannel === "PUBLIC_PILOT" ? "PASS" : "FAIL",
      safeSummary: `${runtimeConfig.releaseChannel} / ${runtimeConfig.environment}`,
    },
    {
      key: "device_trust",
      label: "Device trust",
      status: "READY",
      safeSummary: "Device trust checks are available for protected diagnostics.",
    },
  ];
}
