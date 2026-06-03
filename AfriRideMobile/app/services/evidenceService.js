import { apiRequest } from "./api";

export function getReceipt(rideId) {
  return apiRequest(`/ride/${rideId}/receipt`);
}

export function getEvidence(rideId) {
  return getReceipt(rideId);
}

export function getEvidenceSummary() {
  return apiRequest("/system/evidence");
}

export function getGuardViolations() {
  return apiRequest("/system/guards");
}
