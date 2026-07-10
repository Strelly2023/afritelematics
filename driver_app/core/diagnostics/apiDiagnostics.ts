import { API_BASE_URL } from "../config/environment";
import { runApiConnectivityDiagnostics } from "../api/client";
import type { DiagnosticCheck } from "./diagnosticTypes";

export async function runApiDiagnostics(): Promise<DiagnosticCheck[]> {
  const checks = await runApiConnectivityDiagnostics();
  const mapped = checks.map((check): DiagnosticCheck => ({
    key: check.label.toLowerCase().replace(/\s+/g, "_"),
    label: check.label,
    status: check.status === "pass" ? "PASS" : "FAIL",
    safeSummary:
      check.status === "pass"
        ? `${check.label} passed.`
        : `${check.label} failed. Use Retry or Contact support if this continues.`,
    technicalReference: check.detail,
  }));

  return [
    {
      key: "api_base_url",
      label: "API",
      status: API_BASE_URL === "https://api.afritechnology.com" ? "PASS" : "FAIL",
      safeSummary: API_BASE_URL,
    },
    ...mapped,
  ];
}

