import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { trustColors, trustSpacing } from "../theme/trustTokens";

type MapPreviewCardProps = {
  routeText?: string;
  pickupConfirmed?: boolean;
  dropoffConfirmed?: boolean;
  gpsTraceAvailable?: boolean;
  progressPct?: number;
  statusLabel?: string;
  etaText?: string;
  liveLabel?: string;
};

export function MapPreviewCard({
  routeText = "Route verification pending",
  pickupConfirmed = true,
  dropoffConfirmed = true,
  gpsTraceAvailable = true,
  progressPct = 50,
  statusLabel = "Live route",
  etaText = "ETA pending",
  liveLabel = "GPS linked",
}: MapPreviewCardProps) {
  const clampedProgress = Math.max(0, Math.min(progressPct, 100));
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>{statusLabel}</Text>
        <Text style={styles.pill}>{liveLabel}</Text>
      </View>
      <View style={styles.preview}>
        <View style={styles.routeNodeRow}>
          <View style={styles.originNode} />
          <View style={styles.routeTrack}>
            <View style={[styles.routeProgress, { width: `${clampedProgress}%` }]} />
            <View style={[styles.driverDot, { left: `${Math.max(4, clampedProgress - 8)}%` }]} />
          </View>
          <View style={styles.destinationNode} />
        </View>
        <Text style={styles.routeText}>{routeText}</Text>
        <Text style={styles.etaText}>{etaText}</Text>
      </View>
      <View style={styles.checkRow}>
        <Text style={styles.check}>Pickup: {pickupConfirmed ? "Confirmed" : "Review"}</Text>
        <Text style={styles.check}>Drop-off: {dropoffConfirmed ? "Confirmed" : "Review"}</Text>
      </View>
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
  checkRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: trustSpacing.sm,
    justifyContent: "space-between",
  },
  check: {
    color: trustColors.TEXT,
    fontSize: 14,
    fontWeight: "800",
  },
  destinationNode: {
    backgroundColor: trustColors.HIGH,
    borderRadius: 999,
    height: 14,
    width: 14,
  },
  driverDot: {
    backgroundColor: trustColors.MEDIUM,
    borderRadius: 999,
    height: 12,
    position: "absolute",
    top: -1,
    width: 12,
  },
  etaText: {
    color: trustColors.HIGH,
    fontSize: 13,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  pill: {
    backgroundColor: trustColors.SOFT,
    borderRadius: 999,
    color: trustColors.NEUTRAL,
    fontSize: 11,
    fontWeight: "900",
    paddingHorizontal: 10,
    paddingVertical: 4,
    textTransform: "uppercase",
  },
  preview: {
    alignItems: "center",
    backgroundColor: trustColors.SOFT,
    borderRadius: 8,
    gap: trustSpacing.sm,
    justifyContent: "center",
    minHeight: 180,
    padding: trustSpacing.lg,
  },
  routeNodeRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: trustSpacing.sm,
    width: "100%",
  },
  routeProgress: {
    backgroundColor: trustColors.HIGH,
    borderRadius: 999,
    height: 6,
  },
  routeText: {
    color: trustColors.NEUTRAL,
    fontSize: 16,
    fontWeight: "900",
    textAlign: "center",
  },
  routeTrack: {
    backgroundColor: trustColors.BORDER,
    borderRadius: 999,
    flex: 1,
    height: 6,
    position: "relative",
  },
  originNode: {
    backgroundColor: trustColors.NEUTRAL,
    borderRadius: 999,
    height: 14,
    width: 14,
  },
  title: {
    color: trustColors.TEXT,
    fontSize: 14,
    fontWeight: "900",
  },
});
