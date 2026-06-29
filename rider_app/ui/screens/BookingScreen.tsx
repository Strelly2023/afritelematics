import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { Field } from "../widgets/Field";
import { MapPreviewCard } from "../widgets/MapPreviewCard";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type BookingScreenProps = {
  pickup: string;
  dropoff: string;
  loading: boolean;
  error: string;
  onPickupChange: (value: string) => void;
  onDropoffChange: (value: string) => void;
  onRequestRide: () => void;
};

export function BookingScreen({
  pickup,
  dropoff,
  loading,
  error,
  onPickupChange,
  onDropoffChange,
  onRequestRide,
}: BookingScreenProps) {
  return (
    <SurfacePanel>
      <View style={styles.header}>
        <Text style={styles.title}>Where to?</Text>
        <Text style={styles.subtitle}>Pickup, destination, and ride type stay backend-confirmed.</Text>
      </View>
      <Field label="Pickup" value={pickup} onChangeText={onPickupChange} />
      <Field label="Dropoff" value={dropoff} onChangeText={onDropoffChange} />
      <MapPreviewCard
        routeText={`${pickup} to ${dropoff}`}
        progressPct={12}
        statusLabel="Quote ready"
        etaText="Live ETA after dispatch"
        liveLabel="Booking"
        pickupConfirmed={Boolean(pickup)}
        dropoffConfirmed={Boolean(dropoff)}
        gpsTraceAvailable={false}
      />
      <View style={styles.options}>
        <Text style={styles.option}>Economy</Text>
        <Text style={styles.option}>Premium</Text>
        <Text style={styles.option}>Scheduled</Text>
        <Text style={styles.option}>Airport</Text>
      </View>
      <View style={styles.trustBox}>
        <Text style={styles.trustLabel}>Ecosystem trust</Text>
        <Text style={styles.trustValue}>Stable</Text>
      </View>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <PrimaryButton
        label={loading ? "Requesting" : "Request ride"}
        onPress={onRequestRide}
        disabled={loading}
      />
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  error: {
    color: colors.danger,
    fontWeight: "700",
  },
  header: {
    gap: spacing.xs,
  },
  option: {
    backgroundColor: colors.soft,
    borderRadius: 8,
    color: colors.secondary,
    fontSize: 14,
    fontWeight: "800",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  options: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 14,
  },
  title: {
    color: colors.ink,
    fontSize: 24,
    fontWeight: "800",
  },
  trustBox: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  trustLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  trustValue: {
    color: colors.success,
    fontSize: 16,
    fontWeight: "900",
  },
});
