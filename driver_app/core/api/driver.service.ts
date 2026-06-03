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

type AvailabilityResponse = {
  driver_id: string;
  status: AvailabilityStatus;
  updated_at?: string;
};

type RideRequestResponse = {
  ride_id: string;
  pickup_text: string;
  dropoff_text: string;
  rider_name?: string;
  status: DriverRideRequest["status"];
  quoted_total_text?: string;
};

type TripResponse = {
  ride_id: string;
  status: TripSnapshot["status"];
  rider_name?: string;
  pickup_text?: string;
  dropoff_text?: string;
  next_instruction?: string;
};

type EarningsResponse = {
  driver_id: string;
  period_label: string;
  total_text: string;
  ride_count: number;
  source: "core_system";
};

type ReplayHistoryResponse = {
  rides: Array<{
    ride_id: string;
    replay_id: string;
    replay_verified: boolean;
    completed_at?: string;
  }>;
};

function mapAvailability(result: AvailabilityResponse): DriverAvailability {
  return {
    driverId: result.driver_id,
    status: result.status,
    updatedAt: result.updated_at,
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
  };
}

export async function setAvailability(
  driverId: string,
  status: AvailabilityStatus,
): Promise<DriverAvailability> {
  if (USE_MOCK_API) {
    return mockSetAvailability(driverId, status);
  }

  const result = await apiRequest<AvailabilityResponse>("/driver/availability", {
    method: "POST",
    body: {
      driver_id: driverId,
      status,
    },
  });

  return mapAvailability(result);
}

export async function getRideRequests(
  driverId: string,
): Promise<DriverRideRequest[]> {
  if (USE_MOCK_API) {
    return mockGetRideRequests();
  }

  const result = await apiRequest<{ rides: RideRequestResponse[] }>(
    `/driver/${encodeURIComponent(driverId)}/queue`,
  );

  return result.rides.map((ride) => ({
    rideId: ride.ride_id,
    pickupText: ride.pickup_text,
    dropoffText: ride.dropoff_text,
    riderName: ride.rider_name,
    status: ride.status,
    quotedTotalText: ride.quoted_total_text,
  }));
}

export async function acceptRide(
  rideId: string,
  driverId = "D001",
): Promise<TripSnapshot> {
  if (USE_MOCK_API) {
    return mockRideAction(rideId, "accepted");
  }

  const result = await apiRequest<TripResponse>(`/ride/${rideId}/accept`, {
    method: "POST",
    body: { driver_id: driverId },
  });

  return mapTrip(result);
}

export async function rejectRide(
  rideId: string,
  driverId = "D001",
): Promise<TripSnapshot> {
  if (USE_MOCK_API) {
    return mockRideAction(rideId, "cancelled");
  }

  const result = await apiRequest<TripResponse>(`/ride/${rideId}/reject`, {
    method: "POST",
    body: { driver_id: driverId },
  });

  return mapTrip(result);
}

export async function markArrived(rideId: string): Promise<TripSnapshot> {
  if (USE_MOCK_API) {
    return mockRideAction(rideId, "arrived");
  }

  const result = await apiRequest<TripResponse>("/ride/arrive", {
    method: "POST",
    body: { ride_id: rideId },
  });

  return mapTrip(result);
}

export async function startTrip(
  rideId: string,
  driverId = "D001",
): Promise<TripSnapshot> {
  if (USE_MOCK_API) {
    return mockRideAction(rideId, "started");
  }

  const result = await apiRequest<TripResponse>(`/ride/${rideId}/start`, {
    method: "POST",
    body: { driver_id: driverId },
  });

  return mapTrip(result);
}

export async function completeTrip(
  rideId: string,
  driverId = "D001",
): Promise<TripSnapshot> {
  if (USE_MOCK_API) {
    return mockRideAction(rideId, "completed");
  }

  const result = await apiRequest<TripResponse>(`/ride/${rideId}/complete`, {
    method: "POST",
    body: { driver_id: driverId },
  });

  return mapTrip(result);
}

export async function getEarnings(driverId: string): Promise<EarningsSummary> {
  if (USE_MOCK_API) {
    return mockGetEarnings();
  }

  const result = await apiRequest<EarningsResponse>(
    `/driver/${encodeURIComponent(driverId)}/earnings`,
  );

  return {
    driverId: result.driver_id,
    periodLabel: result.period_label,
    totalText: result.total_text,
    rideCount: result.ride_count,
    source: result.source,
  };
}

export async function getReplayHistory(
  driverId: string,
): Promise<DriverReplayHistoryItem[]> {
  if (USE_MOCK_API) {
    return mockGetReplayHistory();
  }

  const result = await apiRequest<ReplayHistoryResponse>(
    `/driver/replay-history?driver_id=${encodeURIComponent(driverId)}`,
  );

  return result.rides.map((ride) => ({
    rideId: ride.ride_id,
    replayId: ride.replay_id,
    replayVerified: ride.replay_verified,
    completedAt: ride.completed_at,
  }));
}
