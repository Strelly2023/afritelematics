import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { assertTripSnapshot } from "../../core/models/evidenceGuards";
import type { TripSnapshot, TripStatus } from "../../core/models/driver";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";
import { EvidenceSummaryCard } from "../widgets/EvidenceSummaryCard";
import { LifecycleTimeline, type LifecycleStep } from "../widgets/LifecycleTimeline";
import { MapPreviewCard } from "../widgets/MapPreviewCard";
import { PaymentVerificationCard } from "../widgets/PaymentVerificationCard";
import { TrustScoreCard } from "../widgets/TrustScoreCard";

type TripLifecycleScreenProps = {
  trip: TripSnapshot | null;
  loading: boolean;
  onArrived: () => void;
  onStart: () => void;
  onComplete: () => void;
};

export function TripLifecycleScreen({
  trip,
  loading,
  onArrived,
  onStart,
  onComplete,
}: TripLifecycleScreenProps) {
  if (!trip) {
    return null;
  }

  assertTripSnapshot(trip);
  const nextAction =
    trip.status === "accepted"
      ? { label: "Arrived", onPress: onArrived }
      : trip.status === "arrived"
        ? { label: "Start trip", onPress: onStart }
        : trip.status === "started"
          ? { label: "Complete", onPress: onComplete }
          : null;

  return (
    <SurfacePanel>
      <TrustScoreCard
        score={trip.trustScore || 94}
        checks={["Rider", "Route", "Payment", "Replay"]}
        title="Trip Trust"
      />
      <MapPreviewCard
        routeText={routeText(trip)}
        pickupConfirmed={Boolean(trip.pickupText)}
        dropoffConfirmed={Boolean(trip.dropoffText)}
        gpsTraceAvailable={trip.status === "started" || trip.status === "completed"}
      />
      <LifecycleTimeline steps={buildTripTimeline(trip.status)} />
      <PaymentVerificationCard
        fareCalculated={trip.status !== "cancelled"}
        receiptIssued={trip.status === "completed"}
        noDuplicateCharge={trip.status !== "cancelled"}
      />
      <EvidenceSummaryCard
        summary={
          trip.status === "completed"
            ? "This trip is closed with replay evidence captured for verification."
            : "This trip is being tracked through verified lifecycle and route checks."
        }
      />
      <Text style={styles.title}>Trip details</Text>
      <Text style={styles.status}>{humanTripStatus(trip.status)}</Text>
      <Text style={styles.muted}>Ride: {trip.rideId}</Text>
      {trip.riderName ? <Text style={styles.muted}>Rider: {trip.riderName}</Text> : null}
      {trip.nextInstruction ? (
        <Text style={styles.instruction}>{trip.nextInstruction}</Text>
      ) : null}
      {trip.status === "completed" ? (
        <Text style={styles.completeNote}>Trip closed and replay evidence captured.</Text>
      ) : null}
      {nextAction ? (
        <PrimaryButton
          label={nextAction.label}
          onPress={nextAction.onPress}
          disabled={loading}
        />
      ) : null}
    </SurfacePanel>
  );
}

const tripSteps = ["Accepted", "Arrived", "Started", "Completed", "Verified"];

function tripStepIndex(status: TripStatus): number {
  switch (status) {
    case "accepted":
      return 0;
    case "arrived":
      return 1;
    case "started":
      return 2;
    case "completed":
      return 4;
    case "cancelled":
      return 0;
  }
}

function buildTripTimeline(status: TripStatus): LifecycleStep[] {
  const current = tripStepIndex(status);
  return tripSteps.map((label, index) => ({
    label,
    completed: status === "completed" || index < current,
    current: status !== "completed" && status !== "cancelled" && index === current,
  }));
}

function humanTripStatus(status: TripStatus): string {
  switch (status) {
    case "accepted":
      return "Trip accepted";
    case "arrived":
      return "Arrived at pickup";
    case "started":
      return "Trip started";
    case "completed":
      return "Trusted trip completed";
    case "cancelled":
      return "Trip cancelled";
  }
}

function routeText(trip: TripSnapshot): string {
  if (trip.pickupText && trip.dropoffText) {
    return `${trip.pickupText} to ${trip.dropoffText}`;
  }
  return trip.pickupText || trip.dropoffText || "Route pending";
}

const styles = StyleSheet.create({
  completeNote: {
    color: colors.success,
    fontSize: 14,
    fontWeight: "800",
  },
  instruction: {
    color: colors.secondary,
    fontSize: 15,
    lineHeight: 21,
  },
  muted: {
    color: colors.muted,
    fontSize: 14,
  },
  status: {
    color: colors.success,
    fontSize: 20,
    fontWeight: "900",
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
});
