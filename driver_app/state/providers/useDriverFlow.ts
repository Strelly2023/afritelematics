import { useEffect, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";

import {
  acceptRide,
  completeTrip,
  getAvailability,
  getRideRequests,
  markArrived,
  mapRealtimeTrip,
  rejectRide,
  setAvailability,
  startTrip,
} from "../../core/api/driver.service";
import { loadDriverEvidence } from "../../core/services/driverEvidence.service";
import type { AvailabilityStatus } from "../../core/models/driver";
import {
  initialDriverAppState,
  type DriverAppState,
} from "../store/driverStore";
import { API_BASE_URL, USE_MOCK_API } from "../../core/config/environment";
import { getAuthToken } from "../../core/api/session";
import {
  AfriRideRealtimeClient,
  type RealtimeConnectionState,
} from "../../../afriride_system/mobile/shared/realtimeClient";
import { queueDriverOperation } from "../../core/services/mobility.service";

const QUEUE_POLL_INTERVAL_MS = 4000;
export const DRIVER_CONNECTIVITY_STATES = [
  "NETWORK_OFFLINE",
  "API_UNAVAILABLE",
  "AUTH_REQUIRED",
  "SYNCING",
  "ONLINE_NOT_CONFIRMED",
  "DISPATCHABLE",
  "ON_TRIP",
  "OFF_DUTY",
] as const;

export function useDriverFlow(driverId: string) {
  const [state, setState] = useState<DriverAppState>(initialDriverAppState);
  const [realtimeState, setRealtimeState] =
    useState<RealtimeConnectionState>("idle");

  function setError(error: unknown, fallback: string) {
    setState((current) => ({
      ...current,
      error: error instanceof Error ? error.message : fallback,
      loading: false,
    }));
  }

  async function updateAvailability(status: AvailabilityStatus) {
    const previous = state.availability;
    setState((current) => ({
      ...current,
      availability: {
        ...(current.availability || { driverId }),
        status,
        updatedAt: new Date().toISOString(),
      },
      loading: true,
      error: "",
    }));

    try {
      const availability = await setAvailability(driverId, status);
      const requests = status === "available" ? await getRideRequests(driverId) : [];
      setState((current) => ({
        ...current,
        availability,
        requests,
        loading: false,
      }));
    } catch (error) {
      await queueDriverOperation(`/v1/driver/${encodeURIComponent(driverId)}/availability`, {
        status,
      });
      const safeAvailability =
        previous?.status === "available"
          ? {
              ...previous,
              status: "offline" as const,
              updatedAt: new Date().toISOString(),
            }
          : previous || {
              driverId,
              status: "offline" as const,
              updatedAt: new Date().toISOString(),
            };
      setState((current) => ({
        ...current,
        availability: safeAvailability,
        requests: [],
        loading: false,
        error:
          status === "available"
            ? "Availability saved locally. Server confirmation is required before dispatchable status."
            : "Availability saved and will sync automatically.",
      }));
    }
  }

  useEffect(() => {
    let active = true;

    const hydrateAvailability = async () => {
      try {
        const availability = await getAvailability(driverId);
        if (!active) return;
        const requests =
          availability.status === "available"
            ? await getRideRequests(driverId)
            : [];
        if (!active) return;
        setState((current) => ({
          ...current,
          availability,
          requests,
          error: "",
        }));
      } catch (error) {
        if (active) setError(error, "availability_unavailable");
      }
    };

    void hydrateAvailability();
    return () => {
      active = false;
    };
  }, [driverId]);

  useEffect(() => {
    if (state.availability?.status !== "available") {
      return undefined;
    }

    let active = true;
    let timeout: ReturnType<typeof setTimeout> | undefined;

    const refreshQueue = async () => {
      try {
        const requests = await getRideRequests(driverId);
        if (active) {
          setState((current) => ({
            ...current,
            requests,
            error: "",
          }));
        }
      } catch (error) {
        if (active) {
          setState((current) => ({
            ...current,
            availability: current.availability
              ? {
                  ...current.availability,
                  status: "offline",
                  updatedAt: new Date().toISOString(),
                }
              : current.availability,
            requests: [],
            loading: false,
            error:
              "Ride queue sync failed. Driver is online-not-confirmed and not dispatchable until the server confirms availability.",
          }));
        }
      } finally {
        if (active) {
          timeout = setTimeout(refreshQueue, QUEUE_POLL_INTERVAL_MS);
        }
      }
    };

    void refreshQueue();
    return () => {
      active = false;
      if (timeout) clearTimeout(timeout);
    };
  }, [driverId, state.availability?.status]);

  useEffect(() => {
    const token = getAuthToken();
    if (!token || USE_MOCK_API || state.availability?.status !== "available") {
      return undefined;
    }
    const client = new AfriRideRealtimeClient({
      apiBaseUrl: API_BASE_URL,
      actorId: driverId,
      token,
      rideId: state.trip?.rideId,
      storage: AsyncStorage,
      onState: setRealtimeState,
      onEvent: (event) => {
        if (event.type === "DISPATCH_REQUESTED") {
          void getRideRequests(driverId).then((requests) => {
            setState((current) => ({ ...current, requests, error: "" }));
          });
        }
        if (event.type === "RIDE_STATE_UPDATED") {
          const trip = mapRealtimeTrip(event.data);
          if (trip) {
            setState((current) => ({
              ...current,
              trip: trip.status === "completed" ? null : trip,
              requests: current.requests.filter((item) => item.rideId !== trip.rideId),
            }));
          }
        }
      },
    });
    void client.start();
    return () => client.stop();
  }, [driverId, state.availability?.status, state.trip?.rideId]);

  async function acceptRequest(rideId: string) {
    const acceptedRequest = state.requests.find((request) => request.rideId === rideId);
    setState((current) => ({
      ...current,
      requests: current.requests.filter((request) => request.rideId !== rideId),
      loading: true,
      error: "",
    }));

    try {
      const trip = await acceptRide(rideId, driverId);
      setState((current) => ({
        ...current,
        trip,
        requests: current.requests.filter((request) => request.rideId !== rideId),
        loading: false,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        requests: acceptedRequest ? [acceptedRequest, ...current.requests] : current.requests,
        loading: false,
        error: error instanceof Error ? error.message : "accept_unavailable",
      }));
    }
  }

  async function rejectRequest(rideId: string) {
    setState((current) => ({ ...current, loading: true, error: "" }));

    try {
      const trip = await rejectRide(rideId, driverId);
      setState((current) => ({
        ...current,
        trip,
        requests: current.requests.filter((request) => request.rideId !== rideId),
        loading: false,
      }));
    } catch (error) {
      setError(error, "reject_unavailable");
    }
  }

  async function moveTrip(action: "arrived" | "started" | "completed") {
    const rideId = state.trip?.rideId;
    if (!rideId) {
      return;
    }

    setState((current) => ({ ...current, loading: true, error: "" }));

    try {
      const trip =
        action === "arrived"
          ? await markArrived(rideId, driverId)
          : action === "started"
            ? await startTrip(rideId, driverId)
            : await completeTrip(rideId, driverId);
      const evidence =
        trip.status === "completed" ? await loadDriverEvidence(driverId) : null;
      const requests =
        trip.status === "completed" && state.availability?.status === "available"
          ? await getRideRequests(driverId)
          : state.requests;

      setState((current) => ({
        ...current,
        trip: trip.status === "completed" ? null : trip,
        requests,
        earnings: evidence?.earnings || current.earnings,
        replayHistory: evidence?.replayHistory || current.replayHistory,
        loading: false,
      }));
    } catch (error) {
      setError(error, "trip_update_unavailable");
    }
  }

  return {
    ...state,
    realtimeState,
    acceptRequest,
    rejectRequest,
    updateAvailability,
    markArrived: () => moveTrip("arrived"),
    startTrip: () => moveTrip("started"),
    completeTrip: () => moveTrip("completed"),
  };
}
