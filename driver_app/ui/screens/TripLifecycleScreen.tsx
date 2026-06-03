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

  return (
    <SurfacePanel>
      <Text style={styles.title}>Trip lifecycle</Text>
      <Text style={styles.status}>{trip.status}</Text>
      <Text style={styles.muted}>Ride: {trip.rideId}</Text>
      {trip.riderName ? <Text style={styles.muted}>Rider: {trip.riderName}</Text> : null}
      {trip.nextInstruction ? (
        <Text style={styles.instruction}>{trip.nextInstruction}</Text>
      ) : null}
      <View style={styles.actions}>
        <PrimaryButton label="Arrived" onPress={onArrived} disabled={loading} />
        <PrimaryButton label="Start trip" onPress={onStart} disabled={loading} />
        <PrimaryButton label="Complete" onPress={onComplete} disabled={loading} />
      </View>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  actions: {
    gap: spacing.sm,
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
