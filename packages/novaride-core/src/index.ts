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
export type MobilityResourceKind =
  | "person" | "rider" | "human_driver" | "courier"
  | "vehicle" | "autonomous_vehicle" | "fleet_vehicle" | "transit_vehicle"
  | "delivery_robot" | "drone" | "merchant" | "charging_station"
  | "parking_space" | "road_segment" | "energy_asset" | "infrastructure";
export type MobilityResource = Readonly<{
  id: string;
  kind: MobilityResourceKind;
  tenantId: string;
  zoneId: string;
  capacity: number;
  availableAt: string;
  batteryPercent?: number;
  accessibilityReady: boolean;
  autonomousReady: boolean;
}>;
export type MOSCapability =
  | "mobility" | "logistics" | "commerce" | "finance" | "fleet" | "energy"
  | "ai" | "identity" | "communications" | "iot" | "smart_city" | "developer";
export type EventEnvelope<TPayload = unknown> = Readonly<{
  id: string;
  type: string;
  tenantId: string;
  region: string;
  occurredAt: string;
  actorId?: string;
  correlationId: string;
  payload: TPayload;
}>;
export type AIDecisionStage =
  | "identity" | "context" | "demand_prediction" | "supply_prediction" | "pricing"
  | "matching" | "risk_analysis" | "route_optimization" | "dispatch" | "learning";
export type AIDecisionTrace = Readonly<{
  requestId: string;
  stages: readonly AIDecisionStage[];
  selectedResourceId?: string;
  confidence: number;
  explanation: string;
  modelVersion: string;
}>;
export type DigitalTwinAsset = Readonly<{
  id: string;
  kind: "city" | "road_network" | "vehicle" | "driver" | "package" | "charger" | "weather" | "traffic" | "transit";
  syncStatus: "live" | "delayed" | "degraded";
  lastSyncedAt: string;
  riskScore: number;
}>;
export type EnergyPlan = Readonly<{
  vehicleId: string;
  chargerId: string;
  startAt: string;
  targetBatteryPercent: number;
  renewablePercent: number;
  estimatedCost: number;
  gridLoad: "low" | "medium" | "high";
}>;
export type SustainabilityScore = Readonly<{
  gramsCo2eSaved: number;
  carbonAwareRoute: boolean;
  idleMinutesReduced: number;
  renewableEnergyPercent: number;
}>;
export type ReliabilityObjective = Readonly<{
  availabilityTarget: "99.9999%";
  dispatchLatencyMs: number;
  liveTrackingUpdateMs: number;
  activeActiveRegions: readonly string[];
}>;
export type MOSReadinessSnapshot = Readonly<{
  platformName: "NovaRide X";
  capabilities: readonly MOSCapability[];
  reliability: ReliabilityObjective;
  eventNative: boolean;
  zeroTrust: boolean;
  aiNative: boolean;
  autonomousReady: boolean;
  sustainabilityAware: boolean;
}>;
export type MobilityCloudLayer =
  | "applications" | "experience_cloud" | "mobility_cloud_services"
  | "intelligence_cloud" | "data_cloud" | "infrastructure_cloud";
export type MobilityCloudService =
  | "ride_dispatch" | "delivery" | "fleet" | "commerce" | "payments" | "insurance"
  | "energy" | "charging" | "public_transit" | "autonomous_vehicles"
  | "robotics" | "drone_operations" | "safety" | "compliance" | "urban_analytics";
export type MobilityGraphRelation =
  | "owns" | "connected_to" | "operates_in" | "uses" | "services"
  | "linked_to" | "depends_on" | "governed_by";
export type MobilityGraphEdge = Readonly<{
  fromResourceId: string;
  relation: MobilityGraphRelation;
  toResourceId: string;
  confidence: number;
  observedAt: string;
}>;
export type AIAgentKind =
  | "planner" | "reasoning_engine" | "dispatch_agent" | "pricing_agent"
  | "safety_agent" | "fraud_agent" | "fleet_agent" | "energy_agent"
  | "commerce_agent" | "city_agent" | "customer_support_agent" | "maintenance_agent";
export type AIGovernanceDecision = Readonly<{
  decisionId: string;
  agentKind: AIAgentKind;
  modelVersion: string;
  promptVersion?: string;
  humanReviewRequired: boolean;
  auditEventId: string;
  policyIds: readonly string[];
}>;
export type CityOperatingInsight = Readonly<{
  cityId: string;
  category: "mobility" | "infrastructure" | "environment" | "emergency_operations";
  aggregateOnly: boolean;
  metric: string;
  value: number | string;
  generatedAt: string;
}>;
export type FederationNode = Readonly<{
  id: string;
  level: "country" | "region" | "city" | "fleet" | "transit" | "energy" | "commerce" | "public_safety";
  parentId?: string;
  jurisdiction: string;
  apiVersion: string;
  operationalAutonomy: boolean;
}>;
export type EventTaxonomyPrefix =
  | "identity" | "trip" | "driver" | "vehicle" | "fleet" | "energy" | "charging"
  | "payment" | "wallet" | "merchant" | "delivery" | "transit" | "robot"
  | "drone" | "iot" | "safety" | "fraud" | "city" | "weather" | "traffic"
  | "simulation" | "ai" | "audit";
export type MobilityCloudReadiness = MOSReadinessSnapshot & Readonly<{
  layers: readonly MobilityCloudLayer[];
  services: readonly MobilityCloudService[];
  eventTaxonomy: readonly EventTaxonomyPrefix[];
  federationReady: boolean;
  governanceRequired: readonly string[];
}>;

export const advanceRide = (lifecycle: RideLifecycle, next: RideStatus): RideLifecycle => ({
  rideId: lifecycle.rideId,
  status: next,
  timeline: [...lifecycle.timeline, next],
});

export const NOVARIDE_X_CAPABILITIES: readonly MOSCapability[] = [
  "mobility", "logistics", "commerce", "finance", "fleet", "energy",
  "ai", "identity", "communications", "iot", "smart_city", "developer",
];
export const NOVARIDE_X_CLOUD_LAYERS: readonly MobilityCloudLayer[] = [
  "applications", "experience_cloud", "mobility_cloud_services",
  "intelligence_cloud", "data_cloud", "infrastructure_cloud",
];
export const NOVARIDE_X_CLOUD_SERVICES: readonly MobilityCloudService[] = [
  "ride_dispatch", "delivery", "fleet", "commerce", "payments", "insurance",
  "energy", "charging", "public_transit", "autonomous_vehicles", "robotics",
  "drone_operations", "safety", "compliance", "urban_analytics",
];
export const NOVARIDE_X_EVENT_TAXONOMY: readonly EventTaxonomyPrefix[] = [
  "identity", "trip", "driver", "vehicle", "fleet", "energy", "charging",
  "payment", "wallet", "merchant", "delivery", "transit", "robot", "drone",
  "iot", "safety", "fraud", "city", "weather", "traffic", "simulation", "ai", "audit",
];

export const NOVARIDE_X_DECISION_PIPELINE: readonly AIDecisionStage[] = [
  "identity", "context", "demand_prediction", "supply_prediction", "pricing",
  "matching", "risk_analysis", "route_optimization", "dispatch", "learning",
];

export const NOVARIDE_X_READINESS: MOSReadinessSnapshot = {
  platformName: "NovaRide X",
  capabilities: NOVARIDE_X_CAPABILITIES,
  reliability: {
    availabilityTarget: "99.9999%",
    dispatchLatencyMs: 100,
    liveTrackingUpdateMs: 1000,
    activeActiveRegions: ["Australia", "Africa", "Europe", "Asia", "North America", "Middle East"],
  },
  eventNative: true,
  zeroTrust: true,
  aiNative: true,
  autonomousReady: true,
  sustainabilityAware: true,
};
export const NOVARIDE_X_MOBILITY_CLOUD_READINESS: MobilityCloudReadiness = {
  ...NOVARIDE_X_READINESS,
  layers: NOVARIDE_X_CLOUD_LAYERS,
  services: NOVARIDE_X_CLOUD_SERVICES,
  eventTaxonomy: NOVARIDE_X_EVENT_TAXONOMY,
  federationReady: true,
  governanceRequired: [
    "model_governance",
    "api_governance",
    "schema_governance",
    "data_lineage",
    "audit_logging",
    "privacy_management",
    "consent_management",
    "regulatory_compliance",
    "policy_enforcement",
    "lifecycle_management",
  ],
};

export function createDecisionTrace(
  requestId: string,
  selectedResourceId: string,
  confidence: number,
): AIDecisionTrace {
  return {
    requestId,
    stages: NOVARIDE_X_DECISION_PIPELINE,
    selectedResourceId,
    confidence,
    explanation: "AI-native marketplace decision optimized across ETA, risk, price, energy, accessibility, and sustainability.",
    modelVersion: "novaride-x-2035",
  };
}
