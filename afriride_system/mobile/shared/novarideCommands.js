import { PLATFORM_EVENTS, createEventEnvelope } from "./novarideRuntime";

function uid(prefix = "cmd") {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export const COMMANDS = {
  REQUEST_RIDE: "REQUEST_RIDE",
  SET_DRIVER_ONLINE: "SET_DRIVER_ONLINE",
  SET_DRIVER_OFFLINE: "SET_DRIVER_OFFLINE",
  START_TRIP: "START_TRIP",
  COMPLETE_TRIP: "COMPLETE_TRIP",
  SETTLE_PAYMENT: "SETTLE_PAYMENT",
  REFRESH_RUNTIME: "REFRESH_RUNTIME",
};

export function createCommand(commandType, payload = {}, meta = {}) {
  return {
    id: meta.id || uid("cmd"),
    type: commandType,
    payload,
    timestamp: meta.timestamp || new Date().toISOString(),
    source: meta.source || "command-bus",
    correlationId: meta.correlationId || null,
    causationId: meta.causationId || null,
    version: meta.version || 1,
  };
}

export function createCommandBus({ policies = [], handlers = {}, eventStore, emit, validate } = {}) {
  const commandHandlers = new Map(Object.entries(handlers || {}));
  const commandPolicies = Array.isArray(policies) ? [...policies] : [];

  const registerHandler = (commandType, handler) => {
    commandHandlers.set(commandType, handler);
    return handler;
  };

  const registerPolicy = (policy) => {
    if (policy) {
      commandPolicies.push(policy);
    }
    return policy;
  };

  const execute = (command) => {
    const envelope = command?.type ? command : createCommand(command?.commandType || command?.name || COMMANDS.REFRESH_RUNTIME, command?.payload || command || {});

    for (const policy of commandPolicies) {
      const result = policy(envelope);
      if (result && result.allowed === false) {
        return {
          accepted: false,
          reason: result.reason || "Command rejected by policy.",
          command: envelope,
        };
      }
    }

    if (typeof validate === "function") {
      const validation = validate(envelope);
      if (validation && validation.valid === false) {
        return {
          accepted: false,
          reason: validation.reason || "Command failed validation.",
          command: envelope,
        };
      }
    }

    const handler = commandHandlers.get(envelope.type);
    if (typeof handler !== "function") {
      return {
        accepted: false,
        reason: `No handler registered for ${envelope.type}`,
        command: envelope,
      };
    }

    const result = handler(envelope, {
      emit,
      eventStore,
      createEvent: createEventEnvelope,
      events: PLATFORM_EVENTS,
    });

    return {
      accepted: true,
      command: envelope,
      result,
    };
  };

  return {
    registerHandler,
    registerPolicy,
    execute,
    handlers: () => [...commandHandlers.keys()],
    policies: () => [...commandPolicies],
  };
}

export function createDefaultCommandHandlers() {
  return {
    [COMMANDS.REQUEST_RIDE]: (command, runtime) =>
      runtime.emit?.(
        PLATFORM_EVENTS.RIDER_REQUESTED,
        {
          pickup: command.payload?.pickup || null,
          destination: command.payload?.destination || null,
          riderId: command.payload?.riderId || null,
        },
        {
          source: command.source,
          correlationId: command.correlationId,
        },
      ),
    [COMMANDS.SET_DRIVER_ONLINE]: (command, runtime) =>
      runtime.emit?.(
        PLATFORM_EVENTS.DRIVER_STATUS_CHANGED,
        { online: true, driverId: command.payload?.driverId || null },
        { source: command.source, correlationId: command.correlationId },
      ),
    [COMMANDS.SET_DRIVER_OFFLINE]: (command, runtime) =>
      runtime.emit?.(
        PLATFORM_EVENTS.DRIVER_STATUS_CHANGED,
        { online: false, driverId: command.payload?.driverId || null },
        { source: command.source, correlationId: command.correlationId },
      ),
    [COMMANDS.START_TRIP]: (command, runtime) =>
      runtime.emit?.(
        PLATFORM_EVENTS.TRIP_STARTED,
        { rideId: command.payload?.rideId || null },
        { source: command.source, correlationId: command.correlationId },
      ),
    [COMMANDS.COMPLETE_TRIP]: (command, runtime) =>
      runtime.emit?.(
        PLATFORM_EVENTS.TRIP_COMPLETED,
        { rideId: command.payload?.rideId || null },
        { source: command.source, correlationId: command.correlationId },
      ),
    [COMMANDS.SETTLE_PAYMENT]: (command, runtime) =>
      runtime.emit?.(
        PLATFORM_EVENTS.PAYMENT_SETTLED,
        {
          rideId: command.payload?.rideId || null,
          amount: command.payload?.amount || null,
        },
        { source: command.source, correlationId: command.correlationId },
      ),
    [COMMANDS.REFRESH_RUNTIME]: (command, runtime) =>
      runtime.emit?.(
        PLATFORM_EVENTS.OPERATOR_REFRESHED,
        {
          context: command.payload?.context || {},
        },
        { source: command.source, correlationId: command.correlationId },
      ),
  };
}
