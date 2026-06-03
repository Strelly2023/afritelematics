import { apiRequest } from "./api";

export function requestRide(payload) {
  return apiRequest("/passenger/request-ride", {
    method: "POST",
    body: payload,
  });
}

export function getRideStatus(rideId) {
  return apiRequest(`/passenger/status/${rideId}`);
}

export function getActiveRide() {
  return apiRequest("/rides/active");
}

export function getRideHistory() {
  return apiRequest("/rides/active");
}

export function acceptRide(rideId, payload) {
  return apiRequest(`/ride/${rideId}/accept`, {
    method: "POST",
    body: payload,
  });
}

export function startRide(rideId, payload) {
  return apiRequest(`/ride/${rideId}/start`, {
    method: "POST",
    body: payload,
  });
}

export function completeRide(rideId, payload) {
  return apiRequest(`/ride/${rideId}/complete`, {
    method: "POST",
    body: payload,
  });
}

export const acceptAssignedRide = acceptRide;
export const startTrip = startRide;
export const completeTrip = completeRide;
