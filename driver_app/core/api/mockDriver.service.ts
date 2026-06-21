import type {
  DriverAvailability,
  DriverReplayHistoryItem,
  DriverRideRequest,
  EarningsSummary,
  TripSnapshot,
} from "../models/driver";

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
