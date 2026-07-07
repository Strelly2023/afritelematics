import type { EvidencePackage, RideReplay, RideReceipt } from "../../novaride-core/src";
export const createRideReceipt = (rideId: string, transactionId: string): RideReceipt => ({
  id: `NRR-${rideId}`, rideId, transactionId, proofHash: `sha256:${rideId}:${transactionId}`, issuedAt: new Date().toISOString(),
});
export const createReplay = (rideId: string, eventIds: readonly string[]): RideReplay => ({ rideId, eventIds, replayHash: `replay:${rideId}:${eventIds.length}`, verified: true });
export const freezeEvidence = (rideId: string, eventIds: readonly string[]): EvidencePackage => ({ id: `NRE-${rideId}`, rideId, eventIds, signature: `signed:${rideId}`, frozenAt: new Date().toISOString() });
