import type {
  DriverAvailability,
  DriverReplayHistoryItem,
  DriverRideRequest,
  EarningsSummary,
  TripSnapshot,
} from "../models/driver";
import type { DriverIntelligenceFeed } from "../models/intelligence";

const MOCK_DRIVER_ID = "driver.mock.001";
const MOCK_RIDE_ID = "ride.driver.mock.001";

export async function mockSetAvailability(
  driverId: string,
  status: DriverAvailability["status"],
): Promise<DriverAvailability> {
  return {
    driverId,
    status,
    updatedAt: "2026-06-02T09:00:00+10:00",
    trustScore: 94,
    verifiedRides: 152,
    replayConsistencyPct: 100,
  };
}

export async function mockGetRideRequests(): Promise<DriverRideRequest[]> {
  return [
    {
      rideId: MOCK_RIDE_ID,
      pickupText: "Kampala Road",
      dropoffText: "Nakasero",
      riderName: "Mirembe",
      riderTrustScore: 91,
      status: "pending",
      quotedTotalText: "UGX 12,500",
      etaText: "15 min",
    },
  ];
}

export async function mockRideAction(
  rideId: string,
  status: TripSnapshot["status"],
): Promise<TripSnapshot> {
  return {
    rideId,
    status,
    riderName: "Mirembe",
    pickupText: "Kampala Road",
    dropoffText: "Nakasero",
    nextInstruction: "Follow the system-provided trip state.",
    trustScore: 94,
    replayVerified: status === "completed",
  };
}

export async function mockGetEarnings(): Promise<EarningsSummary> {
  return {
    driverId: MOCK_DRIVER_ID,
    periodLabel: "Today",
    totalText: "UGX 12,500",
    rideCount: 1,
    source: "core_system",
    verifiedRideCount: 1,
    disputeCount: 0,
    trustScore: 94,
  };
}

export async function mockGetReplayHistory(): Promise<DriverReplayHistoryItem[]> {
  return [
    {
      rideId: MOCK_RIDE_ID,
      replayId: "replay.driver.mock.001",
      replayVerified: true,
      completedAt: "2026-06-02T09:24:00+10:00",
      trustScore: 94,
      timelineEvents: ["REQUESTED", "ACCEPTED", "ARRIVED", "STARTED", "COMPLETED"],
    },
  ];
}

export async function mockGetDriverIntelligence(): Promise<DriverIntelligenceFeed> {
  return {
    view: "novaride_mobile_driver_intelligence",
    organization_id: "afritech-core",
    driver_id: MOCK_DRIVER_ID,
    status: "online",
    zone: "CBD",
    demand_level: "high",
    surge: 1.8,
    alerts: ["High demand in CBD", "Move closer to verified pickup zones"],
    compliance: {
      vehicle: "verified",
      documents: "valid",
      inspection: "passed",
    },
    trust_score: 98,
    autonomous_mode: true,
    predictive_positioning: {
      mode: "fully_autonomous",
      target_zone: "CBD",
      confidence: 0.93,
      instruction: "Move toward CBD now",
      reason: "High demand and trusted supply support autonomous positioning",
      projection_only: true,
      read_only: true,
    },
    city_automation: {
      mode: "zero_operator",
      zero_operator_mode: true,
      coverage_score: 86,
      active_drivers: 12,
      active_rides: 18,
      city_zones: ["CBD", "Docklands", "Southbank"],
      recommended_zone: "CBD",
      instruction: "Keep city-wide automation active around CBD",
      reason: "City coverage, trust, and supply support zero-operator mode",
      prediction: {
        city_zone_count: 3,
        city_trust_score: 96,
        coverage_score: 86,
        demand_level: "high",
      },
      projection_only: true,
      read_only: true,
    },
    multi_city_orchestration: {
      mode: "global_zero_operator",
      city_count: 3,
      active_city_count: 3,
      global_coverage_score: 88,
      global_trust_score: 96,
      instruction: "Keep multi-city orchestration active and optimize supply across CBD and adjacent cities",
      reason: "Global coverage and supply are sufficient for zero-operator orchestration",
      prediction: {
        city_count: 3,
        active_city_count: 3,
        coverage_score: 88,
        trust_score: 96,
        demand_level: "high",
      },
      projection_only: true,
      read_only: true,
    },
    digital_twin: {
      mode: "global_closed_loop",
      live_sync_score: 92,
      twin_health_score: 94,
      live_state: {
        active_drivers: 12,
        active_rides: 18,
        zone: "CBD",
        demand_level: "high",
        trust_score: 98,
        city_coverage_score: 86,
        global_coverage_score: 88,
      },
      prediction: {
        next_state: "global_zero_operator",
        confidence: 0.94,
        trust_score: 96,
        evidence_coverage: 92,
        exception_pressure: 1,
      },
      recommendation: "Keep multi-city orchestration active and optimize supply across CBD and adjacent cities",
      reason: "The digital twin mirrors live supply, trust, and learning signals in projection-only mode",
      projection_only: true,
      read_only: true,
    },
    self_improving_loop: {
      mode: "learning",
      cycle: ["observe", "decide", "recommend", "measure_outcome", "learn", "recalibrate"],
      band: "strong",
      trend: {
        count: 6,
        first: 82,
        latest: 94,
        delta: 12,
        slope: 2.4,
        direction: "rising",
        average: 88,
        minimum: 82,
        maximum: 94,
      },
      recommendations: ["Preserve the current control band.", "Keep the next review cycle active."],
      recalibration_notes: ["Outcome band strong", "Learning band strong", "Calibrated confidence 94%"],
      watch_items: ["Maintain the current observation loop."],
      outcome_score: 94,
      measurement_summary: "Outcome score 94/100 from trust 96, replay health 95, and evidence coverage 92%.",
      projection_only: true,
      read_only: true,
    },
    recommendation: "Move toward CBD now",
    projection_only: true,
    read_only: true,
    created_at: "2026-06-02T09:00:00+10:00",
  };
}
