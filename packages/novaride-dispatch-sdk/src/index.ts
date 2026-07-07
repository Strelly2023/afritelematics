import type { DispatchDecision, RideRequest } from "../../novaride-core/src";
export type DriverCandidate = Readonly<{ driverId: string; available: boolean; distanceMeters: number; trustScore: number; riskScore: number }>;
export const selectDriver = (request: RideRequest, zoneId: string, candidates: readonly DriverCandidate[]): DispatchDecision | null => {
  const eligible = candidates.filter((candidate) => candidate.available && candidate.trustScore >= 0.7 && candidate.riskScore < 0.8);
  const selected = eligible.sort((a, b) => (b.trustScore - b.riskScore) - (a.trustScore - a.riskScore))[0];
  return selected ? { rideId: request.id, driverId: selected.driverId, zoneId, risk: selected.riskScore, score: selected.trustScore, reason: "eligible_nearest_trusted" } : null;
};
