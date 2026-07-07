import type { EmergencyEvent } from "../../novaride-core/src";
export const createSOSEvent = (rideId: string): EmergencyEvent => ({
  id: `SOS-${Date.now()}`, rideId, kind: "sos", severity: "critical",
  occurredAt: new Date().toISOString(), sharedLiveTrip: true, operationsNotified: true, evidenceFrozen: true,
});
