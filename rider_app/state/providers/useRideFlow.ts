import { useEffect, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Network from "expo-network";

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
import { API_BASE_URL, USE_MOCK_API } from "../../core/config/environment";
import { getAuthToken } from "../../core/api/session";
import {
  AfriRideRealtimeClient,
  type RealtimeConnectionState,
} from "../../../afriride_system/mobile/shared/realtimeClient";
import { enqueueRiderOperation } from "../../core/services/mobility.service";

const POLL_INTERVAL_MS = 4000;

export function useRideFlow() {
  const [state, setState] = useState<RiderAppState>(initialRiderAppState);
  const [realtimeState, setRealtimeState] =
    useState<RealtimeConnectionState>("idle");

  async function submitRideRequest(payload: RequestRidePayload) {
    const optimisticRide = {
      rideId: `optimistic-${Date.now()}`,
      status: "requested" as const,
    };
    setState((current) => ({
      ...current,
      requestedRide: optimisticRide,
      loading: true,
      error: "",
    }));

    try {
      const requestedRide = await requestRide(payload);
      setState((current) => ({
        ...current,
        requestedRide,
        loading: false,
      }));
    } catch (error) {
      const network = await Network.getNetworkStateAsync();
      if (!network.isConnected) {
        await enqueueRiderOperation("/v1/rider/rides", {
          rider_id: payload.riderId,
          pickup: payload.pickup,
          dropoff: payload.dropoff,
          ride_type: "Economy",
        });
        setState((current) => ({
          ...current,
          loading: false,
          error: "Ride saved offline and will sync automatically.",
        }));
        return;
      }
      setState((current) => ({
        ...current,
        requestedRide: null,
        error: error instanceof Error ? error.message : "request_failed",
        loading: false,
      }));
    }
  }

  useEffect(() => {
    const rideId = state.requestedRide?.rideId;
    if (!rideId || rideId.startsWith("optimistic-") || state.evidence) {
      return undefined;
    }

    let active = true;
    let timeout: ReturnType<typeof setTimeout> | undefined;
    const refreshStatus = async () => {
      try {
        const statusSnapshot = await getRideStatus(rideId);
        if (!active) return;

        if (statusSnapshot.status === "completed") {
          const evidence = await loadCompletedRideEvidence(rideId);
          if (!active) return;
          setState((current) => ({
            ...current,
            evidence,
            statusSnapshot,
            error: "",
          }));
        } else {
          setState((current) => ({
            ...current,
            statusSnapshot,
            error: "",
          }));
        }
      } catch (error) {
        if (active) {
          setState((current) => ({
            ...current,
            error: error instanceof Error ? error.message : "status_unavailable",
          }));
        }
      } finally {
        if (active) timeout = setTimeout(refreshStatus, POLL_INTERVAL_MS);
      }
    };

    void refreshStatus();
    return () => {
      active = false;
      if (timeout) clearTimeout(timeout);
    };
  }, [state.evidence, state.requestedRide?.rideId]);

  useEffect(() => {
    const rideId = state.requestedRide?.rideId;
    const token = getAuthToken();
    if (!rideId || rideId.startsWith("optimistic-") || !token || USE_MOCK_API) return undefined;
    const client = new AfriRideRealtimeClient({
      apiBaseUrl: API_BASE_URL,
      actorId: "rider-demo-001",
      token,
      rideId,
      storage: AsyncStorage,
      onState: setRealtimeState,
      onEvent: (event) => {
        if (
          event.type === "RIDE_STATE_UPDATED" ||
          event.type === "DRIVER_LOCATION_UPDATED" ||
          event.type === "SERVER_PUSH_EVENT"
        ) {
          void getRideStatus(rideId).then((statusSnapshot) => {
            setState((current) => ({ ...current, statusSnapshot, error: "" }));
          });
        }
      },
    });
    void client.start();
    return () => client.stop();
  }, [state.requestedRide?.rideId]);

  return {
    ...state,
    realtimeState,
    submitRideRequest,
  };
}
