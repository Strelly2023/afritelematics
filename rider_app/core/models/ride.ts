export type RideStatus =
  | "requested"
  | "confirmed"
  | "waiting_for_driver"
  | "driver_assigned"
  | "arriving"
  | "in_progress"
  | "completed"
  | "cancelled";

export type RequestRidePayload = {
  riderId: string;
  pickup: string;
  dropoff: string;
};

export type RideRequestResult = {
  rideId: string;
  status: RideStatus;
  quotedTotal?: string;
  currency?: string;
  confirmationToken?: string;
};

export type RideStatusSnapshot = {
  rideId: string;
  status: RideStatus;
  driverName?: string;
  vehicleLabel?: string;
  etaText?: string;
  locationText?: string;
};

export type RideReceipt = {
  rideId: string;
  receiptId: string;
  status: "completed";
  distanceText?: string;
  totalText?: string;
  startedAt?: string;
  completedAt?: string;
};

export type LedgerReceiptSummary = {
  receiptId: string;
  verdict: "VALID" | "INVALID";
  receiptHash: string;
  eventCount: number;
  rootHash: string;
  hashMode: string;
  signatureMode: string;
  allSignaturesValid: boolean;
  allIdentitiesVerified: boolean;
  replayValid: boolean;
};

export type RideReplay = {
  rideId: string;
  replayId: string;
  replayVerified: boolean;
  routeSummary?: string;
  explanationSteps: string[];
};

export type PriceExplanation = {
  rideId: string;
  priceExplanation: string;
  source: "core_system";
  lineItems?: Array<{
    label: string;
    amountText: string;
  }>;
};
