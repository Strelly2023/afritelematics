import {
  API_BASE_URL,
  APP_VERSION,
  DEVICE_ID,
  PILOT_GPS_ACCURACY_THRESHOLD_M,
  PILOT_LATENCY_THRESHOLD_MS,
  PILOT_ROUTE_DEVIATION_THRESHOLD_M,
  PILOT_SPEED_THRESHOLD_KPH,
  REQUEST_TIMEOUT_MS,
  TEST_MODE,
} from "../config/environment";
import type {
  EvidenceError,
  PilotEvidenceEvent,
  PilotEvidenceType,
  PilotEvidenceVerdict,
} from "../models/pilotEvidence";

const EVIDENCE_ENDPOINT = "/pilot/evidence";

type GeoPosition = {
  coords: {
    latitude: number;
    longitude: number;
    accuracy?: number | null;
    altitude?: number | null;
    heading?: number | null;
    speed?: number | null;
  };
  timestamp: number;
};

type GeoError = {
  code?: number;
  message?: string;
};

type NavigatorWithGeo = {
  geolocation?: {
    getCurrentPosition: (
      success: (position: GeoPosition) => void,
      error?: (error: GeoError) => void,
      options?: {
        enableHighAccuracy?: boolean;
        timeout?: number;
        maximumAge?: number;
      },
    ) => void;
  };
};

type ExpoLocationModule = typeof import("expo-location");

type EvidenceResponse = {
  status: "captured";
  evidence_id: string;
  node_id: string;
  proposal_id: string;
};

type EvidenceTraceContext = {
  traceId: string;
  traceparent: string;
};

type EvidenceErrorContext = {
  durationMs: number;
  endpoint?: string;
  traceId: string;
};

class EvidenceRequestFailure extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "EvidenceRequestFailure";
    this.status = status;
  }
}

export class PilotEvidenceSubmitError extends Error {
  evidenceError: EvidenceError;

  constructor(evidenceError: EvidenceError) {
    super(evidenceError.message);
    this.name = "PilotEvidenceSubmitError";
    this.evidenceError = evidenceError;
  }
}

export function describePilotEvidenceError(error: unknown): string {
  return extractPilotEvidenceError(error).message;
}

export function extractPilotEvidenceError(error: unknown): EvidenceError {
  if (error instanceof PilotEvidenceSubmitError) {
    return error.evidenceError;
  }
  return buildEvidenceError(error, {
    durationMs: 0,
    endpoint: EVIDENCE_ENDPOINT,
    traceId: "unknown",
  });
}

export function buildEvidenceError(
  error: unknown,
  context: EvidenceErrorContext,
): EvidenceError {
  const endpoint = context.endpoint || EVIDENCE_ENDPOINT;
  if (error instanceof Error) {
    if (error.name === "AbortError") {
      return {
        type: "timeout",
        severity: "warning",
        endpoint,
        durationMs: context.durationMs,
        message: `evidence_api_timeout after ${REQUEST_TIMEOUT_MS}ms at ${API_BASE_URL}${endpoint}`,
        traceId: context.traceId,
      };
    }
    if (/Network request failed|Failed to fetch|Load failed/i.test(error.message)) {
      return {
        type: "network",
        severity: "warning",
        endpoint,
        durationMs: context.durationMs,
        message: `evidence_api_unreachable at ${API_BASE_URL}${endpoint}`,
        traceId: context.traceId,
      };
    }
    if (error instanceof EvidenceRequestFailure) {
      return {
        type: error.status >= 500 ? "server" : "validation",
        severity: error.status >= 500 ? "error" : "warning",
        endpoint,
        durationMs: context.durationMs,
        message: error.message,
        traceId: context.traceId,
      };
    }
    return {
      type: "unknown",
      severity: "error",
      endpoint,
      durationMs: context.durationMs,
      message: error.message,
      traceId: context.traceId,
    };
  }
  return {
    type: "unknown",
    severity: "error",
    endpoint,
    durationMs: context.durationMs,
    message: "evidence_submit_failed",
    traceId: context.traceId,
  };
}

export function generateEvidenceTraceContext(): EvidenceTraceContext {
  const traceId = randomHex(32);
  const spanId = randomHex(16);
  return {
    traceId,
    traceparent: `00-${traceId}-${spanId}-01`,
  };
}

function randomHex(length: number): string {
  const byteLength = Math.ceil(length / 2);
  const bytes = new Uint8Array(byteLength);
  const cryptoApi = (globalThis as {
    crypto?: { getRandomValues?: (array: Uint8Array) => Uint8Array };
  }).crypto;

  if (cryptoApi?.getRandomValues) {
    cryptoApi.getRandomValues(bytes);
  } else {
    for (let index = 0; index < byteLength; index += 1) {
      bytes[index] = Math.floor(Math.random() * 256);
    }
  }

  return Array.from(bytes)
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, length);
}

async function readEvidenceResponse(response: Response): Promise<unknown> {
  const body = await response.text();
  if (!body) {
    return {};
  }
  try {
    return JSON.parse(body);
  } catch {
    const preview = body.replace(/\s+/g, " ").slice(0, 160);
    throw new Error(
      `non_json_evidence_response status=${response.status} content_type=${response.headers.get(
        "content-type",
      ) || "unknown"} body=${preview}`,
    );
  }
}

export function buildEvidenceEvent(
  driverId: string,
  type: PilotEvidenceType,
  payload: Record<string, unknown>,
  constraints: Record<string, unknown> = {},
  verdict: PilotEvidenceVerdict = "observed",
): PilotEvidenceEvent {
  return {
    type,
    driverId,
    surface: "driver_mobile",
    payload: {
      ...payload,
      device_id: DEVICE_ID,
      app_version: APP_VERSION,
      test_mode: TEST_MODE,
    },
    constraints,
    verdict,
    capturedAt: new Date().toISOString(),
  };
}

export async function submitPilotEvidence(
  event: PilotEvidenceEvent,
): Promise<EvidenceResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const startedAt = Date.now();
  const traceContext = generateEvidenceTraceContext();

  try {
    const response = await fetch(`${API_BASE_URL}${EVIDENCE_ENDPOINT}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-AfriRide-Device-Id": DEVICE_ID,
        "X-AfriRide-App-Version": APP_VERSION,
        "X-AfriRide-Event-Id": `pilot-${event.type}-${Date.now()}`,
        "X-AfriRide-Trace-Id": traceContext.traceId,
        "X-AfriRide-Client-Timestamp": event.capturedAt,
        "X-AfriRide-Test-Mode": String(TEST_MODE),
        traceparent: traceContext.traceparent,
      },
      body: JSON.stringify({
        type: event.type,
        driver_id: event.driverId,
        surface: event.surface,
        payload: event.payload,
        constraints: event.constraints || {},
        verdict: event.verdict || "observed",
        captured_at: event.capturedAt,
      }),
      signal: controller.signal,
    });

    const payload = await readEvidenceResponse(response);
    if (!response.ok) {
      throw new EvidenceRequestFailure(
        payload && typeof payload === "object" && "detail" in payload
          ? String(payload.detail)
          : "pilot_evidence_submit_failed",
        response.status,
      );
    }
    return payload as EvidenceResponse;
  } catch (error) {
    throw new PilotEvidenceSubmitError(
      buildEvidenceError(error, {
        durationMs: Date.now() - startedAt,
        endpoint: EVIDENCE_ENDPOINT,
        traceId: traceContext.traceId,
      }),
    );
  } finally {
    clearTimeout(timeout);
  }
}

export async function capturePilotEvidence(
  driverId: string,
  type: PilotEvidenceType,
  payload: Record<string, unknown>,
  constraints?: Record<string, unknown>,
  verdict?: PilotEvidenceVerdict,
): Promise<PilotEvidenceEvent> {
  const event = buildEvidenceEvent(driverId, type, payload, constraints, verdict);
  await submitPilotEvidence(event);
  return event;
}

export async function readCurrentPosition(): Promise<GeoPosition> {
  const location = await loadExpoLocation();
  if (location) {
    try {
      return await readExpoLocation(location);
    } catch (error) {
      if (!isMissingNativeLocation(error)) {
        throw error;
      }
    }
  }
  return readNavigatorLocation();
}

async function loadExpoLocation(): Promise<ExpoLocationModule | null> {
  try {
    return await import("expo-location");
  } catch {
    return null;
  }
}

async function readExpoLocation(location: ExpoLocationModule): Promise<GeoPosition> {
  const permission = await location.requestForegroundPermissionsAsync();
  if (permission.status !== location.PermissionStatus.GRANTED) {
    throw new Error(`location_permission_${permission.status}`);
  }

  const position = await location.getCurrentPositionAsync({
    accuracy: location.Accuracy.High,
  });
  return {
    coords: {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
      altitude: position.coords.altitude,
      heading: position.coords.heading,
      speed: position.coords.speed,
    },
    timestamp: position.timestamp,
  };
}

function isMissingNativeLocation(error: unknown): boolean {
  return (
    error instanceof Error &&
    /ExpoLocation|native module|Cannot find native module/i.test(error.message)
  );
}

function readNavigatorLocation(): Promise<GeoPosition> {
  const navigatorApi = (globalThis as { navigator?: NavigatorWithGeo }).navigator;

  if (!navigatorApi?.geolocation) {
    return Promise.reject(new Error("geolocation_unavailable"));
  }

  return new Promise((resolve, reject) => {
    navigatorApi.geolocation?.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      maximumAge: 1000,
      timeout: 7000,
    });
  });
}

export async function captureLocationEvidence(
  driverId: string,
  previousPosition?: GeoPosition | null,
): Promise<PilotEvidenceEvent[]> {
  const position = await readCurrentPosition();
  const accuracy = position.coords.accuracy ?? null;
  const verdict =
    typeof accuracy === "number" && accuracy > PILOT_GPS_ACCURACY_THRESHOLD_M
      ? "violation"
      : "pass";
  const payload = {
    latitude: position.coords.latitude,
    longitude: position.coords.longitude,
    accuracy_m: accuracy,
    altitude: position.coords.altitude ?? null,
    heading: position.coords.heading ?? null,
    speed: position.coords.speed ?? null,
    position_timestamp: new Date(position.timestamp).toISOString(),
  };

  const locationEvent = await capturePilotEvidence(
    driverId,
    "driver_location_event",
    payload,
  );
  const accuracyEvent = await capturePilotEvidence(
    driverId,
    "gps_accuracy_event",
    payload,
    { expected_max_accuracy_m: PILOT_GPS_ACCURACY_THRESHOLD_M },
    verdict,
  );

  const movementEvents = previousPosition
    ? await captureMovementEvidence(driverId, previousPosition, position)
    : [];

  return [locationEvent, accuracyEvent, ...movementEvents];
}

export function latencyVerdict(latencyMs: number): PilotEvidenceVerdict {
  return latencyMs > PILOT_LATENCY_THRESHOLD_MS ? "violation" : "pass";
}

async function captureMovementEvidence(
  driverId: string,
  previousPosition: GeoPosition,
  currentPosition: GeoPosition,
): Promise<PilotEvidenceEvent[]> {
  const distanceM = distanceMeters(previousPosition, currentPosition);
  const elapsedSeconds = Math.max(
    (currentPosition.timestamp - previousPosition.timestamp) / 1000,
    1,
  );
  const speedKph = (distanceM / elapsedSeconds) * 3.6;
  const payload = {
    distance_m: Math.round(distanceM),
    elapsed_seconds: Math.round(elapsedSeconds),
    speed_kph: Math.round(speedKph),
    previous: {
      latitude: previousPosition.coords.latitude,
      longitude: previousPosition.coords.longitude,
      timestamp: new Date(previousPosition.timestamp).toISOString(),
    },
    current: {
      latitude: currentPosition.coords.latitude,
      longitude: currentPosition.coords.longitude,
      timestamp: new Date(currentPosition.timestamp).toISOString(),
    },
  };
  const speedEvent = await capturePilotEvidence(
    driverId,
    "speed_consistency_event",
    payload,
    { expected_max_speed_kph: PILOT_SPEED_THRESHOLD_KPH },
    speedKph > PILOT_SPEED_THRESHOLD_KPH ? "violation" : "pass",
  );
  const routeEvent = await capturePilotEvidence(
    driverId,
    "route_deviation_event",
    payload,
    { expected_max_sample_distance_m: PILOT_ROUTE_DEVIATION_THRESHOLD_M },
    distanceM > PILOT_ROUTE_DEVIATION_THRESHOLD_M ? "violation" : "pass",
  );

  return [speedEvent, routeEvent];
}

function distanceMeters(previousPosition: GeoPosition, currentPosition: GeoPosition) {
  const earthRadiusM = 6371000;
  const previousLat = toRadians(previousPosition.coords.latitude);
  const currentLat = toRadians(currentPosition.coords.latitude);
  const deltaLat = toRadians(
    currentPosition.coords.latitude - previousPosition.coords.latitude,
  );
  const deltaLon = toRadians(
    currentPosition.coords.longitude - previousPosition.coords.longitude,
  );
  const a =
    Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
    Math.cos(previousLat) *
      Math.cos(currentLat) *
      Math.sin(deltaLon / 2) *
      Math.sin(deltaLon / 2);
  return earthRadiusM * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function toRadians(value: number) {
  return (value * Math.PI) / 180;
}
