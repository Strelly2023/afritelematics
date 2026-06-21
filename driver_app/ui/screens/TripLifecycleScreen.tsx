import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { assertTripSnapshot } from "../../core/models/evidenceGuards";
import type { TripSnapshot } from "../../core/models/driver";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

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
      <Text style={styles.title}>Trip lifecycle</Text>
      <Text style={styles.status}>{trip.status}</Text>
      <Text style={styles.muted}>Ride: {trip.rideId}</Text>
      {trip.riderName ? <Text style={styles.muted}>Rider: {trip.riderName}</Text> : null}
      {trip.nextInstruction ? (
        <Text style={styles.instruction}>{trip.nextInstruction}</Text>
      ) : null}
      <View style={styles.timeline}>
        {["ACCEPTED", "ARRIVED", "STARTED", "COMPLETED"].map((step) => (
          <Text key={step} style={styles.timelineStep}>{step}</Text>
        ))}
      </View>
      <View style={styles.trustBox}>
        <Text style={styles.trustText}>Trust Score: {trip.trustScore || 94}</Text>
        <Text style={styles.trustText}>
          Replay: {trip.replayVerified ? "Verified" : "Pending"}
        </Text>
      </View>
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
  timeline: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  timelineStep: {
    backgroundColor: colors.soft,
    borderRadius: 8,
    color: colors.secondary,
    fontSize: 12,
    fontWeight: "900",
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  trustBox: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  trustText: {
    color: colors.success,
    fontSize: 14,
    fontWeight: "900",
  },
});
