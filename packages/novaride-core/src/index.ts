export type RideStatus =
  | "requested" | "offered" | "assigned" | "driver_en_route" | "arrived"
  | "rider_verified" | "in_progress" | "completed" | "cancelled" | "disputed";
export type GeoPoint = Readonly<{ latitude: number; longitude: number; recordedAt: string }>;
export type RideRequest = Readonly<{ id: string; riderId: string; pickup: GeoPoint; dropoff: GeoPoint; category: string; requestedAt: string }>;
export type RideOffer = Readonly<{ id: string; requestId: string; driverId: string; expiresAt: string }>;
export type RideAssignment = Readonly<{ id: string; requestId: string; driverId: string; vehicleId: string; decidedAt: string }>;
export type RideLifecycle = Readonly<{ rideId: string; status: RideStatus; timeline: readonly RideStatus[] }>;
export type DriverProfile = Readonly<{ id: string; displayName: string; novaIDVerified: boolean; rating: number; online: boolean }>;
export type RiderProfile = Readonly<{ id: string; displayName: string; novaIDVerified: boolean; rating: number }>;
export type VehicleProfile = Readonly<{ id: string; registration: string; make: string; model: string; compliance: "approved" | "review" | "suspended" }>;
export type FareEstimate = Readonly<{ currency: string; base: number; distance: number; time: number; fees: number; total: number }>;
export type TripLocation = GeoPoint & Readonly<{ rideId: string; sequence: number }>;
export type TripRoute = Readonly<{ rideId: string; points: readonly TripLocation[]; distanceMeters: number; durationSeconds: number }>;
export type SafetyEvent = Readonly<{ id: string; rideId: string; kind: string; severity: "low" | "medium" | "high" | "critical"; occurredAt: string }>;
export type EmergencyEvent = SafetyEvent & Readonly<{ sharedLiveTrip: boolean; operationsNotified: boolean; evidenceFrozen: boolean }>;
export type RideReceipt = Readonly<{ id: string; rideId: string; transactionId: string; proofHash: string; issuedAt: string }>;
export type RideReplay = Readonly<{ rideId: string; eventIds: readonly string[]; replayHash: string; verified: boolean }>;
export type EvidencePackage = Readonly<{ id: string; rideId: string; eventIds: readonly string[]; signature: string; frozenAt: string }>;
export type DriverEarnings = Readonly<{ driverId: string; currency: string; gross: number; fees: number; net: number }>;
export type Payout = Readonly<{ id: string; driverId: string; amount: number; status: "available" | "requested" | "paid" }>;
export type DisputeCase = Readonly<{ id: string; rideId: string; reason: string; status: "open" | "review" | "resolved" }>;
export type SupportTicket = Readonly<{ id: string; rideId?: string; subject: string; status: "open" | "pending" | "closed" }>;
export type DispatchDecision = Readonly<{ rideId: string; driverId: string; zoneId: string; risk: number; score: number; reason: string }>;
export type TrustSignal = Readonly<{ subjectId: string; kind: string; score: number; source: string; observedAt: string }>;
export type CityZone = Readonly<{ id: string; city: string; name: string; riskLevel: "low" | "medium" | "high"; surgeMultiplier: number }>;

export const advanceRide = (lifecycle: RideLifecycle, next: RideStatus): RideLifecycle => ({
  rideId: lifecycle.rideId,
  status: next,
  timeline: [...lifecycle.timeline, next],
});
