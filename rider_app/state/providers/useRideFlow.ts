import { useEffect, useState } from "react";

import {
  getRideStatus,
  requestRide,
} from "../../core/api/ride.service";
import type { RequestRidePayload } from "../../core/models/ride";
import { loadCompletedRideEvidence } from "../../core/services/rideEvidence.service";
import {
  initialRiderAppState,
  type RiderAppState,
} from "../store/rideStore";

const POLL_INTERVAL_MS = 4000;

export function useRideFlow() {
  const [state, setState] = useState<RiderAppState>(initialRiderAppState);

  async function submitRideRequest(payload: RequestRidePayload) {
    setState((current) => ({ ...current, loading: true, error: "" }));

    try {
      const requestedRide = await requestRide(payload);
      setState((current) => ({
        ...current,
        requestedRide,
        loading: false,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "request_failed",
        loading: false,
      }));
    }
  }

  useEffect(() => {
    const rideId = state.requestedRide?.rideId;
    if (!rideId || state.evidence) {
      return undefined;
    }

    const interval = setInterval(async () => {
      try {
        const statusSnapshot = await getRideStatus(rideId);

        if (statusSnapshot.status === "completed") {
          const evidence = await loadCompletedRideEvidence(rideId);
          setState((current) => ({
            ...current,
            evidence,
            statusSnapshot,
            error: "",
          }));
          return;
        }

        setState((current) => ({
          ...current,
          statusSnapshot,
          error: "",
        }));
      } catch (error) {
        setState((current) => ({
          ...current,
          error: error instanceof Error ? error.message : "status_unavailable",
        }));
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [state.evidence, state.requestedRide?.rideId]);

  return {
    ...state,
    submitRideRequest,
  };
}
