import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type VehicleManagementScreenProps = {
  make: string;
  model: string;
  plate: string;
  status?: string;
};

export function VehicleManagementScreen({
  make,
  model,
  plate,
  status = "Verified",
}: VehicleManagementScreenProps) {
  return (
    <SurfacePanel>
      <Text style={styles.title}>Vehicle</Text>
      <View style={styles.vehicleCard}>
        <Text style={styles.vehicle}>{make} {model}</Text>
        <Text style={styles.muted}>Plate: {plate}</Text>
        <Text style={styles.status}>{status}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Insurance</Text>
        <Text style={styles.status}>Verified</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Inspection</Text>
        <Text style={styles.status}>Current</Text>
      </View>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  muted: {
    color: colors.muted,
    fontSize: 14,
  },
  row: {
    alignItems: "center",
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: spacing.md,
  },
  status: {
    color: colors.success,
    fontSize: 14,
    fontWeight: "900",
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  vehicle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "900",
  },
  vehicleCard: {
    backgroundColor: colors.soft,
    borderRadius: 8,
    gap: spacing.xs,
    padding: spacing.md,
  },
});
