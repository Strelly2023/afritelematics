import * as Network from "expo-network";

import type { DiagnosticCheck } from "./diagnosticTypes";

export async function runNetworkDiagnostics(): Promise<DiagnosticCheck[]> {
  const state = await Network.getNetworkStateAsync().catch(() => null);
  return [
    {
      key: "internet",
      label: "Internet",
      status: state?.isConnected ? "PASS" : "FAIL",
      safeSummary: state?.isConnected ? "Device network is connected." : "No active device network.",
    },
    {
      key: "dns",
      label: "DNS",
      status: state?.isInternetReachable === false ? "FAIL" : "UNKNOWN",
      safeSummary:
        state?.isInternetReachable === false
          ? "Internet reachability is unavailable."
          : "DNS is checked by the API health request.",
    },
  ];
}

