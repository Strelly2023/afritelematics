import type {
  DriverReplayHistoryItem,
  EarningsSummary,
  TripSnapshot,
} from "./driver";

function fail(message: string): never {
  throw new Error(message);
}

export function assertTripSnapshot(
  trip: TripSnapshot | null | undefined,
): asserts trip is TripSnapshot {
  if (!trip?.rideId || !trip.status) {
    fail("Invalid trip snapshot: missing system state");
  }
}

export function assertEarningsEvidence(
  earnings: EarningsSummary | null | undefined,
): asserts earnings is EarningsSummary {
  if (!earnings?.driverId || !earnings.totalText || earnings.source !== "core_system") {
    fail("Invalid earnings evidence: missing core source");
  }
}

export function assertReplayHistory(
  replayHistory: DriverReplayHistoryItem[] | null | undefined,
): asserts replayHistory is DriverReplayHistoryItem[] {
  if (!replayHistory || replayHistory.some((item) => !item.rideId || !item.replayId)) {
    fail("Invalid replay history: missing ride evidence");
  }
}
