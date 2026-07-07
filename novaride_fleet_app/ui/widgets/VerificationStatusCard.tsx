import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { trustColors, trustSpacing } from "../theme/trustTokens";

type VerificationStatusCardProps = {
  status: Record<string, boolean>;
  title?: string;
};

function labelFromKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function VerificationStatusCard({ status, title = "Verification Status" }: VerificationStatusCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      {Object.entries(status).map(([key, value]) => (
        <View key={key} style={styles.row}>
          <Text style={styles.label}>{labelFromKey(key)}</Text>
          <Text style={[styles.value, value ? styles.verified : styles.review]}>
            {value ? "Verified" : "Review"}
          </Text>
        </View>
      ))}
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
  label: {
    color: trustColors.TEXT,
    fontSize: 14,
    fontWeight: "800",
  },
  review: {
    color: trustColors.MEDIUM,
  },
  row: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  title: {
    color: trustColors.TEXT,
    fontSize: 16,
    fontWeight: "900",
  },
  value: {
    fontSize: 13,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  verified: {
    color: trustColors.HIGH,
  },
});
