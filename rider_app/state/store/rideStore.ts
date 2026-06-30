import type {
  LedgerReceiptSummary,
  PriceExplanation,
  RideReceipt,
  RideReplay,
  RideRequestResult,
  RideStatusSnapshot,
} from "../../core/models/ride";

export type RideEvidenceBundle = {
  receipt?: RideReceipt | null;
  ledgerReceipt?: LedgerReceiptSummary | null;
  replay?: RideReplay | null;
  priceExplanation?: PriceExplanation | null;
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
