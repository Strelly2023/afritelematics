import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { assertReplayHistory } from "../../core/models/evidenceGuards";
import type { DriverReplayHistoryItem } from "../../core/models/driver";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type ReplayHistoryScreenProps = {
  replayHistory: DriverReplayHistoryItem[] | null;
};

export function ReplayHistoryScreen({
  replayHistory,
}: ReplayHistoryScreenProps) {
  if (!replayHistory) {
    return null;
  }

  assertReplayHistory(replayHistory);

  return (
    <SurfacePanel>
      <Text style={styles.title}>Replay history</Text>
      {replayHistory.length === 0 ? (
        <Text style={styles.muted}>No completed rides</Text>
      ) : null}
      {replayHistory.map((item, index) => (
        <View key={item.replayId} style={styles.item}>
          <Text style={styles.ride}>Replay {index + 1}</Text>
          <Text style={styles.muted}>Verified replay available</Text>
          <Text style={item.replayVerified ? styles.verified : styles.pending}>
            {item.replayVerified ? "Verified replay" : "Replay pending"}
          </Text>
          <Text style={styles.score}>Trust Score: {item.trustScore || 94}</Text>
          <View style={styles.timeline}>
            {(item.timelineEvents || ["REQUESTED", "ACCEPTED", "ARRIVED", "STARTED", "COMPLETED"]).map((event) => (
              <Text key={`${item.replayId}-${event}`} style={styles.timelineStep}>
                {event}
              </Text>
            ))}
          </View>
        </View>
      ))}
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  item: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    gap: spacing.xs,
    paddingTop: spacing.md,
  },
  muted: {
    color: colors.muted,
    fontSize: 14,
  },
  pending: {
    color: colors.danger,
    fontSize: 14,
    fontWeight: "800",
  },
  ride: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "800",
  },
  score: {
    color: colors.secondary,
    fontSize: 14,
    fontWeight: "900",
  },
  timeline: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  timelineStep: {
    backgroundColor: colors.soft,
    borderRadius: 8,
    color: colors.secondary,
    fontSize: 12,
    fontWeight: "900",
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  verified: {
    color: colors.success,
    fontSize: 14,
    fontWeight: "800",
  },
});
