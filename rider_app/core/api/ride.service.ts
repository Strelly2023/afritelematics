import { apiRequest } from "./client";
import { USE_MOCK_API } from "../config/environment";
import {
  mockGetPriceExplanation,
  mockGetReceipt,
  mockGetLedgerReceipt,
  mockGetReplay,
  mockGetRideStatus,
  mockRequestRide,
} from "./mockRide.service";
import type {
  PriceExplanation,
  LedgerReceiptSummary,
  RequestRidePayload,
  RideReceipt,
  RideReplay,
  RideRequestResult,
  RideStatusSnapshot,
} from "../models/ride";

type RideRequestResponse = {
  ride_id: string;
  status: RideRequestResult["status"];
  quoted_total?: string;
  currency?: string;
  confirmation_token?: string;
};

type RideStatusResponse = {
  ride_id: string;
  status: RideStatusSnapshot["status"];
  driver_name?: string;
  vehicle_label?: string;
  eta_text?: string;
  location_text?: string;
};

type ReceiptResponse = {
  ride_id: string;
  receipt_id: string;
  status: "completed";
  distance_text?: string;
  total_text?: string;
  started_at?: string;
  completed_at?: string;
};

type ReplayResponse = {
  ride_id: string;
  replay_id: string;
  replay_verified: boolean;
  route_summary?: string;
  explanation_steps?: string[];
};

type LedgerReceiptResponse = {
  receipt_id: string;
  verdict: LedgerReceiptSummary["verdict"];
  receipt_hash: string;
  ledger_proof: {
    event_count: number;
    root_hash: string;
    hash_mode: string;
  };
  signature_validation: {
    signature_mode: string;
    all_signatures_valid: boolean;
  };
  identity_validation: {
    all_verified: boolean;
  };
  replay_proof: {
    replay_valid: boolean;
  };
};

type PriceExplanationResponse = {
  ride_id: string;
  price_explanation: string;
  source: "core_system";
  line_items?: Array<{
    label: string;
    amount_text: string;
  }>;
};

export async function requestRide(
  payload: RequestRidePayload,
): Promise<RideRequestResult> {
  if (USE_MOCK_API) {
    return mockRequestRide(payload);
  }

  const result = await apiRequest<RideRequestResponse>("/ride/request", {
    method: "POST",
    body: {
      rider_id: payload.riderId,
      pickup: payload.pickup,
      dropoff: payload.dropoff,
    },
  });

  return {
    rideId: result.ride_id,
    status: result.status,
    quotedTotal: result.quoted_total,
    currency: result.currency,
    confirmationToken: result.confirmation_token,
  };
}

export async function getRideStatus(rideId: string): Promise<RideStatusSnapshot> {
  if (USE_MOCK_API) {
    return mockGetRideStatus(rideId);
  }

  const result = await apiRequest<RideStatusResponse>(`/ride/${rideId}/status`);

  return {
    rideId: result.ride_id,
    status: result.status,
    driverName: result.driver_name,
    vehicleLabel: result.vehicle_label,
    etaText: result.eta_text,
    locationText: result.location_text,
  };
}

export async function getReceipt(rideId: string): Promise<RideReceipt> {
  if (USE_MOCK_API) {
    return mockGetReceipt(rideId);
  }

  const result = await apiRequest<ReceiptResponse>(`/ride/${rideId}/receipt`);

  return {
    rideId: result.ride_id,
    receiptId: result.receipt_id,
    status: result.status,
    distanceText: result.distance_text,
    totalText: result.total_text,
    startedAt: result.started_at,
    completedAt: result.completed_at,
  };
}

export async function getReplay(rideId: string): Promise<RideReplay> {
  if (USE_MOCK_API) {
    return mockGetReplay(rideId);
  }

  const result = await apiRequest<ReplayResponse>(`/ride/${rideId}/replay`);

  return {
    rideId: result.ride_id,
    replayId: result.replay_id,
    replayVerified: result.replay_verified,
    routeSummary: result.route_summary,
    explanationSteps: result.explanation_steps || [],
  };
}

export async function getLedgerReceipt(
  rideId: string,
): Promise<LedgerReceiptSummary> {
  if (USE_MOCK_API) {
    return mockGetLedgerReceipt(rideId);
  }

  const result = await apiRequest<LedgerReceiptResponse>(
    `/ride/${rideId}/ledger-receipt`,
  );

  return {
    receiptId: result.receipt_id,
    verdict: result.verdict,
    receiptHash: result.receipt_hash,
    eventCount: result.ledger_proof.event_count,
    rootHash: result.ledger_proof.root_hash,
    hashMode: result.ledger_proof.hash_mode,
    signatureMode: result.signature_validation.signature_mode,
    allSignaturesValid: result.signature_validation.all_signatures_valid,
    allIdentitiesVerified: result.identity_validation.all_verified,
    replayValid: result.replay_proof.replay_valid,
  };
}

export async function getPriceExplanation(
  rideId: string,
): Promise<PriceExplanation> {
  if (USE_MOCK_API) {
    return mockGetPriceExplanation(rideId);
  }

  const result = await apiRequest<PriceExplanationResponse>(
    `/ride/${rideId}/price-explanation`,
  );

  return {
    rideId: result.ride_id,
    priceExplanation: result.price_explanation,
    source: result.source,
    lineItems: result.line_items?.map((item) => ({
      label: item.label,
      amountText: item.amount_text,
    })),
  };
}
