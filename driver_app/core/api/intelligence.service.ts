import { apiRequest } from "./client";
import { USE_MOCK_API } from "../config/environment";
import { mockGetDriverIntelligence } from "./mockDriver.service";
import type { DriverIntelligenceFeed } from "../models/intelligence";

type DriverIntelligenceResponse = DriverIntelligenceFeed;

export async function getDriverIntelligence(): Promise<DriverIntelligenceFeed> {
  if (USE_MOCK_API) {
    return mockGetDriverIntelligence();
  }

  const result = await apiRequest<DriverIntelligenceResponse>("/v1/intelligence/driver");
  return result;
}
