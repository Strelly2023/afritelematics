export type DiagnosticStatus = "PASS" | "FAIL" | "READY" | "DEGRADED" | "UNKNOWN";

export type DiagnosticCheck = {
  key: string;
  label: string;
  status: DiagnosticStatus;
  safeSummary: string;
  technicalReference?: string;
};

export type StartupDiagnosticSummary = {
  generatedAt: string;
  checks: DiagnosticCheck[];
  recoveryActions: string[];
};

export const DRIVER_RECOVERY_ACTIONS = [
  "Retry",
  "Open network settings",
  "Open location settings",
  "Re-authenticate",
  "Copy diagnostic reference",
  "Continue offline when safe",
  "Contact support",
] as const;

