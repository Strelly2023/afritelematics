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
  value: {
    color: colors.secondary,
    fontSize: 16,
    fontWeight: "700",
  },
});
