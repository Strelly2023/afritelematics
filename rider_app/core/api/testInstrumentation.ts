import { APP_VERSION, DEVICE_ID, TEST_MODE } from "../config/environment";

type ClientEvent = {
  device_id: string;
  app_version: string;
  event_id: string;
  timestamp: string;
  local_timestamp: string;
  actor_type: "rider";
  actor_id: string;
  action: string;
  payload: unknown;
  test_mode: boolean;
};

type CryptoLike = {
  randomUUID?: () => string;
};

function randomId(): string {
  const cryptoApi = (globalThis as { crypto?: CryptoLike }).crypto;
  if (cryptoApi?.randomUUID) {
    return cryptoApi.randomUUID();
  }
  return `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

type ClientEventInput = {
  path: string;
  method: string;
  payload: unknown;
};

function actorIdFromPayload(payload: unknown): string {
  if (payload && typeof payload === "object" && "rider_id" in payload) {
    return String(payload.rider_id);
  }
  return "unknown_rider";
}

export function buildClientEvent(input: ClientEventInput): ClientEvent {
  const localTimestamp = new Date().toISOString();
  return {
    device_id: DEVICE_ID,
    app_version: APP_VERSION,
    event_id: randomId(),
    timestamp: localTimestamp,
    local_timestamp: localTimestamp,
    actor_type: "rider",
    actor_id: actorIdFromPayload(input.payload),
    action: `${input.method} ${input.path}`,
    payload: input.payload ?? null,
    test_mode: TEST_MODE,
  };
}

export function instrumentationHeaders(event: ClientEvent): Record<string, string> {
  return {
    "X-AfriRide-Device-Id": event.device_id,
    "X-AfriRide-App-Version": event.app_version,
    "X-AfriRide-Event-Id": event.event_id,
    "X-AfriRide-Client-Timestamp": event.local_timestamp,
    "X-AfriRide-Test-Mode": String(event.test_mode),
  };
}

export function withClientEvent(body: unknown, event: ClientEvent): unknown {
  if (body && typeof body === "object" && !Array.isArray(body)) {
    return {
      ...body,
      client_event: event,
    };
  }
  return body;
}
