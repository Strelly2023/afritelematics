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
      <Text style={styles.source}>Source: {earnings.source}</Text>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.muted,
    fontSize: 14,
    fontWeight: "700",
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
