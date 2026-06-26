import { deriveDecision, deriveTrustGraph } from "./novarideRuntime";

export const PROJECTION_NAMES = {
  PASSENGER: "passenger",
  DRIVER: "driver",
  OPERATOR: "operator",
  FLEET: "fleet",
  ANALYTICS: "analytics",
  AUDIT: "audit",
};

function baseProjection(context, events = []) {
  const trustGraph = deriveTrustGraph(context);
  const decision = deriveDecision(context);
  return {
    context,
    events,
    decision,
    trustGraph,
    timestamp: new Date().toISOString(),
    confidence: decision.confidence || context.environment?.confidence || 0,
  };
}

export function createProjectionEngine() {
  const registry = new Map();

  const register = (name, projector) => {
    if (typeof projector === "function") {
      registry.set(name, projector);
    }
    return projector;
  };

  const project = (name, context, events = [], runtime = {}) => {
    const projector = registry.get(name);
    const projection = baseProjection(context, events);
    return typeof projector === "function"
      ? projector({ ...projection, runtime })
      : projection;
  };

  const projectAll = (context, events = [], runtime = {}) => {
    const projections = {};
    registry.forEach((projector, name) => {
      projections[name] = projector({ ...baseProjection(context, events), runtime });
    });
    return projections;
  };

  return {
    register,
    project,
    projectAll,
    has(name) {
      return registry.has(name);
    },
    list() {
      return [...registry.keys()];
    },
  };
}

export function registerDefaultProjections(engine) {
  engine.register(PROJECTION_NAMES.PASSENGER, ({ context, decision, trustGraph, events }) => ({
    surface: "passenger",
    mission: context.mission?.rideStatus || "BOOKING",
    nextAction: decision.label,
    trustGraph,
    eventCount: events.length,
  }));

  engine.register(PROJECTION_NAMES.DRIVER, ({ context, decision, trustGraph, events }) => ({
    surface: "driver",
    mission: context.mission?.online ? "READY" : "OFFLINE",
    nextAction: decision.label,
    trustGraph,
    eventCount: events.length,
  }));

  engine.register(PROJECTION_NAMES.OPERATOR, ({ context, decision, trustGraph, events }) => ({
    surface: "operator",
    mission: "CONTROL",
    nextAction: decision.label,
    trustGraph,
    eventCount: events.length,
  }));

  engine.register(PROJECTION_NAMES.FLEET, ({ context, trustGraph, events }) => ({
    surface: "fleet",
    driversOnline: context.telemetry?.driversOnline || 0,
    activeRides: context.telemetry?.activeRides || 0,
    graphHealth: trustGraph.platform?.graphHealth || "unknown",
    eventCount: events.length,
  }));

  engine.register(PROJECTION_NAMES.ANALYTICS, ({ context, trustGraph, events }) => ({
    surface: "analytics",
    demand: context.environment?.demand || "unknown",
    confidence: context.environment?.confidence || 0,
    replayScore: trustGraph.platform?.replayScore || 0,
    eventCount: events.length,
  }));

  engine.register(PROJECTION_NAMES.AUDIT, ({ context, events }) => ({
    surface: "audit",
    actor: context.actor,
    history: events.slice(-20),
    eventCount: events.length,
  }));
}
