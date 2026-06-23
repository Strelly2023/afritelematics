import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { RiderTrustDashboard } from "../widgets/RiderTrustDashboard";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type RiderProfileScreenProps = {
  name: string;
  email: string;
  trips: number;
  verifiedTrips: number;
  replaySuccessPct: number;
  trustScore: number;
};

export function RiderProfileScreen({
  name,
  email,
  trips,
  verifiedTrips,
  replaySuccessPct,
  trustScore,
}: RiderProfileScreenProps) {
  return (
    <SurfacePanel>
      <RiderTrustDashboard
        trips={trips}
        verifiedTrips={verifiedTrips}
        replaySuccessPct={replaySuccessPct}
        trustScore={trustScore}
      />
      <View style={styles.identity}>
        <Text style={styles.title}>Profile</Text>
        <Text style={styles.value}>{name}</Text>
        <Text style={styles.muted}>{email}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Payment</Text>
        <Text style={styles.status}>Verified</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Safety status</Text>
        <Text style={styles.status}>Good</Text>
      </View>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  identity: {
    gap: spacing.xs,
  },
  label: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  muted: {
    color: colors.muted,
    fontSize: 14,
  },
  row: {
    alignItems: "center",
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: spacing.md,
  },
  status: {
    color: colors.success,
    fontSize: 14,
    fontWeight: "900",
  },
  title: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: "900",
  },
  value: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: "900",
  },
});
