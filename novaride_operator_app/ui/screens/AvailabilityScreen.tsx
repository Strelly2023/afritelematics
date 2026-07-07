import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { DriverAvailability } from "../../core/models/driver";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type AvailabilityScreenProps = {
  availability: DriverAvailability | null;
  loading: boolean;
  onGoAvailable: () => void;
  onGoOffline: () => void;
};

export function AvailabilityScreen({
  availability,
  loading,
  onGoAvailable,
  onGoOffline,
}: AvailabilityScreenProps) {
  return (
    <SurfacePanel>
      <Text style={styles.title}>Availability</Text>
      <Text style={styles.status}>{availability?.status || "offline"}</Text>
      <View style={styles.trustBox}>
        <Text style={styles.trustLabel}>Driver trust</Text>
        <Text style={styles.trustValue}>{availability?.trustScore || 94}</Text>
      </View>
      <View style={styles.actions}>
        <PrimaryButton
          label="Go available"
          onPress={onGoAvailable}
          disabled={loading}
        />
        <PrimaryButton
          label="Go offline"
          onPress={onGoOffline}
          disabled={loading}
          tone="danger"
        />
      </View>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  actions: {
    gap: spacing.sm,
  },
  status: {
    color: colors.success,
    fontSize: 22,
    fontWeight: "900",
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
    fontSize: 24,
    fontWeight: "900",
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
});
