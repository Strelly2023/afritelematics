const upper = (value) => String(value || "").toUpperCase();
const eventId = () => `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`;

export const PLATFORM_EVENTS = {
  RIDER_REQUESTED: "RIDER_REQUESTED",
  DRIVER_ACCEPTED: "DRIVER_ACCEPTED",
  DRIVER_ARRIVED: "DRIVER_ARRIVED",
  TRIP_STARTED: "TRIP_STARTED",
  TRIP_COMPLETED: "TRIP_COMPLETED",
  PAYMENT_SETTLED: "PAYMENT_SETTLED",
  RECEIPT_UPDATED: "RECEIPT_UPDATED",
  EVIDENCE_UPDATED: "EVIDENCE_UPDATED",
  TRUST_UPDATED: "TRUST_UPDATED",
  REPLAY_UPDATED: "REPLAY_UPDATED",
  DRIVER_STATUS_CHANGED: "DRIVER_STATUS_CHANGED",
  OPERATOR_REFRESHED: "OPERATOR_REFRESHED",
  TASK_SCHEDULED: "TASK_SCHEDULED",
  TASK_STARTED: "TASK_STARTED",
  TASK_RETRIED: "TASK_RETRIED",
  TASK_COMPLETED: "TASK_COMPLETED",
  TASK_CANCELLED: "TASK_CANCELLED",
};

export function createPlatformContext(input = {}) {
  const now = input.timestamp || new Date().toISOString();
  const rideStatus = upper(input.rideStatus || input.tripStatus || input.status);
  const online = Boolean(input.online);
  return {
    timestamp: now,
    actor: input.actor || "platform",
    user: input.user || null,
    location: input.location || null,
    timeOfDay: input.timeOfDay || new Date(now).getHours(),
    vehicle: input.vehicle || null,
    trust: {
      score: Number.isFinite(Number(input.trustScore)) ? Number(input.trustScore) : 0,
      evidence: Boolean(input.evidence),
      replay: Boolean(input.replay),
      receipt: Boolean(input.receipt),
      graphHealth: input.graphHealth || "unknown",
    },
    environment: {
      weather: input.weather || "unknown",
      traffic: input.traffic || "unknown",
      demand: input.demand || "unknown",
      confidence: Number.isFinite(Number(input.confidence)) ? Number(input.confidence) : 0,
    },
    mission: {
      phase: input.phase || "UNKNOWN",
      rideStatus,
      activeRideId: input.activeRideId || null,
      pickup: input.pickup || null,
      destination: input.destination || null,
      online,
    },
    telemetry: {
      activeRides: Number.isFinite(Number(input.activeRides)) ? Number(input.activeRides) : 0,
      driversOnline: Number.isFinite(Number(input.driversOnline)) ? Number(input.driversOnline) : 0,
      guards: Number.isFinite(Number(input.guards)) ? Number(input.guards) : 0,
      replayScore: Number.isFinite(Number(input.replayScore)) ? Number(input.replayScore) : 100,
      paymentDelay: Number.isFinite(Number(input.paymentDelay)) ? Number(input.paymentDelay) : 0,
      fatigue: Number.isFinite(Number(input.fatigue)) ? Number(input.fatigue) : 0,
    },
    history: Array.isArray(input.history) ? input.history : [],
  };
}

export function deriveDecision(context) {
  const demand = upper(context.environment?.demand);
  const traffic = upper(context.environment?.traffic);
  const confidence = Number(context.environment?.confidence || 0);
  const online = Boolean(context.mission?.online);
  const rideStatus = upper(context.mission?.rideStatus);

  if (!online) {
    return {
      label: "Go Online",
      reason: "Driver is offline and cannot receive demand.",
      confidence: Math.max(75, confidence),
    };
  }

  if (demand === "HIGH" || demand === "RISING") {
    return {
      label: "Position Nearby",
      reason: `Demand is ${demand.toLowerCase()} and closer positioning may improve trip throughput.`,
      confidence: Math.max(82, confidence),
    };
  }

  if (traffic === "HEAVY" && rideStatus === "STARTED") {
    return {
      label: "Route Around Traffic",
      reason: "Traffic is heavy and the trip is active.",
      confidence: Math.max(88, confidence),
    };
  }

  return {
    label: "Refresh Context",
    reason: "No stronger decision signal is currently available.",
    confidence: Math.max(60, confidence),
  };
}

export function deriveTrustGraph(context) {
  return {
    driver: {
      trust: context.trust?.score || 0,
      evidence: Boolean(context.trust?.evidence),
    },
    ride: {
      confidence: context.environment?.confidence || 0,
      replay: Boolean(context.trust?.replay),
    },
    payment: {
      receipt: Boolean(context.trust?.receipt),
      delay: context.telemetry?.paymentDelay || 0,
    },
    platform: {
      graphHealth: context.trust?.graphHealth || "unknown",
      replayScore: context.telemetry?.replayScore || 0,
    },
  };
}

export function reducePlatformState(previousState, event) {
  const state = previousState || {};
  switch (event?.type) {
    case PLATFORM_EVENTS.RIDER_REQUESTED:
      return {
        ...state,
        lastEvent: event,
        mission: { ...(state.mission || {}), phase: "BOOKING" },
      };
    case PLATFORM_EVENTS.DRIVER_ACCEPTED:
      return {
        ...state,
        lastEvent: event,
        mission: { ...(state.mission || {}), phase: "WAITING" },
      };
    case PLATFORM_EVENTS.TRIP_STARTED:
      return {
        ...state,
        lastEvent: event,
        mission: { ...(state.mission || {}), phase: "ACTIVE" },
      };
    case PLATFORM_EVENTS.TRIP_COMPLETED:
      return {
        ...state,
        lastEvent: event,
        mission: { ...(state.mission || {}), phase: "SETTLED" },
      };
    case PLATFORM_EVENTS.DRIVER_STATUS_CHANGED:
      return {
        ...state,
        lastEvent: event,
        mission: { ...(state.mission || {}), online: Boolean(event.payload?.online) },
      };
    default:
      return {
        ...state,
        lastEvent: event || state.lastEvent || null,
      };
  }
}

export function foldPlatformEvents(events = [], initialState = {}) {
  return events.reduce((state, event) => reducePlatformState(state, event), initialState);
}

export function createEventStore(seedEvents = [], adapter = null) {
  const memoryEvents = Array.isArray(seedEvents) ? [...seedEvents] : [];
  const backend = adapter && typeof adapter.append === "function" ? adapter : null;
  let nextSequence = 1;

  const normalizeEvent = (event = {}, sequence = null) => {
    const hasSequence = Number.isFinite(Number(event.sequence));
    return {
      ...event,
      id: event.id || event.eventId || eventId(),
      sequence: Number.isFinite(Number(sequence))
        ? Number(sequence)
        : hasSequence
          ? Number(event.sequence)
          : null,
      streamPosition: Number.isFinite(Number(sequence))
        ? Number(sequence)
        : Number.isFinite(Number(event.streamPosition))
          ? Number(event.streamPosition)
          : hasSequence
            ? Number(event.sequence)
            : null,
    };
  };

  const readEvents = () => {
    if (backend && typeof backend.load === "function") {
      return backend.load() || [];
    }
    return [...memoryEvents];
  };

  const refreshSequence = (events = []) => {
    const maxSequence = events.reduce((max, event) => {
      const candidate = Number(event?.sequence || event?.streamPosition || 0);
      return Number.isFinite(candidate) ? Math.max(max, candidate) : max;
    }, 0);
    nextSequence = Math.max(nextSequence, maxSequence + 1);
    return nextSequence;
  };

  const initialEvents = readEvents();
  refreshSequence(initialEvents.length ? initialEvents : memoryEvents);

  return {
    kind: backend?.kind || "memory",
    append(event) {
      const normalized = normalizeEvent(event, nextSequence);
      if (Number.isFinite(Number(normalized.sequence))) {
        nextSequence = Number(normalized.sequence) + 1;
      }
      if (backend) {
        backend.append(normalized);
      } else {
        memoryEvents.push(normalized);
      }
      return normalized;
    },
    load(stream = []) {
      const incoming = Array.isArray(stream) ? stream : [];
      nextSequence = 1;
      const normalized = [];
      let localSequence = 1;
      incoming.forEach((event, index) => {
        const sequence = Number.isFinite(Number(event?.sequence)) ? Number(event.sequence) : localSequence;
        const item = normalizeEvent(event, sequence);
        normalized.push(item);
        localSequence = Number(item.sequence) + 1;
      });
      if (backend && typeof backend.clear === "function") {
        backend.clear();
        normalized.forEach((event) => backend.append(event));
      } else {
        memoryEvents.length = 0;
        memoryEvents.push(...normalized);
      }
      refreshSequence(normalized);
      return this.read();
    },
    read() {
      return readEvents();
    },
    replay(reducer, initialState = {}) {
      if (typeof reducer !== "function") {
        return initialState;
      }
      const events = readEvents();
      return events.reduce((state, event) => reducer(state, event), initialState);
    },
    tail(limit = this.size) {
      const events = readEvents();
      return events.slice(Math.max(0, events.length - Math.max(0, limit)));
    },
    snapshot(limit = this.size) {
      return {
        size: this.size,
        tail: this.tail(limit),
      };
    },
    compact(keepLast = 50) {
      if (!Number.isFinite(Number(keepLast)) || keepLast < 0) {
        return this.read();
      }
      const events = readEvents();
      if (events.length <= keepLast) {
        return this.read();
      }
      const next = events.slice(events.length - keepLast);
      return this.load(next);
    },
    byType(type) {
      return readEvents().filter((event) => event.type === type);
    },
    clear() {
      if (backend && typeof backend.clear === "function") {
        backend.clear();
      } else {
        memoryEvents.length = 0;
      }
    },
    get size() {
      return readEvents().length;
    },
    get nextSequence() {
      return nextSequence;
    },
  };
}

export function createDigitalTwin(id, type, initialState = {}) {
  return {
    id,
    type,
    version: 1,
    identity: {
      id,
      type,
    },
    capabilities: [],
    liveState: { ...initialState },
    historicalState: [],
    desiredState: {},
    predictedState: {},
    health: "unknown",
    confidence: 0,
    relationships: [],
    telemetry: {},
    replay: [],
    policyStatus: "unknown",
    updatedAt: new Date().toISOString(),
  };
}

export function createTwinRegistry(seedTwins = []) {
  const twins = new Map();

  const register = (twin) => {
    if (!twin || !twin.id) {
      return null;
    }
    twins.set(twin.id, {
      ...createDigitalTwin(twin.id, twin.type || "entity", twin.liveState || twin.state || {}),
      ...twin,
      identity: twin.identity || {
        id: twin.id,
        type: twin.type || "entity",
      },
    });
    return twins.get(twin.id);
  };

  seedTwins.forEach(register);

  return {
    register,
    upsert(id, type, patch = {}) {
      const current = twins.get(id) || createDigitalTwin(id, type, {});
      const next = {
        ...current,
        id,
        type: type || current.type,
        version: (current.version || 0) + 1,
        updatedAt: new Date().toISOString(),
        liveState: {
          ...(current.liveState || {}),
          ...(patch.liveState || patch.state || patch),
        },
        historicalState: Array.isArray(current.historicalState) ? [...current.historicalState, current.liveState || {}] : [],
        desiredState: {
          ...(current.desiredState || {}),
          ...(patch.desiredState || {}),
        },
        predictedState: {
          ...(current.predictedState || {}),
          ...(patch.predictedState || {}),
        },
        health: patch.health || current.health,
        confidence: Number.isFinite(Number(patch.confidence)) ? Number(patch.confidence) : current.confidence || 0,
        relationships: Array.isArray(patch.relationships) ? patch.relationships : current.relationships || [],
        telemetry: {
          ...(current.telemetry || {}),
          ...(patch.telemetry || {}),
        },
        replay: Array.isArray(patch.replay) ? patch.replay : current.replay || [],
        policyStatus: patch.policyStatus || current.policyStatus || "unknown",
        capabilities: Array.isArray(patch.capabilities) ? patch.capabilities : current.capabilities || [],
      };
      twins.set(id, next);
      return next;
    },
    get(id) {
      return twins.get(id) || null;
    },
    all() {
      return [...twins.values()];
    },
    snapshot() {
      return this.all();
    },
    restore(snapshot = []) {
      twins.clear();
      (Array.isArray(snapshot) ? snapshot : []).forEach((twin) => register(twin));
      return this.all();
    },
    clear() {
      twins.clear();
    },
    queryByType(type) {
      return [...twins.values()].filter((twin) => twin.type === type);
    },
    relate(sourceId, targetId, relation = {}) {
      const source = twins.get(sourceId);
      const target = twins.get(targetId);
      if (!source || !target) {
        return null;
      }
      source.relationships = [
        ...(Array.isArray(source.relationships) ? source.relationships : []),
        { targetId, ...relation },
      ];
      source.updatedAt = new Date().toISOString();
      twins.set(sourceId, source);
      return source;
    },
  };
}

export function createTrustRuntime(seedGraph = {}) {
  const nodes = new Map();
  const edges = [];

  const upsertNode = (id, patch = {}) => {
    const current = nodes.get(id) || {
      id,
      trust: 0,
      risk: 0,
      confidence: 0,
      evidence: [],
      history: [],
      status: "unknown",
    };
    const next = {
      ...current,
      ...patch,
      id,
      trust: Number.isFinite(Number(patch.trust)) ? Number(patch.trust) : current.trust,
      risk: Number.isFinite(Number(patch.risk)) ? Number(patch.risk) : current.risk,
      confidence: Number.isFinite(Number(patch.confidence)) ? Number(patch.confidence) : current.confidence,
      evidence: Array.isArray(patch.evidence) ? patch.evidence : current.evidence,
      history: Array.isArray(patch.history) ? patch.history : [...(current.history || []), patch],
      updatedAt: new Date().toISOString(),
    };
    nodes.set(id, next);
    return next;
  };

  const relate = (sourceId, targetId, patch = {}) => {
    const edge = {
      id: patch.id || `${sourceId}:${targetId}:${Date.now()}`,
      sourceId,
      targetId,
      trust: Number.isFinite(Number(patch.trust)) ? Number(patch.trust) : 0,
      risk: Number.isFinite(Number(patch.risk)) ? Number(patch.risk) : 0,
      confidence: Number.isFinite(Number(patch.confidence)) ? Number(patch.confidence) : 0,
      evidence: Array.isArray(patch.evidence) ? patch.evidence : [],
      history: Array.isArray(patch.history) ? patch.history : [],
      status: patch.status || "active",
      updatedAt: new Date().toISOString(),
    };
    edges.push(edge);
    return edge;
  };

  const score = () => {
    const nodeValues = [...nodes.values()];
    const trustTotal = nodeValues.reduce((sum, node) => sum + (Number(node.trust) || 0), 0);
    const riskTotal = nodeValues.reduce((sum, node) => sum + (Number(node.risk) || 0), 0);
    const edgeValues = edges.reduce((sum, edge) => sum + (Number(edge.trust) || 0), 0);
    const health = trustTotal - riskTotal + edgeValues;
    return {
      trustTotal,
      riskTotal,
      edgeTrust: edgeValues,
      graphHealth: health >= 60 ? "healthy" : health >= 30 ? "degraded" : "critical",
    };
  };

  Object.entries(seedGraph || {}).forEach(([id, node]) => upsertNode(id, node));

  return {
    upsertNode,
    relate,
    getNode(id) {
      return nodes.get(id) || null;
    },
    allNodes() {
      return [...nodes.values()];
    },
    allEdges() {
      return [...edges];
    },
    restore(snapshot = {}) {
      nodes.clear();
      edges.length = 0;
      const entries = Array.isArray(snapshot?.nodes)
        ? snapshot.nodes
        : Object.entries(snapshot || {}).map(([id, node]) => ({ id, ...node }));
      entries.forEach((node) => upsertNode(node.id, node));
      (Array.isArray(snapshot?.edges) ? snapshot.edges : []).forEach((edge) => relate(edge.sourceId, edge.targetId, edge));
      return this.snapshot();
    },
    clear() {
      nodes.clear();
      edges.length = 0;
    },
    snapshot() {
      return {
        nodes: [...nodes.values()],
        edges: [...edges],
        ...score(),
      };
    },
    score,
  };
}

export function createEventEnvelope(type, payload = {}, meta = {}) {
  const timestamp = meta.timestamp || new Date().toISOString();
  return {
    id: meta.id || `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    type,
    payload,
    timestamp,
    source: meta.source || "platform-runtime",
    confidence: Number.isFinite(Number(meta.confidence)) ? Number(meta.confidence) : 1,
  };
}

export function buildRuntimeProjection(context) {
  return {
    context,
    decision: deriveDecision(context),
    trustGraph: deriveTrustGraph(context),
    offlineReady: !context.mission?.online,
    learningSignal: {
      eventCount: Array.isArray(context.history) ? context.history.length : 0,
      activeRides: context.telemetry?.activeRides || 0,
    },
  };
}
