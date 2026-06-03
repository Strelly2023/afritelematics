import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { Field } from "../widgets/Field";
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
        <Text style={styles.title}>Book a ride</Text>
        <Text style={styles.subtitle}>Your trip details are sent to AfriRide.</Text>
      </View>
      <Field label="Pickup" value={pickup} onChangeText={onPickupChange} />
      <Field label="Dropoff" value={dropoff} onChangeText={onDropoffChange} />
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
  subtitle: {
    color: colors.muted,
    fontSize: 14,
  },
  title: {
    color: colors.ink,
    fontSize: 24,
    fontWeight: "800",
  },
});
