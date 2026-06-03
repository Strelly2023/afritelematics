import { apiRequest } from "./api";

export function getReplayReceipt(rideId) {
  return apiRequest(`/ride/${rideId}/replay`);
}

export function getReplayHealth() {
  return apiRequest("/system/replay/health");
}

export const getReplayMonitor = getReplayHealth;
