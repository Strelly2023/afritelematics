import { apiRequest } from "./client";
import { USE_MOCK_API } from "../config/environment";
import { mockGetPassengerIntelligence } from "./mockRide.service";
import type { PassengerIntelligenceFeed } from "../models/intelligence";

type PassengerIntelligenceResponse = PassengerIntelligenceFeed;

export async function getPassengerIntelligence(): Promise<PassengerIntelligenceFeed> {
  if (USE_MOCK_API) {
    return mockGetPassengerIntelligence();
  }

  return apiRequest<PassengerIntelligenceResponse>("/v1/intelligence/passenger");
}
