import type {
  LedgerReceiptSummary,
  PriceExplanation,
  RideReceipt,
  RideReplay,
} from "./ride";

function fail(message: string): never {
  throw new Error(message);
}

export function assertReceiptEvidence(
  receipt: RideReceipt | null | undefined,
): asserts receipt is RideReceipt {
  if (!receipt?.rideId || !receipt.receiptId || receipt.status !== "completed") {
    fail("Invalid receipt: missing completed ride evidence");
  }
}

export function assertReplayEvidence(
  replay: RideReplay | null | undefined,
): asserts replay is RideReplay {
  if (!replay?.rideId || !replay.replayId || replay.replayVerified !== true) {
    fail("Invalid replay: missing verified ride evidence");
  }
}

export function assertLedgerReceiptEvidence(
  receipt: LedgerReceiptSummary | null | undefined,
): asserts receipt is LedgerReceiptSummary {
  if (
    !receipt?.receiptId ||
    receipt.verdict !== "VALID" ||
    !receipt.receiptHash ||
    !receipt.rootHash ||
    receipt.hashMode !== "sha256_canonical_chain" ||
    receipt.signatureMode !== "rsa_pss_sha256" ||
    receipt.allSignaturesValid !== true ||
    receipt.allIdentitiesVerified !== true ||
    receipt.replayValid !== true
  ) {
    fail("Invalid ledger receipt: missing portable proof evidence");
  }
}

export function assertPriceEvidence(
  explanation: PriceExplanation | null | undefined,
): asserts explanation is PriceExplanation {
  if (
    !explanation?.rideId ||
    !explanation.priceExplanation ||
    explanation.source !== "core_system"
  ) {
    fail("Invalid price explanation: missing core evidence");
  }
}
