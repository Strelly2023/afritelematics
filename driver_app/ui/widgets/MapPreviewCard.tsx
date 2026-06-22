import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { trustColors, trustSpacing } from "../theme/trustTokens";

type MapPreviewCardProps = {
  routeText?: string;
  pickupConfirmed?: boolean;
  dropoffConfirmed?: boolean;
  gpsTraceAvailable?: boolean;
};

export function MapPreviewCard({
  routeText = "Route verification pending",
  pickupConfirmed = true,
  dropoffConfirmed = true,
  gpsTraceAvailable = true,
}: MapPreviewCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.preview}>
        <Text style={styles.routeText}>{routeText}</Text>
      </View>
      <Text style={styles.check}>Pickup: {pickupConfirmed ? "Confirmed" : "Review"}</Text>
      <Text style={styles.check}>Drop-off: {dropoffConfirmed ? "Confirmed" : "Review"}</Text>
      <Text style={styles.check}>GPS trace: {gpsTraceAvailable ? "Available" : "Pending"}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: trustColors.CARD,
    borderColor: trustColors.BORDER,
    borderRadius: 8,
    borderWidth: 1,
    gap: trustSpacing.sm,
    padding: trustSpacing.lg,
  },
  check: {
    color: trustColors.TEXT,
    fontSize: 14,
    fontWeight: "800",
  },
  preview: {
    alignItems: "center",
    backgroundColor: trustColors.SOFT,
    borderRadius: 8,
    justifyContent: "center",
    minHeight: 160,
    padding: trustSpacing.lg,
  },
  routeText: {
    color: trustColors.NEUTRAL,
    fontSize: 16,
    fontWeight: "900",
    textAlign: "center",
  },
});
