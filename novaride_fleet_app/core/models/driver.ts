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
  trustScore?: number;
  verifiedRides?: number;
  replayConsistencyPct?: number;
};

export type DriverRideRequest = {
  rideId: string;
  pickupText: string;
  dropoffText: string;
  riderName?: string;
  riderTrustScore?: number;
  status: RideRequestStatus;
  quotedTotalText?: string;
  etaText?: string;
};

export type TripSnapshot = {
  rideId: string;
  status: TripStatus;
  riderName?: string;
  pickupText?: string;
  dropoffText?: string;
  nextInstruction?: string;
  trustScore?: number;
  replayVerified?: boolean;
};

export type EarningsSummary = {
  driverId: string;
  periodLabel: string;
  totalText: string;
  rideCount: number;
  source: "core_system";
  verifiedRideCount?: number;
  disputeCount?: number;
  trustScore?: number;
};

export type DriverReplayHistoryItem = {
  rideId: string;
  replayId: string;
  replayVerified: boolean;
  completedAt?: string;
  trustScore?: number;
  timelineEvents?: Array<"REQUESTED" | "ACCEPTED" | "ARRIVED" | "STARTED" | "COMPLETED">;
};
