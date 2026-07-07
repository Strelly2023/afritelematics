import {
  getEarnings,
  getReplayHistory,
} from "../api/driver.service";

export async function loadDriverEvidence(driverId: string) {
  const [earnings, replayHistory] = await Promise.all([
    getEarnings(driverId),
    getReplayHistory(driverId),
  ]);

  return {
    earnings,
    replayHistory,
  };
}
