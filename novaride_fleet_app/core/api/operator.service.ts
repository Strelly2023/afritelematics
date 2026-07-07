import { apiRequest } from "./client";
import { mockGetOperatorDashboard } from "./mockOperator.service";
import { USE_MOCK_API } from "../config/environment";
import type { OperatorDashboard } from "../models/operator";

type OperatorDashboardResponse = {
  fleet_trust_score: number;
  active_drivers: number;
  verified_rides_today: number;
  evidence_packets_today: number;
  open_replay_exceptions: number;
  replay_exception_rate_pct: number;
  driver_trust_trend: Array<{
    label: string;
    score: number;
  }>;
  public_verification: {
    status: OperatorDashboard["publicVerification"]["status"];
    checks_today: number;
    pass_rate_pct: number;
  };
  pilot_evidence: {
    shift_count: number;
    gps_signal_loss_events: number;
    route_deviation_events: number;
    latency_breaches: number;
  };
};

function mapOperatorDashboard(
  result: OperatorDashboardResponse,
): OperatorDashboard {
  return {
    fleetTrustScore: result.fleet_trust_score,
    activeDrivers: result.active_drivers,
    verifiedRidesToday: result.verified_rides_today,
    evidencePacketsToday: result.evidence_packets_today,
    openReplayExceptions: result.open_replay_exceptions,
    replayExceptionRatePct: result.replay_exception_rate_pct,
    driverTrustTrend: result.driver_trust_trend,
    publicVerification: {
      status: result.public_verification.status,
      checksToday: result.public_verification.checks_today,
      passRatePct: result.public_verification.pass_rate_pct,
    },
    pilotEvidence: {
      shiftCount: result.pilot_evidence.shift_count,
      gpsSignalLossEvents: result.pilot_evidence.gps_signal_loss_events,
      routeDeviationEvents: result.pilot_evidence.route_deviation_events,
      latencyBreaches: result.pilot_evidence.latency_breaches,
    },
  };
}

export async function getOperatorDashboard(): Promise<OperatorDashboard> {
  if (USE_MOCK_API) {
    return mockGetOperatorDashboard();
  }

  const result = await apiRequest<OperatorDashboardResponse>(
    "/v1/operator/dashboard",
  );

  return mapOperatorDashboard(result);
}
