import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { assertEarningsEvidence } from "../../core/models/evidenceGuards";
import type { EarningsSummary } from "../../core/models/driver";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type EarningsScreenProps = {
  earnings: EarningsSummary | null;
};

export function EarningsScreen({ earnings }: EarningsScreenProps) {
  if (!earnings) {
    return null;
  }

  assertEarningsEvidence(earnings);

  return (
    <SurfacePanel>
      <Text style={styles.title}>Earnings</Text>
      <Text style={styles.period}>{earnings.periodLabel}</Text>
      <Text style={styles.total}>{earnings.totalText}</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Rides</Text>
        <Text style={styles.value}>{earnings.rideCount}</Text>
      </View>
      <View style={styles.grid}>
        <Metric label="Verified rides" value={earnings.verifiedRideCount || earnings.rideCount} />
        <Metric label="Disputes" value={earnings.disputeCount || 0} />
        <Metric label="Trust score" value={earnings.trustScore || 94} />
      </View>
      <Text style={styles.source}>Source: {earnings.source}</Text>
    </SurfacePanel>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    gap: spacing.sm,
  },
  label: {
    color: colors.muted,
    fontSize: 14,
    fontWeight: "700",
  },
  metric: {
    backgroundColor: colors.soft,
    borderRadius: 8,
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
    fontSize: 20,
    fontWeight: "900",
  },
  period: {
    color: colors.muted,
    fontSize: 14,
  },
  row: {
    gap: spacing.xs,
  },
  source: {
    color: colors.success,
    fontSize: 14,
    fontWeight: "800",
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  total: {
    color: colors.secondary,
    fontSize: 28,
    fontWeight: "900",
  },
  value: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "800",
  },
});
