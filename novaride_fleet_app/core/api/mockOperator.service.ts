import type { OperatorDashboard } from "../models/operator";

export async function mockGetOperatorDashboard(): Promise<OperatorDashboard> {
  return {
    fleetTrustScore: 96,
    activeDrivers: 12,
    verifiedRidesToday: 48,
    evidencePacketsToday: 212,
    openReplayExceptions: 1,
    replayExceptionRatePct: 0.8,
    driverTrustTrend: [
      { label: "Mon", score: 93 },
      { label: "Tue", score: 94 },
      { label: "Wed", score: 95 },
      { label: "Thu", score: 96 },
    ],
    publicVerification: {
      status: "operational",
      checksToday: 37,
      passRatePct: 100,
    },
    pilotEvidence: {
      shiftCount: 7,
      gpsSignalLossEvents: 0,
      routeDeviationEvents: 1,
      latencyBreaches: 0,
    },
  };
}
