import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { trustColors, trustLevelColor, trustLevelLabel, trustSpacing } from "../theme/trustTokens";

type TrustScoreCardProps = {
  score: number;
  checks: string[];
  title?: string;
};

export function TrustScoreCard({ score, checks, title = "Trust Score" }: TrustScoreCardProps) {
  const color = trustLevelColor(score);

  return (
    <View style={[styles.card, { borderColor: color }]}>
      <View style={styles.header}>
        <Text style={styles.title}>{title}</Text>
        <Text style={[styles.level, { color }]}>{trustLevelLabel(score)}</Text>
      </View>
      <Text style={[styles.score, { color }]}>{score}/100</Text>
      <View style={styles.checks}>
        {checks.map((item) => (
          <Text key={item} style={styles.check}>
            Verified: {item}
          </Text>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: trustColors.CARD,
    borderRadius: 8,
    borderWidth: 1,
    gap: trustSpacing.md,
    padding: trustSpacing.lg,
  },
  check: {
    color: trustColors.TEXT,
    fontSize: 14,
    fontWeight: "700",
  },
  checks: {
    gap: trustSpacing.xs,
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  level: {
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  score: {
    fontSize: 34,
    fontWeight: "900",
  },
  title: {
    color: trustColors.TEXT,
    fontSize: 14,
    fontWeight: "900",
    textTransform: "uppercase",
  },
});
