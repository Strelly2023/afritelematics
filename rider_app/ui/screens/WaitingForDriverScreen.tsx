import React from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { MapPreviewCard } from "../widgets/MapPreviewCard";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

export function WaitingForDriverScreen() {
  return (
    <SurfacePanel>
      <MapPreviewCard
        routeText="Dispatch is matching the nearest verified driver"
        progressPct={18}
        statusLabel="Finding driver"
        etaText="Searching live network"
        liveLabel="Queue"
        pickupConfirmed={true}
        dropoffConfirmed={false}
        gpsTraceAvailable={false}
      />
      <View style={styles.row}>
        <ActivityIndicator color={colors.primary} />
        <Text style={styles.text}>Waiting for driver confirmation</Text>
      </View>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  row: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.md,
  },
  text: {
    color: colors.secondary,
    fontSize: 16,
    fontWeight: "700",
  },
});
