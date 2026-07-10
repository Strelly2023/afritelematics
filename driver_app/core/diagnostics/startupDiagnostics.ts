import { getPendingDriverQueueCount } from "../services/mobility.service";
import { runApiDiagnostics } from "./apiDiagnostics";
import { runBuildDiagnostics } from "./buildDiagnostics";
import {
  DRIVER_RECOVERY_ACTIONS,
  type StartupDiagnosticSummary,
} from "./diagnosticTypes";
import { runLocationDiagnostics } from "./locationDiagnostics";
import { runNetworkDiagnostics } from "./networkDiagnostics";

export async function runStartupDiagnostics(): Promise<StartupDiagnosticSummary> {
  const [network, api, location] = await Promise.all([
    runNetworkDiagnostics(),
    runApiDiagnostics(),
    runLocationDiagnostics(),
  ]);
  const pendingSync = await getPendingDriverQueueCount().catch(() => -1);

  return {
    generatedAt: new Date().toISOString(),
    checks: [
      ...runBuildDiagnostics(),
      ...network,
      ...api,
      ...location,
      {
        key: "offline_queue",
        label: "Offline queue",
        status: pendingSync >= 0 ? "READY" : "DEGRADED",
        safeSummary:
          pendingSync >= 0
            ? `Offline queue ready. Pending changes: ${pendingSync}.`
            : "Offline queue could not be checked.",
      },
    ],
    recoveryActions: [...DRIVER_RECOVERY_ACTIONS],
  };
}
