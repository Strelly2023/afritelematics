import * as Location from "expo-location";

import type { DiagnosticCheck } from "./diagnosticTypes";

export async function runLocationDiagnostics(): Promise<DiagnosticCheck[]> {
  const foreground = await Location.getForegroundPermissionsAsync().catch(() => null);
  const servicesEnabled = await Location.hasServicesEnabledAsync().catch(() => false);
  return [
    {
      key: "gps_permission",
      label: "GPS permission",
      status: foreground?.granted ? "PASS" : "FAIL",
      safeSummary: foreground?.granted
        ? "Foreground location permission is granted."
        : "Location permission is required before a dispatchable state.",
    },
    {
      key: "location_service",
      label: "Location service",
      status: servicesEnabled ? "PASS" : "FAIL",
      safeSummary: servicesEnabled
        ? "Device location service is enabled."
        : "Enable device location services to continue.",
    },
    {
      key: "background_location",
      label: "Background location",
      status: foreground?.granted ? "READY" : "DEGRADED",
      safeSummary: "Background location is only required for active Driver shifts.",
    },
  ];
}

