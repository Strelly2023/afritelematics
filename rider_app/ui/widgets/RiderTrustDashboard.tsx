import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { trustColors, trustSpacing } from "../theme/trustTokens";
import { TrustScoreCard } from "./TrustScoreCard";

type RiderTrustDashboardProps = {
  trips: number;
  verifiedTrips: number;
  replaySuccessPct: number;
  safetyStatus?: string;
  trustScore: number;
};

export function RiderTrustDashboard({
  trips,
  verifiedTrips,
  replaySuccessPct,
  safetyStatus = "Good",
  trustScore,
}: RiderTrustDashboardProps) {
  return (
    <View style={styles.stack}>
      <TrustScoreCard
        score={trustScore}
        checks={["Trips", "Payments", "Replay"]}
        title="Your Trust Profile"
      />
      <View style={styles.card}>
        <Metric label="Trips" value={trips} />
        <Metric label="Verified trips" value={verifiedTrips} />
        <Metric label="Replay success" value={`${replaySuccessPct}%`} />
        <Metric label="Safety status" value={safetyStatus} />
      </View>
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
  stack: {
    gap: trustSpacing.md,
  },
});
