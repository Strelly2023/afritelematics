import {
  getPriceExplanation,
  getReceipt,
  getLedgerReceipt,
  getReplay,
} from "../api/ride.service";

export async function loadCompletedRideEvidence(rideId: string) {
  const [receipt, replay, ledgerReceipt, priceExplanation] = await Promise.all([
    getReceipt(rideId),
    getReplay(rideId),
    getLedgerReceipt(rideId),
    getPriceExplanation(rideId),
  ]);

  return {
    receipt,
    replay,
    ledgerReceipt,
    priceExplanation,
  };
}
