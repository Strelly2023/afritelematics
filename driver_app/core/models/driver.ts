export type AvailabilityStatus = "available" | "offline";

export type RideRequestStatus = "pending" | "accepted" | "rejected";

export type TripStatus =
  | "accepted"
  | "arrived"
  | "started"
  | "completed"
  | "cancelled";

export type DriverAvailability = {
  driverId: string;
  status: AvailabilityStatus;
  updatedAt?: string;
};

export type DriverRideRequest = {
  rideId: string;
  pickupText: string;
  dropoffText: string;
  riderName?: string;
  status: RideRequestStatus;
  quotedTotalText?: string;
};

export type TripSnapshot = {
  rideId: string;
  status: TripStatus;
  riderName?: string;
  pickupText?: string;
  dropoffText?: string;
  nextInstruction?: string;
};

export type EarningsSummary = {
  driverId: string;
  periodLabel: string;
  totalText: string;
  rideCount: number;
  source: "core_system";
};

export type DriverReplayHistoryItem = {
  rideId: string;
  replayId: string;
  replayVerified: boolean;
  completedAt?: string;
};
