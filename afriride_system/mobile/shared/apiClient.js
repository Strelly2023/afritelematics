const DEFAULT_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_TIMEOUT_MS = 5000;
const DEFAULT_RETRIES = 2;

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_AFRIRIDE_API_URL || DEFAULT_BASE_URL;

function idempotencyKey(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function request(path, options = {}, retries = DEFAULT_RETRIES) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      signal: controller.signal,
      ...options,
    });

    const payload = await response.json();

    if (!response.ok || payload.status === "error") {
      throw new Error(payload.error?.message || payload.detail || "request_failed");
    }

    return payload.data;
  } catch (error) {
    if (retries > 0) {
      return request(path, options, retries - 1);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export function requestRide({ passengerId, pickup, destination, rideId }) {
  return request("/passenger/request-ride", {
    method: "POST",
    headers: {
      "Idempotency-Key": idempotencyKey("request-ride"),
    },
    body: JSON.stringify({
      passenger_id: passengerId,
      pickup,
      destination,
      ride_id: rideId,
    }),
  });
}

export function getRideStatus(rideId) {
  return request(`/passenger/status/${rideId}`);
}

export function setDriverStatus({ driverId, online }) {
  return request("/driver/status", {
    method: "POST",
    headers: {
      "Idempotency-Key": idempotencyKey("driver-status"),
    },
    body: JSON.stringify({
      driver_id: driverId,
      online,
    }),
  });
}

export function getDriverRequests(driverId) {
  return request(`/driver/requests/${driverId}`);
}

export function acceptRide({ driverId, rideId }) {
  return request("/driver/accept", {
    method: "POST",
    headers: {
      "Idempotency-Key": idempotencyKey("accept-ride"),
    },
    body: JSON.stringify({
      driver_id: driverId,
      ride_id: rideId,
    }),
  });
}

export function startTrip({ driverId, rideId }) {
  return request("/driver/start", {
    method: "POST",
    headers: {
      "Idempotency-Key": idempotencyKey("start-trip"),
    },
    body: JSON.stringify({
      driver_id: driverId,
      ride_id: rideId,
    }),
  });
}

export function completeTrip({ driverId, rideId }) {
  return request("/driver/complete", {
    method: "POST",
    headers: {
      "Idempotency-Key": idempotencyKey("complete-trip"),
    },
    body: JSON.stringify({
      driver_id: driverId,
      ride_id: rideId,
    }),
  });
}
