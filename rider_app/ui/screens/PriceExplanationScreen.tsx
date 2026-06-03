import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { assertPriceEvidence } from "../../core/models/evidenceGuards";
import type { PriceExplanation } from "../../core/models/ride";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type PriceExplanationScreenProps = {
  explanation: PriceExplanation;
};

export function PriceExplanationScreen({
  explanation,
}: PriceExplanationScreenProps) {
  assertPriceEvidence(explanation);

  return (
    <SurfacePanel>
      <Text style={styles.title}>Price explanation</Text>
      <Text style={styles.source}>Source: {explanation.source}</Text>
      <Text style={styles.body}>{explanation.priceExplanation}</Text>
      {explanation.lineItems?.map((item) => (
        <View key={item.label} style={styles.item}>
          <Text style={styles.itemLabel}>{item.label}</Text>
          <Text style={styles.amount}>{item.amountText}</Text>
        </View>
      ))}
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  amount: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "800",
  },
  body: {
    color: colors.secondary,
    fontSize: 15,
    lineHeight: 21,
  },
  item: {
    alignItems: "center",
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: spacing.md,
  },
  itemLabel: {
    color: colors.secondary,
    flex: 1,
    fontSize: 15,
    fontWeight: "700",
  },
  source: {
    color: colors.success,
    fontSize: 14,
    fontWeight: "800",
  },
  title: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: "800",
  },
});
