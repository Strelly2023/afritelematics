import React from "react";
import { StyleSheet, Text, View } from "react-native";

import {
  assertLedgerReceiptEvidence,
  assertReceiptEvidence,
} from "../../core/models/evidenceGuards";
import type { LedgerReceiptSummary, RideReceipt } from "../../core/models/ride";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type ReceiptScreenProps = {
  receipt: RideReceipt;
  ledgerReceipt?: LedgerReceiptSummary;
};

export function ReceiptScreen({ receipt, ledgerReceipt }: ReceiptScreenProps) {
  assertReceiptEvidence(receipt);
  if (ledgerReceipt) {
    assertLedgerReceiptEvidence(ledgerReceipt);
  }

  return (
    <SurfacePanel>
      <Text style={styles.title}>Receipt</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Ride</Text>
        <Text style={styles.value}>{receipt.rideId}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Receipt</Text>
        <Text style={styles.value}>{receipt.receiptId}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Distance</Text>
        <Text style={styles.value}>{receipt.distanceText || "Provided by API"}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Total</Text>
        <Text style={styles.value}>{receipt.totalText || "Provided by API"}</Text>
      </View>
      {ledgerReceipt ? (
        <View style={styles.proofBox}>
          <Text style={styles.proofTitle}>Proof</Text>
          <Text style={styles.proofValue}>Verdict: {ledgerReceipt.verdict}</Text>
          <Text style={styles.proofValue}>Events: {ledgerReceipt.eventCount}</Text>
          <Text style={styles.proofValue}>Hash: {ledgerReceipt.hashMode}</Text>
          <Text style={styles.proofValue}>Signature: {ledgerReceipt.signatureMode}</Text>
          <Text style={styles.proofValue}>Receipt Hash: {ledgerReceipt.receiptHash}</Text>
        </View>
      ) : null}
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  row: {
    gap: spacing.xs,
  },
  proofBox: {
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  proofTitle: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "800",
  },
  proofValue: {
    color: colors.secondary,
    fontSize: 13,
    fontWeight: "700",
  },
  title: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: "800",
  },
  value: {
    color: colors.secondary,
    fontSize: 16,
    fontWeight: "700",
  },
});
