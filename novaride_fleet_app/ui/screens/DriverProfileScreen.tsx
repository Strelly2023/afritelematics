import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { DriverAvailability, EarningsSummary } from "../../core/models/driver";
import { DriverReputationCard } from "../widgets/DriverReputationCard";
import { TrustScoreCard } from "../widgets/TrustScoreCard";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type DriverProfileScreenProps = {
  name: string;
  email: string;
  availability: DriverAvailability | null;
  earnings: EarningsSummary | null;
};

export function DriverProfileScreen({
  name,
  email,
  availability,
  earnings,
}: DriverProfileScreenProps) {
  const trustScore = earnings?.trustScore || availability?.trustScore || 94;
  const verifiedRides = availability?.verifiedRides || earnings?.verifiedRideCount || 0;
  const disputes = earnings?.disputeCount || 0;

  return (
    <SurfacePanel>
      <TrustScoreCard
        score={trustScore}
        checks={["Profile", "Trips", "Payments"]}
        title="Driver Account"
      />
      <View style={styles.identity}>
        <Text style={styles.title}>Profile</Text>
        <Text style={styles.value}>{name}</Text>
        <Text style={styles.muted}>{email}</Text>
      </View>
      <DriverReputationCard
        trips={earnings?.rideCount || verifiedRides}
        replaySuccessPct={availability?.replayConsistencyPct || 100}
        disputes={disputes}
      />
      <View style={styles.row}>
        <Text style={styles.label}>Availability</Text>
        <Text style={styles.status}>{availability?.status || "offline"}</Text>
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
    textTransform: "capitalize",
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
