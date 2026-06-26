import { createCommandBus, createDefaultCommandHandlers, createCommand } from "./novarideCommands";
import { createPlatformContracts, validateContractCompatibility } from "./novarideContracts";
import { createProjectionEngine, registerDefaultProjections, PROJECTION_NAMES } from "./novarideProjection";
import { createRuntimeScheduler } from "./novarideScheduler";
import { createPluginSdk, normalizePluginManifest } from "./novaridePluginSdk";
import { createRuntimeCertification } from "./novarideCertification";
import { createMemoryEventStoreAdapter, createProjectionStoreAdapter, createStorageAdapters, createSnapshotChecksum, createSnapshotIntegrity } from "./novarideStorage";
import { createPlatformTrustRuntime } from "./novarideTrustRuntime";
import { stableCanonicalize } from "./canonicalize";
import {
  PLATFORM_EVENTS,
  createEventEnvelope,
  createEventStore,
  createPlatformContext,
  createTwinRegistry,
  foldPlatformEvents,
} from "./novarideRuntime";

function uid(prefix = "rt") {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function deepFreeze(value, seen = new WeakSet()) {
  if (!value || typeof value !== "object") {
    return value;
  }

  if (seen.has(value)) {
    return value;
  }
  seen.add(value);

  const keys = [...Object.getOwnPropertyNames(value), ...Object.getOwnPropertySymbols(value)];
  keys.forEach((key) => {
    deepFreeze(value[key], seen);
  });

  Object.freeze(value);
  return value;
}

function compareSequence(left, right) {
  const seqLeft =
    typeof left?.sequence === "number" && Number.isFinite(left.sequence)
      ? left.sequence
      : Number.POSITIVE_INFINITY;
  const seqRight =
    typeof right?.sequence === "number" && Number.isFinite(right.sequence)
      ? right.sequence
      : Number.POSITIVE_INFINITY;
  if (seqLeft !== seqRight) {
    return seqLeft - seqRight;
  }
  const idLeft = String(left?.id || "");
  const idRight = String(right?.id || "");
  if (idLeft < idRight) return -1;
  if (idLeft > idRight) return 1;
  return 0;
}

function normalizePlugin(plugin = {}) {
  const manifest = normalizePluginManifest({
    id: plugin.id || plugin.name || uid("plugin"),
    name: plugin.name || plugin.id || "Runtime Plugin",
    version: plugin.version || "1.0.0",
    capabilities: Array.isArray(plugin.capabilities) ? plugin.capabilities : [],
    commands: Array.isArray(plugin.commands) ? plugin.commands : [],
    events: Array.isArray(plugin.events) ? plugin.events : [],
    policies: Array.isArray(plugin.policies) ? plugin.policies : [],
    permissions: Array.isArray(plugin.permissions) ? plugin.permissions : [],
    configuration: plugin.configuration || {},
    dependencies: Array.isArray(plugin.dependencies) ? plugin.dependencies : [],
    migration: typeof plugin.migration === "function" ? plugin.migration : null,
  });

  return {
    ...manifest,
    screens: Array.isArray(plugin.screens) ? plugin.screens : [],
    project: typeof plugin.project === "function" ? plugin.project : null,
    onEvent: typeof plugin.onEvent === "function" ? plugin.onEvent : null,
    onDecision: typeof plugin.onDecision === "function" ? plugin.onDecision : null,
  };
}

export function createRuntimePlugin(plugin = {}) {
  return normalizePlugin(plugin);
}

export function createDefaultRuntimePlugins() {
  return [
    createRuntimePlugin({
      id: "core-context",
      name: "Context Engine",
      capabilities: ["context", "mission"],
      project: ({ context, projections, runtime }) => ({
        contextSummary: {
          actor: context.actor,
          online: Boolean(context.mission?.online),
          phase: context.mission?.phase,
          rideStatus: context.mission?.rideStatus,
        },
        missionSignal: projections.passenger?.nextAction || projections.driver?.nextAction || "Refresh Context",
        runtimeVersion: runtime.version,
      }),
    }),
    createRuntimePlugin({
      id: "core-trust",
      name: "Trust Engine",
      capabilities: ["trust", "replay", "evidence"],
      project: ({ context, trustSnapshot }) => ({
        trustSummary: {
          score: context.trust?.score || 0,
          evidence: Boolean(context.trust?.evidence),
          replay: Boolean(context.trust?.replay),
          receipt: Boolean(context.trust?.receipt),
          graphHealth: trustSnapshot.graphHealth || "unknown",
        },
      }),
    }),
    createRuntimePlugin({
      id: "core-spatial",
      name: "Spatial Engine",
      capabilities: ["spatial", "routing"],
      project: ({ context }) => ({
        spatialSummary: {
          location: context.location || null,
          pickup: context.mission?.pickup || null,
          destination: context.mission?.destination || null,
        },
      }),
    }),
  ];
}

function projectionKeyForContext(context) {
  const actor = String(context.actor || "").toLowerCase();
  if (actor.includes("operator")) return PROJECTION_NAMES.OPERATOR;
  if (actor.includes("driver")) return PROJECTION_NAMES.DRIVER;
  if (actor.includes("merchant")) return PROJECTION_NAMES.FLEET;
  if (actor.includes("audit")) return PROJECTION_NAMES.AUDIT;
  return PROJECTION_NAMES.PASSENGER;
}

export function createPlatformRuntime({
  runtimeName = "NovaRuntime",
  runtimeVersion = "1.0.0",
  initialContext = {},
  initialState = {},
  seedEvents = [],
  seedTwins = [],
  seedTrust = {},
  seedSnapshot = null,
  eventStoreAdapter = null,
  projectionStoreAdapter = null,
  scheduler = null,
  pluginSdk = null,
  allowedPluginPermissions = [],
  runtimeIdentity = {},
  plugins = createDefaultRuntimePlugins(),
} = {}) {
  const runtimeId = uid("runtime");
  const runtimeMeta = Object.freeze({
    id: runtimeId,
    name: runtimeName,
    version: runtimeVersion,
    organization: runtimeIdentity.organization || "NovaTech",
    region: runtimeIdentity.region || "global",
    publicKey: runtimeIdentity.publicKey || `pk-${runtimeId}`,
    capabilities: runtimeIdentity.capabilities || ["events", "projection", "trust", "scheduler", "plugins"],
  });

  const storageAdapters = createStorageAdapters({ events: seedEvents });
  const eventStore = createEventStore(seedEvents, eventStoreAdapter || storageAdapters.eventStore || createMemoryEventStoreAdapter(seedEvents));
  const projectionStore = projectionStoreAdapter || createProjectionStoreAdapter();
  const twinRegistry = createTwinRegistry(seedTwins);
  const trustRuntime = createPlatformTrustRuntime(seedTrust);
  const projectionEngine = createProjectionEngine();
  registerDefaultProjections(projectionEngine);
  const runtimeScheduler = scheduler || createRuntimeScheduler();
  const pluginSdkRuntime = pluginSdk || createPluginSdk({ allowedPermissions: allowedPluginPermissions });
  const integrity = createSnapshotIntegrity({ signer: runtimeIdentity.signer || runtimeIdentity.keyProvider || null });
  const pluginRegistry = new Map();
  const listeners = new Set();
  const executionHistory = [];
  const contracts = createPlatformContracts();
  const certification = createRuntimeCertification({
    runtime: runtimeMeta,
    contracts,
    health: () => health(),
    metrics: () => metrics(),
  });

  const normalizedInitialState = {
    ...initialState,
    runtime: runtimeMeta,
  };

  const notify = (snapshot) => {
    listeners.forEach((listener) => {
      try {
        listener(snapshot);
      } catch {
        // ignore listener failures
      }
    });
  };

  const pluginCan = (plugin = {}, permission = "") => {
    const permissions = Array.isArray(plugin.permissions) ? plugin.permissions : [];
    return permissions.includes(permission) || permissions.includes("*");
  };

  const createPluginSandbox = (plugin, pluginContext) => {
    const sandbox = {
      context: pluginContext.context,
      projections: pluginContext.projections,
      runtime: {
        id: runtimeMeta.id,
        name: runtimeMeta.name,
        version: runtimeMeta.version,
        organization: runtimeMeta.organization,
        region: runtimeMeta.region,
        capabilities: runtimeMeta.capabilities,
        trustScore: runtimeTrustScore(),
      },
      state: pluginContext.state,
      trustSnapshot: pluginContext.trustSnapshot,
      event: pluginContext.event,
      contracts: pluginContext.contracts,
    };

    if (pluginCan(plugin, "events:read") || pluginCan(plugin, "events")) {
      sandbox.events = {
        read: () => eventStore.read(),
        tail: (limit = 25) => eventStore.tail(limit),
        size: eventStore.size,
      };
    }

    if (pluginCan(plugin, "scheduler")) {
      sandbox.scheduler = {
        snapshot: () => runtimeScheduler.snapshot(),
        queues: runtimeScheduler.snapshot().queues,
      };
    }

    if (pluginCan(plugin, "trust")) {
      sandbox.trust = {
        snapshot: () => trustRuntime.trust.snapshot(),
      };
    }

    if (pluginCan(plugin, "twins")) {
      sandbox.twins = {
        all: () => twinRegistry.all(),
        get: (id) => twinRegistry.get(id),
      };
    }

    return Object.freeze(sandbox);
  };

  const runtimeTrustScore = () => {
    const queueSnapshot = runtimeScheduler.snapshot();
    const trustSnapshot = trustRuntime.trust.snapshot();
    const eventCount = eventStore.size;
    const pluginCount = pluginRegistry.size;
    let score = 100;

    if (trustSnapshot.graphHealth === "critical") {
      score -= 40;
    } else if (trustSnapshot.graphHealth === "warning") {
      score -= 15;
    } else if (!trustSnapshot.graphHealth || trustSnapshot.graphHealth === "unknown") {
      score -= 20;
    }

    if (queueSnapshot.depth > 50) {
      score -= 20;
    } else if (queueSnapshot.depth > 20) {
      score -= 8;
    }

    if (eventCount > 0) {
      score += 5;
    }

    if (pluginCount > 0) {
      score += 5;
    }

    if (runtimeMeta.publicKey) {
      score += 5;
    }

    return Math.max(0, Math.min(100, score));
  };

  const currentState = () =>
    foldPlatformEvents(eventStore.read(), {
      ...normalizedInitialState,
      runtime: runtimeMeta,
    });

  const captureSnapshot = () => ({
    eventLog: eventStore.read(),
    projectionStore: projectionStore.snapshot ? projectionStore.snapshot() : projectionStore.read(),
    scheduler: runtimeScheduler.snapshot(),
    twins: twinRegistry.snapshot ? twinRegistry.snapshot() : twinRegistry.all(),
    trust: trustRuntime.trust.snapshot(),
  });

  const restoreSnapshot = (snapshot = {}) => {
    if (snapshot?.eventLog) {
      eventStore.load(snapshot.eventLog);
    }
    if (snapshot?.projectionStore) {
      projectionStore.load?.(snapshot.projectionStore);
    }
    if (snapshot?.scheduler) {
      runtimeScheduler.restore(snapshot.scheduler);
    }
    if (snapshot?.twins) {
      twinRegistry.restore?.(Array.isArray(snapshot.twins) ? snapshot.twins : snapshot.twins.all || []);
    }
    if (snapshot?.trust) {
      trustRuntime.trust.restore?.(snapshot.trust);
    }
    return snapshot;
  };

  const hydrate = (snapshot = null) => {
    if (!snapshot) {
      return null;
    }
    if (snapshot.eventStore?.checksum && Array.isArray(snapshot.eventStore?.tail)) {
      const expected = createSnapshotChecksum(snapshot.eventStore.tail);
      if (expected !== snapshot.eventStore.checksum) {
        throw new Error("Snapshot checksum mismatch.");
      }
    }
    if (snapshot.integrity?.fingerprint) {
      const expectedFingerprint = integrity.fingerprint({
        eventLog: snapshot.eventLog || [],
        projectionStore: snapshot.projectionStore || {},
        scheduler: snapshot.scheduler || {},
        twins: snapshot.twins || {},
        trust: snapshot.trust || {},
      });
      if (expectedFingerprint !== snapshot.integrity.fingerprint) {
        throw new Error("Snapshot fingerprint mismatch.");
      }
    }
    if (snapshot.eventLog) {
      eventStore.load(snapshot.eventLog);
    }
    if (snapshot.projectionStore) {
      projectionStore.load?.(snapshot.projectionStore);
    }
    if (snapshot.scheduler) {
      runtimeScheduler.restore(snapshot.scheduler);
    }
    if (snapshot.twins) {
      twinRegistry.restore?.(Array.isArray(snapshot.twins) ? snapshot.twins : snapshot.twins.all || []);
    }
    if (snapshot.trust) {
      trustRuntime.trust.restore?.(snapshot.trust);
    }
    return snapshot;
  };

  hydrate(seedSnapshot);

  const transaction = (work) => {
    const before = captureSnapshot();
    const startedAt = Date.now();
    try {
      const result = typeof work === "function" ? work() : work;
      executionHistory.push({
        type: "transaction",
        status: "committed",
        durationMs: Date.now() - startedAt,
        eventCount: eventStore.size,
        queueDepth: runtimeScheduler.snapshot().depth,
      });
      return result;
    } catch (error) {
      restoreSnapshot(before);
      executionHistory.push({
        type: "transaction",
        status: "rolled_back",
        durationMs: Date.now() - startedAt,
        error: error?.message || String(error),
      });
      throw error;
    }
  };

  const registerPlugin = (plugin) => {
    const normalized = normalizePlugin(plugin);
    const validation = pluginSdkRuntime.validate(normalized);
    if (!validation.valid) {
      throw new Error(`Invalid plugin manifest: ${validation.issues.join("; ")}`);
    }
    const registration = pluginSdkRuntime.register(normalized);
    if (!registration.valid) {
      throw new Error(`Plugin registration rejected: ${registration.issues.join("; ")}`);
    }
    pluginRegistry.set(normalized.id, {
      ...normalized,
      lifecycle: "installed",
      installedAt: new Date().toISOString(),
      activatedAt: null,
      deprecatedAt: null,
    });
    notify({
      type: "plugin.registered",
      plugin: pluginRegistry.get(normalized.id),
      runtime: runtimeMeta,
      pluginCount: pluginRegistry.size,
    });
    return pluginRegistry.get(normalized.id);
  };

  const registerPlugins = (list = []) => list.map(registerPlugin);

  const updatePluginLifecycle = (pluginId, lifecycle) => {
    const plugin = pluginRegistry.get(pluginId);
    if (!plugin) {
      return null;
    }
    const next = {
      ...plugin,
      lifecycle,
      activatedAt: lifecycle === "active" ? new Date().toISOString() : plugin.activatedAt,
      deprecatedAt: lifecycle === "deprecated" ? new Date().toISOString() : plugin.deprecatedAt,
    };
    pluginRegistry.set(pluginId, next);
    notify({
      type: "plugin.lifecycle",
      plugin: next,
      runtime: runtimeMeta,
      lifecycle,
    });
    return next;
  };

  const activatePlugin = (pluginId) => updatePluginLifecycle(pluginId, "active");
  const suspendPlugin = (pluginId) => updatePluginLifecycle(pluginId, "suspended");
  const deprecatePlugin = (pluginId) => updatePluginLifecycle(pluginId, "deprecated");
  const removePlugin = (pluginId) => {
    const plugin = pluginRegistry.get(pluginId);
    if (!plugin) {
      return null;
    }
    pluginRegistry.delete(pluginId);
    notify({
      type: "plugin.removed",
      plugin,
      runtime: runtimeMeta,
      pluginCount: pluginRegistry.size,
    });
    return plugin;
  };

  const schedule = (queueName, task = {}) => {
    const entry = runtimeScheduler.enqueue(queueName, task);
    eventStore.append(
      createEventEnvelope(PLATFORM_EVENTS.TASK_SCHEDULED, { task: entry }, { source: runtimeName, confidence: 1 }),
    );
    return entry;
  };
  const drain = (queueName = "projection", limit = 1) => {
    const tasks = runtimeScheduler.drain(queueName, limit);
    tasks.forEach((task) => {
      eventStore.append(
        createEventEnvelope(PLATFORM_EVENTS.TASK_STARTED, { task }, { source: runtimeName, confidence: 1 }),
      );
      eventStore.append(
        createEventEnvelope(PLATFORM_EVENTS.TASK_COMPLETED, { task }, { source: runtimeName, confidence: 1 }),
      );
    });
    return tasks;
  };

  const emit = (type, payload = {}, meta = {}) => {
    const event = createEventEnvelope(type, payload, {
      ...meta,
      source: meta.source || runtimeName,
    });
    eventStore.append(event);

    const state = currentState();
    const payloadContext = payload?.context || payload?.runtimeContext || payload || {};
    trustRuntime.ingestContext(payloadContext, {
      confidence: meta.confidence || 0,
      offlineReady: !payloadContext?.mission?.online,
    });

    twinRegistry.upsert("platform", "platform", {
      liveState: {
        latestEvent: event,
        state,
      },
      telemetry: {
        eventCount: eventStore.size,
        queueDepth: runtimeScheduler.snapshot().depth,
      },
      replay: eventStore.tail(12),
      confidence: meta.confidence || 0,
      health: "active",
    });

    notify({
      type: "event.dispatched",
      event,
      state,
      runtime: runtimeMeta,
      eventCount: eventStore.size,
    });

    return event;
  };

  const commandBus = createCommandBus({
    policies: [
      (command) =>
        command?.type
          ? { allowed: true }
          : { allowed: false, reason: "Command type is required." },
    ],
    handlers: createDefaultCommandHandlers(),
    eventStore,
    emit,
    validate(command) {
      return command?.type ? { valid: true } : { valid: false, reason: "Command type is required." };
    },
  });

  const project = (context, eventLog = eventStore.read()) => {
    const projections = projectionEngine.projectAll(context, eventLog, runtimeMeta);
    const primaryProjection = projections[projectionKeyForContext(context)] || projections[PROJECTION_NAMES.PASSENGER];
    const trustSnapshot = trustRuntime.ingestContext(context, {
      confidence: primaryProjection?.confidence || 0,
      offlineReady: !context.mission?.online,
    }).snapshot;
    const state = foldPlatformEvents(eventLog, normalizedInitialState);

    return {
      context,
      projections,
      primaryProjection,
      trustSnapshot,
      state,
      runtime: runtimeMeta,
      contracts,
    };
  };

  const executeInternal = (input = {}) => {
    const startedAt = Date.now();
    const context = createPlatformContext({
      ...initialContext,
      ...input,
    });

    const preEvents = eventStore.read();
    const preProjection = project(context, preEvents);
    const decision = {
      label: preProjection.primaryProjection?.nextAction || "Refresh Context",
      reason: context.mission?.online
        ? "Runtime projections are synchronized and ready for execution."
        : "Runtime is offline and requires activation before dispatch.",
      confidence: Number.isFinite(Number(preProjection.primaryProjection?.confidence))
        ? Number(preProjection.primaryProjection?.confidence)
        : context.environment?.confidence || 0,
    };

    const runtimeEvent = emit(
      context.mission?.online ? PLATFORM_EVENTS.OPERATOR_REFRESHED : PLATFORM_EVENTS.DRIVER_STATUS_CHANGED,
      {
        context,
        decision,
        projections: preProjection.projections,
        trustSnapshot: preProjection.trustSnapshot,
      },
      {
        confidence: decision.confidence || 1,
      },
    );

    const allEvents = eventStore.read();
    const updatedProjection = project(context, allEvents);
    const updatedState = foldPlatformEvents(allEvents, normalizedInitialState);

    projectionStore.write("passenger", updatedProjection.projections.passenger || null);
    projectionStore.write("driver", updatedProjection.projections.driver || null);
    projectionStore.write("operator", updatedProjection.projections.operator || null);
    projectionStore.write("fleet", updatedProjection.projections.fleet || null);
    projectionStore.write("analytics", updatedProjection.projections.analytics || null);
    projectionStore.write("audit", updatedProjection.projections.audit || null);

    schedule("projection", {
      type: "runtime.projection",
      priority: updatedProjection.primaryProjection?.surface === "operator" ? 1 : 0,
      payload: updatedProjection.projections,
      retries: 0,
    });
    schedule("decision", {
      type: "runtime.decision",
      priority: decision.confidence || 0,
      payload: decision,
      retries: 0,
    });
    schedule("audit", {
      type: "runtime.audit",
      priority: 0,
      payload: { eventId: runtimeEvent.id },
      retries: 0,
    });

    const pluginOutputs = [];
    const pluginContext = {
      context,
      projections: updatedProjection.projections,
      runtime: runtimeMeta,
      state: updatedState,
      trustSnapshot: updatedProjection.trustSnapshot,
      event: runtimeEvent,
      eventStore,
      twins: twinRegistry,
      contracts,
    };

    for (const plugin of pluginRegistry.values()) {
      if (plugin.project) {
        const sandbox = createPluginSandbox(plugin, pluginContext);
        const output = plugin.project(sandbox);
        if (output !== undefined) {
          pluginOutputs.push({
            pluginId: plugin.id,
            name: plugin.name,
            output,
          });
        }
      }
    }

    const queueSnapshot = runtimeScheduler.snapshot();
    const twinSnapshot = {
      all: twinRegistry.all(),
      platform: twinRegistry.get("platform"),
    };
    const durationMs = Date.now() - startedAt;
    executionHistory.push({
      type: "execute",
      durationMs,
      eventCount: allEvents.length,
      queueDepth: queueSnapshot.depth,
      projectionKey: projectionKeyForContext(context),
    });

    return {
      runtime: runtimeMeta,
      context,
      decision,
      projections: updatedProjection.projections,
      primaryProjection: updatedProjection.primaryProjection,
      trustSnapshot: updatedProjection.trustSnapshot,
      state: updatedState,
      event: runtimeEvent,
      eventLog: allEvents,
      eventStore: eventStore.snapshot(25),
      projectionStore: projectionStore.snapshot ? projectionStore.snapshot() : projectionStore.read(),
      scheduleQueue: queueSnapshot.queues,
      scheduler: queueSnapshot,
      scheduled: {
        decision: queueSnapshot.queues.decision[0] || null,
        projection: queueSnapshot.queues.projection[0] || null,
        audit: queueSnapshot.queues.audit[0] || null,
      },
      pluginOutputs,
      plugins: [...pluginRegistry.values()],
      twins: twinSnapshot,
      timeline: allEvents.map((event, index) => ({
        index,
        id: event.id,
        type: event.type,
        source: event.source,
        timestamp: event.timestamp,
        confidence: event.confidence,
      })),
      signals: {
        eventCount: allEvents.length,
        pluginCount: pluginRegistry.size,
        queueDepth: queueSnapshot.depth,
        offlineReady: !context.mission?.online,
        learningSignal: {
          eventCount: allEvents.length,
          activeRides: context.telemetry?.activeRides || 0,
        },
      },
      contracts,
    };
  };

  const execute = (input = {}) => transaction(() => executeInternal(input));

  const replay = ({ from = 0, to = null } = {}) => {
    const events = eventStore
      .read()
      .slice(Math.max(0, from), to === null ? undefined : to)
      .sort(compareSequence);
    const canonicalEvents = [...events].sort(compareSequence).map((event) => deepFreeze(stableCanonicalize(event)));
    const canonicalEventPayloads = canonicalEvents;
    const state = foldPlatformEvents(canonicalEvents, normalizedInitialState);
    const context = createPlatformContext(initialContext);
    const projections = projectionEngine.projectAll(context, canonicalEvents, runtimeMeta);
    const normalizedProjections = projections ? stableCanonicalize(JSON.parse(JSON.stringify(projections))) : {};
    const checksums = {
      eventLog: createSnapshotChecksum(canonicalEventPayloads),
      state: createSnapshotChecksum(stableCanonicalize(state)),
      projections: createSnapshotChecksum(normalizedProjections),
      runtime: createSnapshotChecksum(
        stableCanonicalize({
          id: runtimeMeta.id,
          version: runtimeMeta.version,
        }),
      ),
    };
    return {
      events,
      state,
      projections: normalizedProjections,
      runtime: runtimeMeta,
      checksums,
      replayHash: createSnapshotChecksum(
        stableCanonicalize({
          version: "replay-v1",
          events: checksums.eventLog,
          state: checksums.state,
          projections: checksums.projections,
          runtime: checksums.runtime,
        }),
      ),
      metadata: {
        eventCount: canonicalEvents.length,
      },
    };
  };

  const recover = (snapshotData = null) => {
    if (!snapshotData) {
      return snapshot();
    }
    if (Array.isArray(snapshotData.eventLog)) {
      eventStore.load(snapshotData.eventLog);
    } else {
      restoreSnapshot(snapshotData);
    }
    if (snapshotData.scheduler) {
      runtimeScheduler.restore(snapshotData.scheduler);
    }
    if (snapshotData.twins) {
      twinRegistry.restore?.(Array.isArray(snapshotData.twins) ? snapshotData.twins : snapshotData.twins.all || []);
    }
    if (snapshotData.trust) {
      trustRuntime.trust.restore?.(snapshotData.trust);
    }
    const replayed = replay({ from: 0 });
    if (snapshotData.projectionStore) {
      projectionStore.load?.(snapshotData.projectionStore);
    } else {
      projectionStore.load?.(replayed.projections || {});
    }
    const restored = restoreSnapshot({
      ...snapshotData,
      eventLog: eventStore.read(),
      projectionStore: projectionStore.snapshot ? projectionStore.snapshot() : projectionStore.read(),
      scheduler: runtimeScheduler.snapshot(),
      twins: twinRegistry.snapshot ? twinRegistry.snapshot() : twinRegistry.all(),
      trust: trustRuntime.trust.snapshot(),
    });
    return {
      ...restored,
      replayed,
      snapshot: snapshot(),
    };
  };

  const health = () => {
    const queueSnapshot = runtimeScheduler.snapshot();
    const trustSnapshot = trustRuntime.trust.snapshot();
    const projectionSnapshot = projectionStore.snapshot ? projectionStore.snapshot() : projectionStore.read();
    const projections = projectionSnapshot?.projections || projectionSnapshot || {};
    const trustScore = runtimeTrustScore();
    return {
      runtime: runtimeMeta,
      status:
        trustSnapshot.graphHealth === "critical"
          ? "degraded"
          : queueSnapshot.depth > 50
            ? "busy"
            : "healthy",
      eventCount: eventStore.size,
      queueDepth: queueSnapshot.depth,
      pluginCount: pluginRegistry.size,
      projectionCount: Object.keys(projections || {}).length,
      trust: {
        ...trustSnapshot,
        score: trustScore,
        level: trustScore >= 80 ? "high" : trustScore >= 55 ? "medium" : "low",
      },
      contracts,
      subsystems: {
        eventStore: typeof eventStore.read === "function" ? "healthy" : "critical",
        projectionStore: typeof projectionStore.read === "function" ? "healthy" : "critical",
        scheduler: typeof runtimeScheduler.snapshot === "function" ? "healthy" : "critical",
        trust: trustSnapshot.graphHealth || "unknown",
        plugins: pluginRegistry.size >= 0 ? "healthy" : "critical",
      },
    };
  };

  const status = () => {
    const currentHealth = health();
    return {
      runtime: runtimeMeta,
      status: currentHealth.status,
      certified: certification.report().certified,
      pluginCount: pluginRegistry.size,
      eventCount: eventStore.size,
      queueDepth: runtimeScheduler.snapshot().depth,
      trustScore: currentHealth.trust.score,
      trust: currentHealth.trust,
    };
  };

  const diagnostics = () => ({
    runtime: runtimeMeta,
    health: health(),
    metrics: metrics(),
    snapshot: snapshot(),
    capabilities: runtimeCapabilities(),
    dependencies: dependencies(),
  });

  const dependencies = () => ({
    eventStore: {
      kind: eventStore.kind || "memory",
      supported: Boolean(eventStore.read && eventStore.append),
    },
    projectionStore: {
      kind: projectionStore.kind || "memory",
      supported: Boolean(projectionStore.read && projectionStore.write),
    },
    scheduler: {
      supported: Boolean(runtimeScheduler.enqueue && runtimeScheduler.drain),
      queues: Object.keys(runtimeScheduler.snapshot().queues || {}),
    },
    trust: {
      supported: Boolean(trustRuntime.trust.snapshot),
    },
    plugins: {
      supported: Boolean(pluginSdkRuntime.validate),
      count: pluginRegistry.size,
    },
  });

  const storage = () => ({
    eventStore: {
      size: eventStore.size,
      nextSequence: eventStore.nextSequence,
      snapshot: eventStore.snapshot(25),
    },
    projectionStore: {
      snapshot: projectionStore.snapshot ? projectionStore.snapshot() : projectionStore.read(),
    },
    scheduler: runtimeScheduler.snapshot(),
  });

  const federation = (peer = {}) => {
    const handshakeReport = handshake(peer);
    return {
      ...handshakeReport,
      runtime: runtimeMeta,
      protocol: handshakeReport.protocol,
      trustPolicy: handshakeReport.trustPolicy,
      trust: {
        score: handshakeReport.trustPolicy?.local?.score ?? runtimeTrustScore(),
        level: health().trust.level,
      },
      synchronizationReady: handshakeReport.accepted,
    };
  };

  const upgrade = (peer = {}) => {
    const certificationReport = certification.compare(peer);
    const compatibility = validateContracts(peer.contracts || peer);
    const runtimeFingerprint = integrity.fingerprint({
      runtime: runtimeMeta,
      contracts,
      capabilities: runtimeCapabilities(),
    });
    const approved = Object.values(certificationReport).every(Boolean) && Object.values(compatibility).every(Boolean);
    return {
      approved,
      certification: certificationReport,
      compatibility,
      runtime: runtimeMeta,
      plan: {
        migrationRequirements: approved ? [] : Object.entries(compatibility).filter(([, ok]) => !ok).map(([name]) => `${name}-contract-alignment`),
        breakingChanges: Object.entries(compatibility).filter(([, ok]) => !ok).map(([name]) => name),
        rollbackStrategy: approved ? "none" : "retain-current-runtime",
        fingerprint: runtimeFingerprint,
      },
    };
  };

  const handshake = (peer = {}) => {
    const peerRuntime = peer.runtime || peer.identity || null;
    const peerContracts = peer.contracts || peer;
    const compatibility = validateContracts(peerContracts || {});
    const peerTrustVersion = peer.trustVersion || peer.trust?.version || null;
    const peerTrustScore = Number.isFinite(Number(peer.trustScore)) ? Number(peer.trustScore) : null;
    const peerPolicyVersion = peer.policyVersion || peer.trustPolicyVersion || null;
    const localTrustScore = runtimeTrustScore();
    const negotiatedFeatures = Object.entries(compatibility)
      .filter(([, ok]) => ok)
      .map(([name]) => name);
    const protocol = {
      stage: "hello",
      steps: [
        { stage: "hello", accepted: true },
        {
          stage: "identity",
          local: runtimeMeta.id,
          peer: peerRuntime?.id || null,
          accepted: Boolean(peerRuntime?.id),
        },
        {
          stage: "version",
          local: runtimeMeta.version,
          peer: peer.version || peer.runtimeVersion || null,
          accepted: Boolean(peer.version || peer.runtimeVersion),
        },
        {
          stage: "contracts",
          local: contracts,
          peer: peerContracts || null,
          accepted: Object.values(compatibility).every(Boolean),
        },
        {
          stage: "trust",
          local: {
            health: trustRuntime.trust.snapshot().graphHealth || "unknown",
            score: localTrustScore,
          },
          peer: peerTrustVersion,
          accepted: Boolean(peerTrustVersion) || localTrustScore >= 60,
        },
        {
          stage: "policy",
          local: {
            version: "1",
            trustScore: localTrustScore,
          },
          peer: {
            version: peerPolicyVersion,
            trustScore: peerTrustScore,
          },
          accepted: peerTrustScore !== null && peerTrustScore >= 60 && Boolean(peerPolicyVersion),
        },
        {
          stage: "capabilities",
          local: runtimeCapabilities(),
          peer: peer.capabilities || null,
          accepted: true,
        },
      ],
    };
    return {
      hello: {
        runtime: runtimeMeta,
        contracts,
        capabilities: runtimeCapabilities(),
        trustVersion: trustRuntime.trust.snapshot().graphHealth || "unknown",
        trustScore: localTrustScore,
      },
      peer: {
        runtime: peerRuntime,
        version: peer.version || peer.runtimeVersion || null,
      },
      compatibility,
      negotiatedFeatures,
      accepted: protocol.steps.every((step) => step.accepted !== false),
      protocol,
      trustPolicy: {
        local: {
          version: "1",
          score: localTrustScore,
        },
        peer: {
          version: peerPolicyVersion,
          score: peerTrustScore,
        },
        accepted: peerTrustScore !== null && peerTrustScore >= 60 && Boolean(peerPolicyVersion),
      },
    };
  };

  const snapshotArtifact = async () => {
    const artifact = snapshot();
    const signature = await integrity.sign(artifact, { runtimeId: runtimeMeta.id });
    return {
      artifact,
      signature,
    };
  };

  const verifySnapshotArtifact = async (artifact, signature) => {
    return integrity.verify(artifact, signature, { runtimeId: runtimeMeta.id });
  };

  const certificationArtifact = async (peer = contracts) => {
    const replayResult = replay({ from: 0 });
    const deployment = {
      kind: "deployment-certificate",
      runtime: runtimeMeta,
      trust: {
        score: runtimeTrustScore(),
        level: health().trust.level,
      },
      validation: certification.deployment(peer),
      replay: replayResult.replayHash,
      checksums: replayResult.checksums,
      contracts,
      issuedAt: new Date().toISOString(),
    };
    const signature = await integrity.sign(deployment, {
      runtimeId: runtimeMeta.id,
      kind: "deployment-certification",
      contractVersion: contracts.runtime?.version || null,
    });
    return {
      certificate: deployment,
      signature,
    };
  };

  const verifyCertificationArtifact = async (artifact, signature) => {
    return integrity.verify(artifact, signature, { runtimeId: runtimeMeta.id, kind: "deployment-certification" });
  };

  const deploymentCertificate = async (peer = contracts) => certificationArtifact(peer);

  const verifyDeploymentCertificate = async (artifact, signature) =>
    integrity.verify(artifact, signature, { runtimeId: runtimeMeta.id, kind: "deployment-certification" });

  const metrics = () => {
    const queueSnapshot = runtimeScheduler.snapshot();
    const trustSnapshot = trustRuntime.trust.snapshot();
    return {
      runtime: runtimeMeta,
      categories: {
        runtime: {
          commandLatencyMs: executionHistory.length
            ? Math.round(executionHistory.reduce((sum, item) => sum + (item.durationMs || 0), 0) / executionHistory.length)
            : 0,
          projectionLatencyMs: 0,
          queueDepth: queueSnapshot.depth,
        },
        platform: {
          replayDurationMs: eventStore.size,
          trustVerificationLatencyMs: 0,
        },
        business: {
          rides: currentState().telemetry?.activeRides || 0,
          payments: currentState().telemetry?.paymentDelay || 0,
          settlements: currentState().mission?.phase === "SETTLED" ? 1 : 0,
        },
      },
      executionHistory: [...executionHistory],
      eventCount: eventStore.size,
      queueDepth: queueSnapshot.depth,
      queueMetrics: queueSnapshot.metrics,
      pluginCount: pluginRegistry.size,
      trust: trustSnapshot,
      averageExecutionMs: executionHistory.length
        ? Math.round(executionHistory.reduce((sum, item) => sum + (item.durationMs || 0), 0) / executionHistory.length)
        : 0,
      lastExecution: executionHistory[executionHistory.length - 1] || null,
    };
  };

  const runtimeCapabilities = () => ({
    runtime: runtimeMeta,
    contracts,
    identity: runtimeMeta,
    eventStore: {
      supported: Boolean(eventStore.read && eventStore.append),
      kind: eventStore.kind || "memory",
      sequenceAware: true,
    },
    projectionStore: {
      supported: Boolean(projectionStore.read && projectionStore.write),
      kind: projectionStore.kind || "memory",
    },
    scheduler: {
      supported: Boolean(runtimeScheduler.enqueue && runtimeScheduler.drain),
      queues: Object.keys(runtimeScheduler.snapshot().queues || {}),
      eventSourced: true,
    },
      trust: {
        supported: Boolean(trustRuntime.trust.snapshot),
        graphAware: true,
        score: runtimeTrustScore(),
      },
    plugins: {
      supported: Boolean(pluginSdkRuntime.validate),
      lifecycleAware: true,
      count: pluginRegistry.size,
      permissions: pluginSdkRuntime.allowedPermissions,
    },
  });

  const snapshot = () => {
    const state = currentState();
    const events = eventStore.read();
    const queueSnapshot = runtimeScheduler.snapshot();
    return {
      runtime: runtimeMeta,
      state,
      eventLog: events,
      eventStore: eventStore.snapshot(25),
      projectionStore: projectionStore.snapshot ? projectionStore.snapshot() : projectionStore.read(),
      scheduleQueue: queueSnapshot.queues,
      scheduler: queueSnapshot,
      plugins: [...pluginRegistry.values()],
      twins: {
        all: twinRegistry.all(),
        platform: twinRegistry.get("platform"),
      },
      trust: trustRuntime.trust.snapshot(),
      trustScore: runtimeTrustScore(),
      contracts,
      integrity: {
        fingerprint: integrity.fingerprint({
          runtime: runtimeMeta,
          state,
          eventLog: events,
          projectionStore: projectionStore.snapshot ? projectionStore.snapshot() : projectionStore.read(),
          scheduler: queueSnapshot,
          twins: twinRegistry.all(),
          trust: trustRuntime.trust.snapshot(),
        }),
      },
    };
  };

  registerPlugins(plugins);

  return {
    runtime: runtimeMeta,
    contracts,
    commandBus,
    execute,
    replay,
    recover,
    health,
    status,
    metrics,
    diagnostics,
    dependencies,
    storage,
    federation,
    handshake,
    upgrade,
    runtimeCapabilities,
    snapshotArtifact,
    verifySnapshotArtifact,
    certificationArtifact,
    verifyCertificationArtifact,
    deploymentCertificate,
    verifyDeploymentCertificate,
    restore: recover,
    certify() {
      return certification.report();
    },
    certification,
    transaction,
    project,
    emit,
    dispatch: emit,
    schedule,
    drain,
    snapshot,
    registerPlugin,
    registerPlugins,
    activatePlugin,
    suspendPlugin,
    deprecatePlugin,
    removePlugin,
    createCommand,
    createEventEnvelope,
    subscribe(listener) {
      if (typeof listener !== "function") {
        return () => {};
      }
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    get plugins() {
      return [...pluginRegistry.values()];
    },
    get eventLog() {
      return eventStore.read();
    },
    get eventStore() {
      return eventStore;
    },
    get projections() {
      return projectionStore.snapshot ? projectionStore.snapshot() : projectionStore.read();
    },
    get projectionStore() {
      return projectionStore;
    },
    get twins() {
      return twinRegistry;
    },
    get trust() {
      return trustRuntime.trust;
    },
    get queue() {
      return runtimeScheduler.snapshot().queues;
    },
    get state() {
      return currentState();
    },
    get initialPluginCount() {
      return pluginRegistry.size;
    },
    validateContracts(otherContracts) {
      return {
        runtime: validateContractCompatibility(contracts.runtime, otherContracts?.runtime),
        event: validateContractCompatibility(contracts.event, otherContracts?.event),
        projection: validateContractCompatibility(contracts.projection, otherContracts?.projection),
        plugin: validateContractCompatibility(contracts.plugin, otherContracts?.plugin),
        twin: validateContractCompatibility(contracts.twin, otherContracts?.twin),
        command: validateContractCompatibility(contracts.command, otherContracts?.command),
      };
    },
    certify(peer = contracts) {
      return {
        report: certification.report(),
        compatibility: this.validateContracts(peer?.contracts || peer),
        comparison: certification.compare(peer),
        approved:
          Object.values(this.validateContracts(peer?.contracts || peer)).every(Boolean) &&
          Object.values(certification.compare(peer)).every(Boolean),
      };
    },
    identity() {
      return { ...runtimeMeta };
    },
  };
}
