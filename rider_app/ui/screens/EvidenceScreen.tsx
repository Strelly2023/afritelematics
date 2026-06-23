import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { LedgerReceiptSummary, RideReceipt, RideReplay } from "../../core/models/ride";
import { EvidenceSummaryCard } from "../widgets/EvidenceSummaryCard";
import { VerificationStatusCard } from "../widgets/VerificationStatusCard";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type EvidenceScreenProps = {
  receipt: RideReceipt | null;
  replay: RideReplay | null;
  ledgerReceipt?: LedgerReceiptSummary | null;
};

export function EvidenceScreen({
  receipt,
  replay,
  ledgerReceipt,
}: EvidenceScreenProps) {
  const eventCount = ledgerReceipt?.eventCount ?? 0;
  const receiptVerified = receipt?.verificationStatus !== "FAILED";
  const replayVerified = Boolean(replay?.replayVerified);

  return (
    <SurfacePanel>
      <Text style={styles.title}>Trip Evidence</Text>
      <EvidenceSummaryCard
        summary={
          receipt && replay
            ? "Trip evidence is available through verified receipt, payment, and replay checks."
            : "Evidence appears after a trip is completed and verified by the system."
        }
      />
      <VerificationStatusCard
        status={{
          receipt: Boolean(receipt) && receiptVerified,
          replay: replayVerified,
          payment: Boolean(receipt) && receiptVerified,
          gps_trace: replayVerified,
        }}
      />
      <View style={styles.row}>
        <Text style={styles.label}>Events verified</Text>
        <Text style={styles.value}>{eventCount}</Text>
      </View>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  row: {
    alignItems: "center",
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: spacing.md,
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  value: {
    color: colors.secondary,
    fontSize: 18,
    fontWeight: "900",
  },
});
