import React from "react";
import { StyleSheet, Text } from "react-native";

import type { RideStatus, RideStatusSnapshot } from "../../core/models/ride";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { LifecycleTimeline, type LifecycleStep } from "../widgets/LifecycleTimeline";
import { MapPreviewCard } from "../widgets/MapPreviewCard";
import { TrustScoreCard } from "../widgets/TrustScoreCard";
import { VerificationStatusCard } from "../widgets/VerificationStatusCard";

type LiveTrackingScreenProps = {
  status: RideStatusSnapshot;
};

export function LiveTrackingScreen({ status }: LiveTrackingScreenProps) {
  const trustScore = status.trustScore || status.driverTrustScore || 92;

  return (
    <SurfacePanel>
      <TrustScoreCard
        score={trustScore}
        checks={["Driver", "GPS", "Payment", "Replay"]}
      />
      <MapPreviewCard routeText={status.locationText || "Location pending"} />
      <LifecycleTimeline steps={buildRideTimeline(status.status)} />
      <VerificationStatusCard
        status={{
          driver: Boolean(status.driverName || status.driverTrustScore),
          gps: Boolean(status.locationText),
          payment: status.status === "completed",
          replay: status.status === "completed",
        }}
      />
      <Text style={styles.status}>Current status: {humanRideStatus(status.status)}</Text>
      {status.driverName ? <Text style={styles.detail}>Driver: {status.driverName}</Text> : null}
      {status.vehicleLabel ? <Text style={styles.detail}>Vehicle: {status.vehicleLabel}</Text> : null}
      {status.etaText ? <Text style={styles.detail}>ETA: {status.etaText}</Text> : null}
    </SurfacePanel>
  );
}

const rideSteps = ["Requested", "Accepted", "Arrived", "Started", "Completed", "Verified"];

function rideStepIndex(status: RideStatus): number {
  switch (status) {
    case "requested":
      return 0;
    case "confirmed":
    case "waiting_for_driver":
    case "driver_assigned":
      return 1;
    case "arriving":
      return 2;
    case "in_progress":
      return 3;
    case "completed":
      return 5;
    case "cancelled":
      return 0;
  }
}

function buildRideTimeline(status: RideStatus): LifecycleStep[] {
  const current = rideStepIndex(status);
  return rideSteps.map((label, index) => ({
    label,
    completed: status === "completed" || index < current,
    current: status !== "completed" && status !== "cancelled" && index === current,
  }));
}

function humanRideStatus(status: RideStatus): string {
  switch (status) {
    case "requested":
      return "Ride requested";
    case "confirmed":
    case "waiting_for_driver":
    case "driver_assigned":
      return "Driver accepted";
    case "arriving":
      return "Driver arriving";
    case "in_progress":
      return "Trip started";
    case "completed":
      return "Trusted trip completed";
    case "cancelled":
      return "Ride cancelled";
  }
}

const styles = StyleSheet.create({
  detail: {
    color: colors.secondary,
    fontSize: 14,
    fontWeight: "700",
  },
  status: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "700",
  },
});
