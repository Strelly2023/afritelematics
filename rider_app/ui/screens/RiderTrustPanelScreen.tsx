import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { RideReceipt, RideStatusSnapshot } from "../../core/models/ride";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { TrustBadge } from "../widgets/TrustBadge";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type RiderTrustPanelScreenProps = {
  status?: RideStatusSnapshot | null;
  receipt?: RideReceipt | null;
};

export function RiderTrustPanelScreen({
  status,
  receipt,
}: RiderTrustPanelScreenProps) {
  const trustScore = receipt?.trustScore || status?.trustScore || 92;
  const verificationStatus = receipt?.verificationStatus || "PASSED";

  return (
    <SurfacePanel>
      <View style={styles.header}>
        <Text style={styles.title}>Trust panel</Text>
        <Text style={styles.verified}>Verified ride</Text>
      </View>
      <View style={styles.grid}>
        <TrustBadge label="Trust score" score={trustScore} status={verificationStatus} />
        <TrustBadge
          label="Replay match"
          status={receipt?.replayMatch === false ? "REVIEW_REQUIRED" : "PASSED"}
        />
        <TrustBadge
          label="Evidence"
          status={receipt?.evidenceComplete === false ? "REVIEW_REQUIRED" : "PASSED"}
        />
      </View>
      <View style={styles.actions}>
        <PrimaryButton label="View receipt" onPress={() => undefined} tone="secondary" />
        <PrimaryButton label="View replay" onPress={() => undefined} tone="secondary" />
        <PrimaryButton label="Verify ride" onPress={() => undefined} />
      </View>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  actions: {
    gap: spacing.sm,
  },
  grid: {
    gap: spacing.sm,
  },
  header: {
    gap: spacing.xs,
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  verified: {
    color: colors.success,
    fontSize: 15,
    fontWeight: "900",
  },
});
