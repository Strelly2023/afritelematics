export type PilotEvidenceType =
  | "driver_shift_started"
  | "driver_location_event"
  | "network_latency_event"
  | "ride_accept_latency"
  | "gps_accuracy_event"
  | "route_deviation_event"
  | "speed_consistency_event"
  | "gps_signal_loss_event"
  | "app_backgrounded"
  | "app_resumed"
  | "crash_event";

export type PilotEvidenceVerdict = "observed" | "pass" | "violation";

export type PilotEvidenceEvent = {
  type: PilotEvidenceType;
  driverId: string;
  surface: "driver_mobile";
  payload: Record<string, unknown>;
  constraints?: Record<string, unknown>;
  verdict?: PilotEvidenceVerdict;
  capturedAt: string;
};

export type DiagnosticsSnapshot = {
  shiftStarted: boolean;
  locationSamples: number;
  networkSamples: number;
  evidenceSubmitted: number;
  evidenceFailed: number;
  lastEvidenceType?: PilotEvidenceType;
  lastEvidenceAt?: string;
  lastLatencyMs?: number;
  lastGpsAccuracyM?: number;
  lastSpeedKph?: number;
  routeDeviationEvents: number;
  gpsSignalLossEvents: number;
  lastLocation?: {
    latitude: number;
    longitude: number;
  };
  lastError?: string;
};
