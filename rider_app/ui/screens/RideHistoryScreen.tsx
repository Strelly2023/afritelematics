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
      {history.map((ride, index) => (
        <View key={ride.rideId} style={styles.row}>
          <View style={styles.route}>
            <Text style={styles.ride}>Trip {index + 1}</Text>
            <Text style={styles.muted}>{humanStatus(ride.status)}</Text>
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

function humanStatus(status: RideHistoryItem["status"]): string {
  switch (status) {
    case "requested":
      return "Ride requested";
    case "confirmed":
    case "waiting_for_driver":
    case "driver_assigned":
    case "matched":
      return "Driver matched";
    case "arriving":
      return "Driver arriving";
    case "arrived":
      return "Driver arrived";
    case "in_progress":
      return "Trip in progress";
    case "completed":
      return "Trip completed";
    case "cancelled":
      return "Ride cancelled";
  }
}
