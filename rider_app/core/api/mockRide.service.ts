import type {
  LedgerReceiptSummary,
  PriceExplanation,
  RequestRidePayload,
  RideReceipt,
  RideReplay,
  RideRequestResult,
  RideStatusSnapshot,
} from "../models/ride";
import type { PassengerIntelligenceFeed } from "../models/intelligence";

const MOCK_RIDE_ID = "ride.mock.001";

export async function mockRequestRide(
  payload: RequestRidePayload,
): Promise<RideRequestResult> {
  return {
    rideId: MOCK_RIDE_ID,
    status: payload.pickup && payload.dropoff ? "confirmed" : "requested",
    quotedTotal: "UGX 12,500",
    currency: "UGX",
    confirmationToken: "mock-confirmation-token",
    trustScore: 92,
    rideType: "Economy",
  };
}

export async function mockGetRideStatus(
  rideId: string,
): Promise<RideStatusSnapshot> {
  return {
    rideId,
    status: "completed",
    driverName: "Amina K.",
    vehicleLabel: "Toyota Axio UBA 421X",
    etaText: "Arrived",
    locationText: "Completed at Nakasero",
    driverTrustScore: 94,
    trustScore: 92,
  };
}

export async function mockGetReceipt(rideId: string): Promise<RideReceipt> {
  return {
    rideId,
    receiptId: "receipt.mock.001",
    status: "completed",
    distanceText: "4.2 km",
    totalText: "UGX 12,500",
    startedAt: "2026-05-31T09:00:00+10:00",
    completedAt: "2026-05-31T09:18:00+10:00",
    trustScore: 92,
    verificationStatus: "PASSED",
    replayMatch: true,
    evidenceComplete: true,
  };
}

export async function mockGetReplay(rideId: string): Promise<RideReplay> {
  return {
    rideId,
    replayId: "replay.mock.001",
    replayVerified: true,
    routeSummary: "Kampala Road to Nakasero",
    explanationSteps: [
      "Ride request was accepted through the API contract.",
      "Trip status was confirmed by the system evidence stream.",
      "Completion evidence was verified before receipt display.",
    ],
    timelineEvents: [
      { label: "REQUESTED", verified: true },
      { label: "DRIVER_ACCEPTED", verified: true },
      { label: "DRIVER_MATCHED", verified: true },
      { label: "ARRIVING", verified: true },
      { label: "ARRIVED", verified: true },
      { label: "STARTED", verified: true },
      { label: "COMPLETED", verified: true },
    ],
  };
}

export async function mockGetLedgerReceipt(
  rideId: string,
): Promise<LedgerReceiptSummary> {
  return {
    receiptId: "ledger-receipt.mock.001",
    verdict: "VALID",
    receiptHash:
      "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    eventCount: 7,
    rootHash:
      "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    hashMode: "sha256_canonical_chain",
    signatureMode: "rsa_pss_sha256",
    allSignaturesValid: true,
    allIdentitiesVerified: true,
    replayValid: true,
  };
}

export async function mockGetPriceExplanation(
  rideId: string,
): Promise<PriceExplanation> {
  return {
    rideId,
    priceExplanation:
      "The final amount is returned as a core-system explanation and displayed without app-side recalculation.",
    source: "core_system",
    lineItems: [
      { label: "Base fare", amountText: "UGX 5,000" },
      { label: "Distance", amountText: "UGX 7,500" },
      { label: "Total", amountText: "UGX 12,500" },
    ],
  };
}

export async function mockGetPassengerIntelligence(): Promise<PassengerIntelligenceFeed> {
  return {
    view: "novaride_mobile_passenger_intelligence",
    organization_id: "afritech-core",
    passenger_id: "rider.mock.001",
    system_status: "stable",
    safety_score: 96,
    demand: "moderate",
    eta_confidence: "high",
    alerts: ["Demand is moderate", "Driver matching remains stable"],
    trust: {
      driver_verified: true,
      vehicle_verified: true,
      payment_secure: true,
    },
    autonomous_mode: true,
    predictive_positioning: {
      mode: "fully_autonomous",
      target_zone: "CBD",
      confidence: 0.91,
      instruction: "Driver supply is strongest in CBD",
      reason: "Stable demand and verified supply support predictive positioning",
      projection_only: true,
      read_only: true,
    },
    city_automation: {
      mode: "zero_operator",
      zero_operator_mode: true,
      coverage_score: 84,
      active_drivers: 12,
      active_rides: 18,
      city_zones: ["CBD", "Docklands", "Southbank"],
      recommended_zone: "CBD",
      instruction: "Keep city-wide automation active around CBD",
      reason: "City coverage, trust, and supply support zero-operator mode",
      prediction: {
        city_zone_count: 3,
        city_trust_score: 95,
        coverage_score: 84,
        demand_level: "high",
      },
      projection_only: true,
      read_only: true,
    },
    multi_city_orchestration: {
      mode: "global_zero_operator",
      city_count: 3,
      active_city_count: 3,
      global_coverage_score: 87,
      global_trust_score: 95,
      instruction: "Keep multi-city orchestration active and optimize supply across CBD and adjacent cities",
      reason: "Global coverage and supply are sufficient for zero-operator orchestration",
      prediction: {
        city_count: 3,
        active_city_count: 3,
        coverage_score: 87,
        trust_score: 95,
        demand_level: "high",
      },
      projection_only: true,
      read_only: true,
    },
    digital_twin: {
      mode: "global_closed_loop",
      live_sync_score: 91,
      twin_health_score: 93,
      live_state: {
        active_drivers: 12,
        active_rides: 18,
        zone: "CBD",
        demand_level: "high",
        trust_score: 97,
        city_coverage_score: 84,
        global_coverage_score: 87,
      },
      prediction: {
        next_state: "global_zero_operator",
        confidence: 0.93,
        trust_score: 95,
        evidence_coverage: 91,
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
        first: 81,
        latest: 93,
        delta: 12,
        slope: 2.4,
        direction: "rising",
        average: 87,
        minimum: 81,
        maximum: 93,
      },
      recommendations: ["Preserve the current control band.", "Keep the next review cycle active."],
      recalibration_notes: ["Outcome band strong", "Learning band strong", "Calibrated confidence 93%"],
      watch_items: ["Maintain the current observation loop."],
      outcome_score: 93,
      measurement_summary: "Outcome score 93/100 from trust 95, replay health 95, and evidence coverage 91%.",
      projection_only: true,
      read_only: true,
    },
    projection_only: true,
    read_only: true,
    created_at: "2026-06-02T09:00:00+10:00",
  };
}
