import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { trustColors, trustSpacing } from "../theme/trustTokens";

type HumanReceiptCardProps = {
  from: string;
  to: string;
  driverVerified?: boolean;
  paymentVerified?: boolean;
  routeVerified?: boolean;
  finalStatus?: string;
  totalText?: string;
};

export function HumanReceiptCard({
  from,
  to,
  driverVerified = true,
  paymentVerified = true,
  routeVerified = true,
  finalStatus = "Trusted Trip",
  totalText,
}: HumanReceiptCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Trip Summary</Text>
      <Text style={styles.line}>From: {from}</Text>
      <Text style={styles.line}>To: {to}</Text>
      {totalText ? <Text style={styles.line}>Total: {totalText}</Text> : null}
      <View style={styles.checks}>
        <Text style={styles.check}>Driver: {driverVerified ? "Verified" : "Review"}</Text>
        <Text style={styles.check}>Payment: {paymentVerified ? "Verified" : "Review"}</Text>
        <Text style={styles.check}>Route: {routeVerified ? "Verified" : "Review"}</Text>
      </View>
      <Text style={styles.status}>{finalStatus}</Text>
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
  check: {
    color: trustColors.TEXT,
    fontSize: 14,
    fontWeight: "800",
  },
  checks: {
    gap: trustSpacing.xs,
    paddingTop: trustSpacing.xs,
  },
  line: {
    color: trustColors.MUTED,
    fontSize: 15,
    fontWeight: "700",
  },
  status: {
    color: trustColors.HIGH,
    fontSize: 17,
    fontWeight: "900",
  },
  title: {
    color: trustColors.TEXT,
    fontSize: 16,
    fontWeight: "900",
  },
});
