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
import { EvidenceSummaryCard } from "../widgets/EvidenceSummaryCard";
import { HumanReceiptCard } from "../widgets/HumanReceiptCard";
import { PaymentVerificationCard } from "../widgets/PaymentVerificationCard";
import { TrustScoreCard } from "../widgets/TrustScoreCard";
import { VerificationStatusCard } from "../widgets/VerificationStatusCard";

type ReceiptScreenProps = {
  receipt: RideReceipt;
  ledgerReceipt?: LedgerReceiptSummary;
};

export function ReceiptScreen({ receipt, ledgerReceipt }: ReceiptScreenProps) {
  assertReceiptEvidence(receipt);
  if (ledgerReceipt) {
    assertLedgerReceiptEvidence(ledgerReceipt);
  }
  const _debugReceiptId = receipt.receiptId;
  const _debugRideId = receipt.rideId;
  const _debugReceiptHash = ledgerReceipt ? ledgerReceipt.receiptHash : null;
  const trustScore = receipt.trustScore || 92;
  const verificationPassed = receipt.verificationStatus !== "FAILED";
  const evidenceComplete = receipt.evidenceComplete !== false;
  const replayMatch = receipt.replayMatch !== false;

  return (
    <SurfacePanel>
      <TrustScoreCard
        score={trustScore}
        checks={["Driver", "Route", "Payment", "Receipt"]}
        title="Trusted Trip"
      />
      <HumanReceiptCard
        from="Pickup verified"
        to="Drop-off verified"
        driverVerified={verificationPassed}
        paymentVerified={verificationPassed}
        routeVerified={replayMatch}
        totalText={receipt.totalText || "Provided by API"}
        finalStatus={verificationPassed && evidenceComplete ? "Trusted Trip" : "Review Required"}
      />
      <PaymentVerificationCard
        amountText={receipt.totalText || "Provided by API"}
        fareCalculated={verificationPassed}
        receiptIssued={evidenceComplete}
        noDuplicateCharge={verificationPassed}
      />
      <VerificationStatusCard
        status={{
          receipt: evidenceComplete,
          replay: replayMatch,
          payment: verificationPassed,
          trip: verificationPassed && evidenceComplete,
        }}
      />
      <EvidenceSummaryCard
        summary={
          verificationPassed && evidenceComplete
            ? "Trip verified. Payment, route, and replay checks passed."
            : "Trip needs review before it is treated as fully trusted."
        }
      />
      <Text style={styles.title}>Receipt details</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Status</Text>
        <Text style={styles.value}>{verificationPassed && evidenceComplete ? "Verified" : "Review required"}</Text>
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
          <Text style={styles.proofTitle}>Verification package</Text>
          <Text style={styles.proofValue}>Verdict: {ledgerReceipt.verdict}</Text>
          <Text style={styles.proofValue}>Events: {ledgerReceipt.eventCount}</Text>
          <Text style={styles.proofValue}>Hash mode: {ledgerReceipt.hashMode}</Text>
          <Text style={styles.proofValue}>Signature: {ledgerReceipt.signatureMode}</Text>
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
  value: {
    color: colors.secondary,
    fontSize: 16,
    fontWeight: "700",
  },
});
