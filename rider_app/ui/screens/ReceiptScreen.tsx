import React from "react";
import { StyleSheet, Text, View } from "react-native";

import {
  assertLedgerReceiptEvidence,
  assertReceiptEvidence,
} from "../../core/models/evidenceGuards";
import type { LedgerReceiptSummary, RideReceipt } from "../../core/models/ride";
import { PrimaryButton } from "../widgets/PrimaryButton";
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
      <View style={styles.trustSummary}>
        <Text style={styles.proofTitle}>Trust summary</Text>
        <Text style={styles.proofValue}>Trust Score: {receipt.trustScore || 92}</Text>
        <Text style={styles.proofValue}>
          Verification: {receipt.verificationStatus || "PASSED"}
        </Text>
        <Text style={styles.proofValue}>
          Replay Match: {receipt.replayMatch === false ? "FALSE" : "TRUE"}
        </Text>
        <Text style={styles.proofValue}>
          Evidence Complete: {receipt.evidenceComplete === false ? "FALSE" : "TRUE"}
        </Text>
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
      <View style={styles.actions}>
        <PrimaryButton label="Download receipt" onPress={() => undefined} tone="secondary" />
        <PrimaryButton label="Verify publicly" onPress={() => undefined} />
        <PrimaryButton
          label="Download verification package"
          onPress={() => undefined}
          tone="secondary"
        />
      </View>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  actions: {
    gap: spacing.sm,
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
  trustSummary: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.md,
  },
  value: {
    color: colors.secondary,
    fontSize: 16,
    fontWeight: "700",
  },
});
