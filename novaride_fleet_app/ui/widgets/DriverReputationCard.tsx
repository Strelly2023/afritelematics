import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { trustColors, trustSpacing } from "../theme/trustTokens";

type DriverReputationCardProps = {
  trips: number;
  replaySuccessPct: number;
  disputes: number;
  trustLevel?: string;
};

export function DriverReputationCard({
  trips,
  replaySuccessPct,
  disputes,
  trustLevel = "High",
}: DriverReputationCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Driver Reputation</Text>
      <Metric label="Trips" value={trips} />
      <Metric label="Replay success" value={`${replaySuccessPct}%`} />
      <Metric label="Disputes" value={disputes} />
      <Metric label="Trust level" value={trustLevel} />
    </View>
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
  card: {
    backgroundColor: trustColors.CARD,
    borderColor: trustColors.BORDER,
    borderRadius: 8,
    borderWidth: 1,
    gap: trustSpacing.sm,
    padding: trustSpacing.lg,
  },
  metric: {
    gap: trustSpacing.xs,
  },
  metricLabel: {
    color: trustColors.MUTED,
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  metricValue: {
    color: trustColors.TEXT,
    fontSize: 18,
    fontWeight: "900",
  },
  title: {
    color: trustColors.TEXT,
    fontSize: 16,
    fontWeight: "900",
  },
});
