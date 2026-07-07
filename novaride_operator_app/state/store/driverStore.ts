import type {
  DriverAvailability,
  DriverReplayHistoryItem,
  DriverRideRequest,
  EarningsSummary,
  TripSnapshot,
} from "../../core/models/driver";

export type DriverAppState = {
  availability: DriverAvailability | null;
  requests: DriverRideRequest[];
  trip: TripSnapshot | null;
  earnings: EarningsSummary | null;
  replayHistory: DriverReplayHistoryItem[] | null;
  loading: boolean;
  error: string;
};

export const initialDriverAppState: DriverAppState = {
  availability: null,
  requests: [],
  trip: null,
  earnings: null,
  replayHistory: null,
  loading: false,
  error: "",
};
