import type {
  LedgerReceiptSummary,
  PriceExplanation,
  RequestRidePayload,
  RideReceipt,
  RideReplay,
  RideRequestResult,
  RideStatusSnapshot,
} from "../models/ride";

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
