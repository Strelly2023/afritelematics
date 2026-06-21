import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { DriverAvailability, EarningsSummary } from "../../core/models/driver";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type DriverTrustProfileScreenProps = {
  availability: DriverAvailability | null;
  earnings: EarningsSummary | null;
};

export function DriverTrustProfileScreen({
  availability,
  earnings,
}: DriverTrustProfileScreenProps) {
  const trustScore = earnings?.trustScore || availability?.trustScore || 94;
  const verifiedRides = availability?.verifiedRides || earnings?.verifiedRideCount || 0;
  const replayConsistency = availability?.replayConsistencyPct || 100;

  return (
    <SurfacePanel>
      <View style={styles.header}>
        <Text style={styles.title}>Driver trust profile</Text>
        <Text style={styles.status}>Trusted driver</Text>
      </View>
      <View style={styles.metrics}>
        <Metric label="Trust score" value={trustScore} />
        <Metric label="Verified rides" value={verifiedRides} />
        <Metric label="Replay consistency" value={`${replayConsistency}%`} />
      </View>
    </SurfacePanel>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    gap: spacing.xs,
  },
  metric: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  metricLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  metricValue: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  metrics: {
    gap: spacing.sm,
  },
  status: {
    color: colors.success,
    fontSize: 15,
    fontWeight: "900",
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
});
