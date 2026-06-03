import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { RideStatusSnapshot } from "../../core/models/ride";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type LiveTrackingScreenProps = {
  status: RideStatusSnapshot;
};

export function LiveTrackingScreen({ status }: LiveTrackingScreenProps) {
  return (
    <SurfacePanel>
      <View style={styles.map}>
        <Text style={styles.mapText}>{status.locationText || "Location pending"}</Text>
      </View>
      <Text style={styles.status}>Current status: {status.status}</Text>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  map: {
    alignItems: "center",
    backgroundColor: colors.soft,
    borderRadius: 8,
    minHeight: 180,
    justifyContent: "center",
    padding: spacing.lg,
  },
  mapText: {
    color: colors.secondary,
    fontSize: 16,
    fontWeight: "800",
    textAlign: "center",
  },
  status: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "700",
  },
});
