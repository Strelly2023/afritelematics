import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { trustColors, trustSpacing } from "../theme/trustTokens";

type EvidenceSummaryCardProps = {
  summary: string;
  title?: string;
};

export function EvidenceSummaryCard({
  summary,
  title = "Why this is trusted",
}: EvidenceSummaryCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.summary}>{summary}</Text>
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
  summary: {
    color: trustColors.MUTED,
    fontSize: 14,
    fontWeight: "600",
    lineHeight: 20,
  },
  title: {
    color: trustColors.TEXT,
    fontSize: 16,
    fontWeight: "900",
  },
});
