import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { RideHistoryItem } from "../../core/models/ride";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type RideHistoryScreenProps = {
  history: RideHistoryItem[];
};

export function RideHistoryScreen({ history }: RideHistoryScreenProps) {
  return (
    <SurfacePanel>
      <Text style={styles.title}>Ride history</Text>
      {history.length === 0 ? <Text style={styles.muted}>No rides yet</Text> : null}
      {history.map((ride) => (
        <View key={ride.rideId} style={styles.row}>
          <View style={styles.route}>
            <Text style={styles.ride}>{ride.rideId}</Text>
            <Text style={styles.muted}>{ride.status}</Text>
          </View>
          <Text
            style={
              ride.verificationStatus === "REVIEW_REQUIRED"
                ? styles.review
                : styles.verified
            }
          >
            {ride.verificationStatus === "REVIEW_REQUIRED" ? "Review" : "OK"}
          </Text>
          <Text style={styles.score}>{ride.trustScore || 92}</Text>
        </View>
      ))}
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  muted: {
    color: colors.muted,
    fontSize: 13,
  },
  review: {
    color: colors.amber,
    fontSize: 14,
    fontWeight: "900",
  },
  ride: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "900",
  },
  route: {
    flex: 1,
    gap: spacing.xs,
  },
  row: {
    alignItems: "center",
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: "row",
    gap: spacing.md,
    paddingTop: spacing.md,
  },
  score: {
    color: colors.secondary,
    fontSize: 18,
    fontWeight: "900",
    minWidth: 36,
    textAlign: "right",
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  verified: {
    color: colors.success,
    fontSize: 14,
    fontWeight: "900",
  },
});
