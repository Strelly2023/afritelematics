import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { RideHistoryItem } from "../../core/models/ride";
import { RiderNotificationsScreen } from "./RiderNotificationsScreen";
import { RideHistoryScreen } from "./RideHistoryScreen";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type ActivityScreenProps = {
  history: RideHistoryItem[];
  notifications: Array<{ id: string; title: string; detail: string; tone?: "success" | "info" | "review" }>;
};

export function ActivityScreen({ history, notifications }: ActivityScreenProps) {
  return (
    <View style={styles.stack}>
      <SurfacePanel>
        <Text style={styles.title}>Activity</Text>
        <Text style={styles.subtitle}>Trips, confirmations, and delivery updates.</Text>
      </SurfacePanel>
      <RideHistoryScreen history={history} />
      <RiderNotificationsScreen notifications={notifications} />
    </View>
  );
}

const styles = StyleSheet.create({
  stack: {
    gap: spacing.md,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 14,
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
});
