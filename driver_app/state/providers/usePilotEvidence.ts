import { useCallback, useEffect, useState } from "react";
import { AppState, type AppStateStatus } from "react-native";

import {
  LOCATION_SAMPLE_INTERVAL_MS,
  NETWORK_SAMPLE_INTERVAL_MS,
} from "../../core/config/environment";
import type {
  DiagnosticsSnapshot,
  PilotEvidenceEvent,
} from "../../core/models/pilotEvidence";
import {
  captureLocationEvidence,
  capturePilotEvidence,
  describePilotEvidenceError,
  extractPilotEvidenceError,
} from "../../core/services/pilotEvidence.service";

const initialDiagnostics: DiagnosticsSnapshot = {
  shiftStarted: false,
  locationSamples: 0,
  networkSamples: 0,
  evidenceSubmitted: 0,
  evidenceFailed: 0,
  routeDeviationEvents: 0,
  gpsSignalLossEvents: 0,
};

type PositionSnapshot = Parameters<typeof captureLocationEvidence>[1];

export function usePilotEvidence(driverId: string) {
  const [diagnostics, setDiagnostics] =
    useState<DiagnosticsSnapshot>(initialDiagnostics);
  const [lastPosition, setLastPosition] = useState<PositionSnapshot>(null);

  const markSubmitted = useCallback((event: PilotEvidenceEvent) => {
    setDiagnostics((current) => ({
      ...current,
      evidenceSubmitted: current.evidenceSubmitted + 1,
      lastEvidenceType: event.type,
      lastEvidenceAt: event.capturedAt,
      lastError: undefined,
    }));
  }, []);

  const markFailed = useCallback((error: unknown) => {
    const evidenceError = extractPilotEvidenceError(error);
    setDiagnostics((current) => ({
      ...current,
      evidenceFailed: current.evidenceFailed + 1,
      lastEvidenceError: evidenceError,
      lastError: describePilotEvidenceError(error),
    }));
  }, []);

  const capture = useCallback(
    async (
      type: Parameters<typeof capturePilotEvidence>[1],
      payload: Record<string, unknown>,
      constraints?: Record<string, unknown>,
      verdict?: Parameters<typeof capturePilotEvidence>[4],
    ) => {
      try {
        const event = await capturePilotEvidence(
          driverId,
          type,
          payload,
          constraints,
          verdict,
        );
        markSubmitted(event);
        return event;
      } catch (error) {
        markFailed(error);
        return null;
      }
    },
    [driverId, markFailed, markSubmitted],
  );

  const startShift = useCallback(async () => {
    const event = await capture("driver_shift_started", {
      driver_id: driverId,
      sample_intervals_ms: {
        location: LOCATION_SAMPLE_INTERVAL_MS,
        network: NETWORK_SAMPLE_INTERVAL_MS,
      },
    });
    if (event) {
      setDiagnostics((current) => ({ ...current, shiftStarted: true }));
    }
  }, [capture, driverId]);

  useEffect(() => {
    if (!diagnostics.shiftStarted) {
      return undefined;
    }

    const subscription = AppState.addEventListener(
      "change",
      (nextState: AppStateStatus) => {
        if (nextState === "background" || nextState === "inactive") {
          void capture("app_backgrounded", { app_state: nextState });
        }
        if (nextState === "active") {
          void capture("app_resumed", { app_state: nextState });
        }
      },
    );
    return () => subscription.remove();
  }, [capture, diagnostics.shiftStarted]);

  useEffect(() => {
    if (!diagnostics.shiftStarted) {
      return undefined;
    }

    const id = setInterval(() => {
      void captureLocationEvidence(driverId, lastPosition)
        .then((events) => {
          events.forEach(markSubmitted);
          const locationEvent = events.find(
            (event) => event.type === "driver_location_event",
          );
          const accuracyEvent = events.find(
            (event) => event.type === "gps_accuracy_event",
          );
          const speedEvent = events.find(
            (event) => event.type === "speed_consistency_event",
          );
          const routeEvent = events.find(
            (event) => event.type === "route_deviation_event",
          );
          setDiagnostics((current) => ({
            ...current,
            locationSamples: current.locationSamples + 1,
            routeDeviationEvents:
              routeEvent?.verdict === "violation"
                ? current.routeDeviationEvents + 1
                : current.routeDeviationEvents,
            lastGpsAccuracyM:
              typeof accuracyEvent?.payload.accuracy_m === "number"
                ? accuracyEvent.payload.accuracy_m
                : current.lastGpsAccuracyM,
            lastSpeedKph:
              typeof speedEvent?.payload.speed_kph === "number"
                ? speedEvent.payload.speed_kph
                : current.lastSpeedKph,
            lastLocation:
              typeof locationEvent?.payload.latitude === "number" &&
              typeof locationEvent?.payload.longitude === "number"
                ? {
                    latitude: locationEvent.payload.latitude,
                    longitude: locationEvent.payload.longitude,
                  }
                : current.lastLocation,
          }));
          if (
            typeof locationEvent?.payload.latitude === "number" &&
            typeof locationEvent?.payload.longitude === "number"
          ) {
            setLastPosition({
              coords: {
                latitude: locationEvent.payload.latitude,
                longitude: locationEvent.payload.longitude,
                accuracy:
                  typeof locationEvent.payload.accuracy_m === "number"
                    ? locationEvent.payload.accuracy_m
                    : null,
              },
              timestamp: Date.parse(
                String(locationEvent.payload.position_timestamp || Date.now()),
              ),
            });
          }
        })
        .catch(async (error) => {
          markFailed(error);
          setDiagnostics((current) => ({
            ...current,
            gpsSignalLossEvents: current.gpsSignalLossEvents + 1,
          }));
          await capture(
            "gps_signal_loss_event",
            { error: error instanceof Error ? error.message : "gps_unavailable" },
            { expected_signal: "available" },
            "violation",
          );
          await capture(
            "gps_accuracy_event",
            { error: error instanceof Error ? error.message : "gps_unavailable" },
            { expected_max_accuracy_m: 50 },
            "violation",
          );
        });
    }, LOCATION_SAMPLE_INTERVAL_MS);

    return () => clearInterval(id);
  }, [
    capture,
    diagnostics.shiftStarted,
    driverId,
    lastPosition,
    markFailed,
    markSubmitted,
  ]);

  useEffect(() => {
    if (!diagnostics.shiftStarted) {
      return undefined;
    }

    const id = setInterval(() => {
      setDiagnostics((current) => ({
        ...current,
        networkSamples: current.networkSamples + 1,
      }));
    }, NETWORK_SAMPLE_INTERVAL_MS);

    return () => clearInterval(id);
  }, [diagnostics.shiftStarted]);

  return {
    diagnostics,
    startShift,
    capture,
  };
}
