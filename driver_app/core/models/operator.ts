export type OperatorDashboard = {
  fleetTrustScore: number;
  activeDrivers: number;
  verifiedRidesToday: number;
  evidencePacketsToday: number;
  openReplayExceptions: number;
  replayExceptionRatePct: number;
  driverTrustTrend: Array<{
    label: string;
    score: number;
  }>;
  publicVerification: {
    status: "operational" | "degraded" | "offline";
    checksToday: number;
    passRatePct: number;
  };
  pilotEvidence: {
    shiftCount: number;
    gpsSignalLossEvents: number;
    routeDeviationEvents: number;
    latencyBreaches: number;
  };
};
