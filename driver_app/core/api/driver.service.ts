import { apiRequest } from "./client";
import { USE_MOCK_API } from "../config/environment";
import {
  mockGetEarnings,
  mockGetReplayHistory,
  mockGetRideRequests,
  mockRideAction,
  mockSetAvailability,
} from "./mockDriver.service";
import type {
  AvailabilityStatus,
  DriverAvailability,
  DriverReplayHistoryItem,
  DriverRideRequest,
  EarningsSummary,
  TripSnapshot,
} from "../models/driver";
import { PILOT_LATENCY_THRESHOLD_MS } from "../config/environment";
import {
  capturePilotEvidence,
  latencyVerdict,
} from "../services/pilotEvidence.service";

type AvailabilityResponse = {
  driver_id: string;
  status: AvailabilityStatus;
  updated_at?: string;
  trust_score?: number;
  verified_rides?: number;
  replay_consistency_pct?: number;
};

type RideRequestResponse = {
  ride_id: string;
  pickup_text: string;
  dropoff_text: string;
  rider_name?: string;
  status: DriverRideRequest["status"];
  quoted_total_text?: string;
  rider_trust_score?: number;
  eta_text?: string;
};

type TripResponse = {
  ride_id: string;
  status: TripSnapshot["status"];
  rider_name?: string;
  pickup_text?: string;
  dropoff_text?: string;
  next_instruction?: string;
  trust_score?: number;
  replay_verified?: boolean;
};

type EarningsResponse = {
  driver_id: string;
  period_label: string;
  total_text: string;
  ride_count: number;
  source: "core_system";
  verified_ride_count?: number;
  dispute_count?: number;
  trust_score?: number;
};

type ReplayHistoryResponse = {
  items?: Array<{
    ride_id: string;
    replay_id: string;
    replay_verified: boolean;
    completed_at?: string;
    trust_score?: number;
    timeline_events?: DriverReplayHistoryItem["timelineEvents"];
  }>;
  rides?: Array<{
    ride_id: string;
    replay_id: string;
    replay_verified: boolean;
    completed_at?: string;
    trust_score?: number;
    timeline_events?: DriverReplayHistoryItem["timelineEvents"];
  }>;
};

export async function updateDriverLocation(
  driverId: string,
  position: {
    latitude: number;
    longitude: number;
    heading?: number | null;
    timestamp: number;
  },
): Promise<void> {
  if (USE_MOCK_API) return;
  await apiRequest("/v1/drivers/location", {
    method: "POST",
    body: {
      driver_id: driverId,
      lat: position.latitude,
      lng: position.longitude,
      heading: position.heading ?? null,
      timestamp: new Date(position.timestamp).toISOString(),
    },
  });
}

function mapAvailability(result: AvailabilityResponse): DriverAvailability {
  return {
    driverId: result.driver_id,
    status: result.status,
    updatedAt: result.updated_at,
    trustScore: result.trust_score,
    verifiedRides: result.verified_rides,
    replayConsistencyPct: result.replay_consistency_pct,
  };
}

function mapTrip(result: TripResponse): TripSnapshot {
  return {
    rideId: result.ride_id,
    status: result.status,
    riderName: result.rider_name,
    pickupText: result.pickup_text,
    dropoffText: result.dropoff_text,
    nextInstruction: result.next_instruction,
    trustScore: result.trust_score,
    replayVerified: result.replay_verified,
  };
}

export function mapRealtimeTrip(data: Record<string, unknown>): TripSnapshot | null {
  const status = data.status;
  const rideId = data.ride_id;
  if (
    typeof rideId !== "string" ||
    !["accepted", "arrived", "started", "completed", "cancelled"].includes(String(status))
  ) {
    return null;
  }
  return mapTrip(data as unknown as TripResponse);
}

export async function setAvailability(
  driverId: string,
  status: AvailabilityStatus,
): Promise<DriverAvailability> {
  if (USE_MOCK_API) {
    return mockSetAvailability(driverId, status);
  }

  const result = await apiRequest<AvailabilityResponse>(
    `/v1/driver/${encodeURIComponent(driverId)}/availability`,
    {
      method: "POST",
      headers: {
        "Idempotency-Key": `availability:${encodeURIComponent(driverId)}:${status}`,
      },
      body: {
        status,
      },
    },
  );

  return mapAvailability(result);
}

export async function getAvailability(
  driverId: string,
): Promise<DriverAvailability> {
  if (USE_MOCK_API) {
    return mockSetAvailability(driverId, "offline");
  }

  const result = await apiRequest<AvailabilityResponse>(
    `/v1/driver/${encodeURIComponent(driverId)}/availability`,
  );

  return mapAvailability(result);
}

export async function getRideRequests(
  driverId: string,
): Promise<DriverRideRequest[]> {
  if (USE_MOCK_API) {
    return mockGetRideRequests();
  }

  const result = await apiRequest<{
    items?: RideRequestResponse[];
    rides?: RideRequestResponse[];
  }>(
    `/v1/driver/${encodeURIComponent(driverId)}/ride-queue`,
  );

  return (result.items || result.rides || []).map((ride) => ({
    rideId: ride.ride_id,
    pickupText: ride.pickup_text,
    dropoffText: ride.dropoff_text,
    riderName: ride.rider_name,
    status: ride.status,
    quotedTotalText: ride.quoted_total_text,
    riderTrustScore: ride.rider_trust_score,
    etaText: ride.eta_text,
  }));
}

export async function acceptRide(
  rideId: string,
  driverId = "",
): Promise<TripSnapshot> {
  const startedAt = Date.now();
  if (USE_MOCK_API) {
    return mockRideAction(rideId, "accepted");
  }

  const result = await apiRequest<TripResponse>(
    `/v1/driver/rides/${encodeURIComponent(rideId)}/accept`,
    {
      method: "POST",
      headers: {
        "Idempotency-Key": `accept:${encodeURIComponent(driverId)}:${encodeURIComponent(rideId)}`,
      },
      body: { driver_id: driverId },
    },
  );

  const latencyMs = Date.now() - startedAt;
  void capturePilotEvidence(
    driverId,
    "ride_accept_latency",
    {
      ride_id: rideId,
      latency_ms: latencyMs,
      status: result.status,
    },
    { expected_max_latency_ms: PILOT_LATENCY_THRESHOLD_MS },
    latencyVerdict(latencyMs),
  ).catch(() => undefined);

  return mapTrip(result);
}

export async function rejectRide(
  rideId: string,
  driverId = "",
): Promise<TripSnapshot> {
  if (USE_MOCK_API) {
    return mockRideAction(rideId, "cancelled");
  }

  const result = await apiRequest<TripResponse>(
    `/v1/driver/rides/${encodeURIComponent(rideId)}/reject`,
    {
      method: "POST",
      headers: {
        "Idempotency-Key": `reject:${encodeURIComponent(driverId)}:${encodeURIComponent(rideId)}`,
      },
      body: { driver_id: driverId },
    },
  );

  return mapTrip(result);
}

export async function markArrived(
  rideId: string,
  driverId = "",
): Promise<TripSnapshot> {
  if (USE_MOCK_API) {
    return mockRideAction(rideId, "arrived");
  }

  const result = await apiRequest<TripResponse>(
    `/v1/driver/rides/${encodeURIComponent(rideId)}/arrive`,
    {
      method: "POST",
      headers: {
        "Idempotency-Key": `arrive:${encodeURIComponent(driverId)}:${encodeURIComponent(rideId)}`,
      },
      body: { driver_id: driverId },
    },
  );

  return mapTrip(result);
}

export async function startTrip(
  rideId: string,
  driverId = "",
): Promise<TripSnapshot> {
  if (USE_MOCK_API) {
    return mockRideAction(rideId, "started");
  }

  const result = await apiRequest<TripResponse>(
    `/v1/driver/rides/${encodeURIComponent(rideId)}/start`,
    {
      method: "POST",
      headers: {
        "Idempotency-Key": `start:${encodeURIComponent(driverId)}:${encodeURIComponent(rideId)}`,
      },
      body: { driver_id: driverId },
    },
  );

  return mapTrip(result);
}

export async function completeTrip(
  rideId: string,
  driverId = "",
): Promise<TripSnapshot> {
  if (USE_MOCK_API) {
    return mockRideAction(rideId, "completed");
  }

  const result = await apiRequest<TripResponse>(
    `/v1/driver/rides/${encodeURIComponent(rideId)}/complete`,
    {
      method: "POST",
      headers: {
        "Idempotency-Key": `complete:${encodeURIComponent(driverId)}:${encodeURIComponent(rideId)}`,
      },
      body: { driver_id: driverId },
    },
  );

  return mapTrip(result);
}

export async function getEarnings(driverId: string): Promise<EarningsSummary> {
  if (USE_MOCK_API) {
    return mockGetEarnings();
  }

  const result = await apiRequest<EarningsResponse>(
    `/v1/driver/${encodeURIComponent(driverId)}/earnings`,
  );

  return {
    driverId: result.driver_id,
    periodLabel: result.period_label,
    totalText: result.total_text,
    rideCount: result.ride_count,
    source: result.source,
    verifiedRideCount: result.verified_ride_count,
    disputeCount: result.dispute_count,
    trustScore: result.trust_score,
  };
}

export async function getReplayHistory(
  driverId: string,
): Promise<DriverReplayHistoryItem[]> {
  if (USE_MOCK_API) {
    return mockGetReplayHistory();
  }

  const result = await apiRequest<ReplayHistoryResponse>(
    `/v1/driver/${encodeURIComponent(driverId)}/replay-history`,
  );

  return (result.items || result.rides || []).map((ride) => ({
    rideId: ride.ride_id,
    replayId: ride.replay_id,
    replayVerified: ride.replay_verified,
    completedAt: ride.completed_at,
    trustScore: ride.trust_score,
    timelineEvents: ride.timeline_events,
  }));
}
