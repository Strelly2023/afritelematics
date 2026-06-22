import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { trustColors, trustSpacing } from "../theme/trustTokens";

type PaymentVerificationCardProps = {
  amountText?: string;
  fareCalculated?: boolean;
  receiptIssued?: boolean;
  noDuplicateCharge?: boolean;
};

export function PaymentVerificationCard({
  amountText,
  fareCalculated = true,
  receiptIssued = true,
  noDuplicateCharge = true,
}: PaymentVerificationCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Payment Verified</Text>
      {amountText ? <Text style={styles.amount}>{amountText}</Text> : null}
      <Text style={styles.check}>Fare calculated: {fareCalculated ? "Verified" : "Review"}</Text>
      <Text style={styles.check}>Receipt issued: {receiptIssued ? "Verified" : "Review"}</Text>
      <Text style={styles.check}>Duplicate charge: {noDuplicateCharge ? "Clear" : "Review"}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  amount: {
    color: trustColors.NEUTRAL,
    fontSize: 22,
    fontWeight: "900",
  },
  card: {
    backgroundColor: trustColors.CARD,
    borderColor: trustColors.BORDER,
    borderRadius: 8,
    borderWidth: 1,
    gap: trustSpacing.sm,
    padding: trustSpacing.lg,
  },
  check: {
    color: trustColors.TEXT,
    fontSize: 14,
    fontWeight: "800",
  },
  title: {
    color: trustColors.TEXT,
    fontSize: 16,
    fontWeight: "900",
  },
});
