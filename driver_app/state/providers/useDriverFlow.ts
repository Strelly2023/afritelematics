import { useEffect, useState } from "react";

import {
  acceptRide,
  completeTrip,
  getAvailability,
  getRideRequests,
  markArrived,
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

const QUEUE_POLL_INTERVAL_MS = 4000;

export function useDriverFlow(driverId: string) {
  const [state, setState] = useState<DriverAppState>(initialDriverAppState);

  function setError(error: unknown, fallback: string) {
    setState((current) => ({
      ...current,
      error: error instanceof Error ? error.message : fallback,
      loading: false,
    }));
  }

  async function updateAvailability(status: AvailabilityStatus) {
    setState((current) => ({ ...current, loading: true, error: "" }));

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
      setError(error, "availability_unavailable");
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
        if (active) setError(error, "ride_queue_unavailable");
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

  async function acceptRequest(rideId: string) {
    setState((current) => ({ ...current, loading: true, error: "" }));

    try {
      const trip = await acceptRide(rideId, driverId);
      setState((current) => ({
        ...current,
        trip,
        requests: current.requests.filter((request) => request.rideId !== rideId),
        loading: false,
      }));
    } catch (error) {
      setError(error, "accept_unavailable");
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
    acceptRequest,
    rejectRequest,
    updateAvailability,
    markArrived: () => moveTrip("arrived"),
    startTrip: () => moveTrip("started"),
    completeTrip: () => moveTrip("completed"),
  };
}
