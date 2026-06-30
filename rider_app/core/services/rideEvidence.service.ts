import {
  getPriceExplanation,
  getReceipt,
  getLedgerReceipt,
  getReplay,
} from "../api/ride.service";
import type {
  LedgerReceiptSummary,
  PriceExplanation,
  RideReceipt,
  RideReplay,
} from "../models/ride";

export async function loadCompletedRideEvidence(rideId: string) {
  const [receipt, replay, ledgerReceipt, priceExplanation] = await Promise.allSettled([
    getReceipt(rideId),
    getReplay(rideId),
    getLedgerReceipt(rideId),
    getPriceExplanation(rideId),
  ]);

  return {
    receipt: valueOrFallback(receipt, fallbackReceipt(rideId)),
    replay: valueOrFallback(replay, fallbackReplay(rideId)),
    ledgerReceipt: valueOrFallback(ledgerReceipt, fallbackLedgerReceipt(rideId)),
    priceExplanation: valueOrFallback(
      priceExplanation,
      fallbackPriceExplanation(rideId),
    ),
  };
}

function valueOrFallback<T>(
  result: PromiseSettledResult<T>,
  fallback: T,
): T {
  return result.status === "fulfilled" ? result.value : fallback;
}

function fallbackReceipt(rideId: string): RideReceipt {
  return {
    rideId,
    receiptId: `receipt-pending-${rideId}`,
    status: "completed",
    totalText: "Syncing",
    trustScore: 72,
    verificationStatus: "REVIEW_REQUIRED",
    replayMatch: false,
    evidenceComplete: false,
  };
}

function fallbackReplay(rideId: string): RideReplay {
  return {
    rideId,
    replayId: `replay-pending-${rideId}`,
    replayVerified: false,
    routeSummary: "Replay evidence is syncing.",
    explanationSteps: ["Completion received. Replay package is still syncing."],
  };
}

function fallbackLedgerReceipt(rideId: string): LedgerReceiptSummary {
  return {
    receiptId: `ledger-pending-${rideId}`,
    verdict: "INVALID",
    receiptHash: "",
    eventCount: 0,
    rootHash: "",
    hashMode: "pending",
    signatureMode: "pending",
    allSignaturesValid: false,
    allIdentitiesVerified: false,
    replayValid: false,
  };
}

function fallbackPriceExplanation(rideId: string): PriceExplanation {
  return {
    rideId,
    priceExplanation: "Price explanation is syncing from the core system.",
    source: "core_system",
    lineItems: [],
  };
}
