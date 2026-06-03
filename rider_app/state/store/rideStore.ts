import type {
  LedgerReceiptSummary,
  PriceExplanation,
  RideReceipt,
  RideReplay,
  RideRequestResult,
  RideStatusSnapshot,
} from "../../core/models/ride";

export type RideEvidenceBundle = {
  receipt: RideReceipt;
  ledgerReceipt: LedgerReceiptSummary;
  replay: RideReplay;
  priceExplanation: PriceExplanation;
};

export type RiderAppState = {
  requestedRide: RideRequestResult | null;
  statusSnapshot: RideStatusSnapshot | null;
  evidence: RideEvidenceBundle | null;
  loading: boolean;
  error: string;
};

export const initialRiderAppState: RiderAppState = {
  requestedRide: null,
  statusSnapshot: null,
  evidence: null,
  loading: false,
  error: "",
};
