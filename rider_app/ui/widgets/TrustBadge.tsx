import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type TrustBadgeProps = {
  label: string;
  score?: number;
  status?: "PASSED" | "REVIEW_REQUIRED" | "FAILED";
};

export function TrustBadge({ label, score, status = "PASSED" }: TrustBadgeProps) {
  const isPassed = status === "PASSED";

  return (
    <View style={[styles.badge, isPassed ? styles.passed : styles.review]}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>
        {typeof score === "number" ? score : isPassed ? "Verified" : "Review"}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: 8,
    gap: spacing.xs,
    padding: spacing.md,
  },
  label: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  passed: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderWidth: 1,
  },
  review: {
    backgroundColor: "#fff4e6",
    borderColor: "#ffd7a8",
    borderWidth: 1,
  },
  value: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "900",
  },
});
