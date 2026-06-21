import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { RideStatusSnapshot } from "../../core/models/ride";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type DriverAssignedScreenProps = {
  status: RideStatusSnapshot;
};

export function DriverAssignedScreen({ status }: DriverAssignedScreenProps) {
  return (
    <SurfacePanel>
      <Text style={styles.title}>Driver assigned</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Driver</Text>
        <Text style={styles.value}>{status.driverName || "Pending"}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Vehicle</Text>
        <Text style={styles.value}>{status.vehicleLabel || "Pending"}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>ETA</Text>
        <Text style={styles.value}>{status.etaText || "Pending"}</Text>
      </View>
      <View style={styles.trustRow}>
        <Text style={styles.label}>Driver trust</Text>
        <Text style={styles.trustValue}>{status.driverTrustScore || 94}</Text>
      </View>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  row: {
    gap: spacing.xs,
  },
  title: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: "800",
  },
  trustRow: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  trustValue: {
    color: colors.success,
    fontSize: 22,
    fontWeight: "900",
  },
  value: {
    color: colors.secondary,
    fontSize: 16,
    fontWeight: "700",
  },
});
