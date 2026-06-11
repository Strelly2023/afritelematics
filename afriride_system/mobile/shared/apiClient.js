const DEFAULT_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_TIMEOUT_MS = 5000;
const DEFAULT_RETRIES = 2;

let apiBaseUrl = process.env.EXPO_PUBLIC_AFRIRIDE_API_URL || DEFAULT_BASE_URL;
const tokenCache = new Map();

export function getApiBaseUrl() {
  return apiBaseUrl;
}

export function setApiBaseUrl(value) {
  apiBaseUrl = (value || DEFAULT_BASE_URL).replace(/\/$/, "");
  tokenCache.clear();
}

function randomId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function idempotencyKey(prefix) {
  return randomId(prefix);
}

function actorType(role) {
  return role === "RIDER" ? "rider" : role === "DRIVER" ? "driver" : "operator";
}

async function readPayload(response) {
  const body = await response.text();
  if (!body) {
    return {};
  }
  try {
    return JSON.parse(body);
  } catch {
    throw new Error(`non_json_response_${response.status}`);
  }
}

function extractMessage(payload) {
  if (payload?.error?.message) {
    return payload.error.message;
  }
  if (payload?.detail) {
    return payload.detail;
  }
  return "request_failed";
}

function unwrap(payload) {
  if (payload && typeof payload === "object" && "status" in payload && "data" in payload) {
    if (payload.status === "error") {
      throw new Error(extractMessage(payload));
    }
    return payload.data;
  }
  return payload;
}

function buildClientEvent({ role, userId, path, method, payload }) {
  const timestamp = new Date().toISOString();
  return {
    event_id: randomId("mobile-event"),
    device_id: `mobile-${actorType(role)}-${userId}`,
    actor_type: actorType(role),
    actor_id: userId,
    action: `${method} ${path}`,
    payload,
    local_timestamp: timestamp,
    app_version: "0.1",
    test_mode: true,
  };
}

function withClientEvent(body, clientEvent) {
  if (!body) {
    return body;
  }
  return {
    ...body,
    client_event: clientEvent,
  };
}

async function issueToken(role, userId) {
  const cacheKey = `${role}:${userId}`;
  if (tokenCache.has(cacheKey)) {
    return tokenCache.get(cacheKey);
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  try {
    const response = await fetch(`${apiBaseUrl}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, role }),
      signal: controller.signal,
    });
    const payload = await readPayload(response);
    if (!response.ok || !payload.token) {
      throw new Error(extractMessage(payload));
    }
    tokenCache.set(cacheKey, payload.token);
    return payload.token;
  } finally {
    clearTimeout(timeout);
  }
}

export async function authenticateUser({ role, userId }) {
  const token = await issueToken(role, userId);
  return {
    role,
    user_id: userId,
    token,
  };
}

export async function registerRider({ riderId, fullName, phoneNumber }) {
  const session = await authenticateUser({ role: "RIDER", userId: riderId });
  return {
    ...session,
    profile: {
      rider_id: riderId,
      full_name: fullName,
      phone_number: phoneNumber,
      registration_state: "ACTIVE",
    },
  };
}

export async function updateLocalProfile({ role, userId, profile }) {
  await issueToken(role, userId);
  return {
    role,
    user_id: userId,
    profile,
  };
}

async function request(path, options = {}, retries = DEFAULT_RETRIES) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  const method = options.method || "GET";

  try {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    if (options.role && options.userId) {
      headers.Authorization = `Bearer ${await issueToken(options.role, options.userId)}`;
    }

    let body = options.body;
    if (body && options.role && options.userId && method !== "GET") {
      body = withClientEvent(
        body,
        buildClientEvent({
          role: options.role,
          userId: options.userId,
          path,
          method,
          payload: body,
        }),
      );
    }

    const response = await fetch(`${apiBaseUrl}${path}`, {
      headers,
      method,
      signal: controller.signal,
      body: body ? JSON.stringify(body) : undefined,
    });
    const payload = await readPayload(response);
    if (!response.ok) {
      throw new Error(extractMessage(payload));
    }
    return unwrap(payload);
  } catch (error) {
    if (retries > 0) {
      return request(path, options, retries - 1);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export function getSystemHealth({ operatorId }) {
  return request("/system/health", {
    role: "OPERATOR",
    userId: operatorId,
  });
}

export function getActiveRides({ operatorId }) {
  return request("/rides/active", {
    role: "OPERATOR",
    userId: operatorId,
  });
}

export function getDriversSnapshot({ operatorId }) {
  return request("/system/drivers", {
    role: "OPERATOR",
    userId: operatorId,
  });
}

export function getReplayHealth({ operatorId }) {
  return request("/system/replay/health", {
    role: "OPERATOR",
    userId: operatorId,
  });
}

export function getEvidenceHealth({ operatorId }) {
  return request("/system/evidence", {
    role: "OPERATOR",
    userId: operatorId,
  });
}

export function getGuardViolations({ operatorId }) {
  return request("/system/guards", {
    role: "OPERATOR",
    userId: operatorId,
  });
}

export function getTrustMetrics({ operatorId }) {
  return request("/system/trust-metrics", {
    role: "OPERATOR",
    userId: operatorId,
  });
}

export function getPilotMetrics({ operatorId }) {
  return request("/system/pilot-metrics", {
    role: "OPERATOR",
    userId: operatorId,
  });
}

export function requestRide({ passengerId, pickup, destination, rideId }) {
  return request("/passenger/request-ride", {
    method: "POST",
    role: "RIDER",
    userId: passengerId,
    headers: {
      "Idempotency-Key": idempotencyKey("request-ride"),
    },
    body: {
      passenger_id: passengerId,
      pickup,
      destination,
      ...(rideId ? { ride_id: rideId } : {}),
    },
  });
}

export function getRideStatus({ riderId, rideId }) {
  return request(`/passenger/status/${rideId}`, {
    role: "RIDER",
    userId: riderId,
  });
}

export function cancelRide({ passengerId, rideId }) {
  return request("/passenger/cancel", {
    method: "POST",
    role: "RIDER",
    userId: passengerId,
    headers: {
      "Idempotency-Key": idempotencyKey("cancel-ride"),
    },
    body: {
      passenger_id: passengerId,
      ride_id: rideId,
    },
  });
}

export function getRideReceipt({ riderId, rideId }) {
  return request(`/ride/${rideId}/receipt`, {
    role: "RIDER",
    userId: riderId,
  });
}

export function getRideReplay({ role, userId, rideId }) {
  return request(`/ride/${rideId}/replay`, {
    role,
    userId,
  });
}

export function getRideEvidence({ role, userId, rideId }) {
  return request(`/ride/${rideId}/evidence`, {
    role,
    userId,
  });
}

export function setDriverStatus({ driverId, online }) {
  return request("/driver/status", {
    method: "POST",
    role: "DRIVER",
    userId: driverId,
    headers: {
      "Idempotency-Key": idempotencyKey("driver-status"),
    },
    body: {
      driver_id: driverId,
      online,
    },
  });
}

export function getDriverAssignedRides({ driverId }) {
  return request(`/driver/${driverId}/rides/assigned`, {
    role: "DRIVER",
    userId: driverId,
  });
}

export function getDriverEarnings({ driverId }) {
  return request(`/driver/${driverId}/earnings`, {
    role: "DRIVER",
    userId: driverId,
  });
}

export function acceptRide({ driverId, rideId }) {
  return request(`/ride/${rideId}/accept`, {
    method: "POST",
    role: "DRIVER",
    userId: driverId,
    headers: {
      "Idempotency-Key": idempotencyKey("accept-ride"),
    },
    body: {
      driver_id: driverId,
    },
  });
}

export function startTrip({ driverId, rideId }) {
  return request(`/ride/${rideId}/start`, {
    method: "POST",
    role: "DRIVER",
    userId: driverId,
    headers: {
      "Idempotency-Key": idempotencyKey("start-trip"),
    },
    body: {
      driver_id: driverId,
    },
  });
}

export function arriveRide({ driverId, rideId }) {
  return request(`/ride/${rideId}/arrive`, {
    method: "POST",
    role: "DRIVER",
    userId: driverId,
    headers: {
      "Idempotency-Key": idempotencyKey("arrive-ride"),
    },
    body: {
      driver_id: driverId,
    },
  });
}

export function completeTrip({ driverId, rideId }) {
  return request(`/ride/${rideId}/complete`, {
    method: "POST",
    role: "DRIVER",
    userId: driverId,
    headers: {
      "Idempotency-Key": idempotencyKey("complete-trip"),
    },
    body: {
      driver_id: driverId,
    },
  });
}
