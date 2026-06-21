import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { assertReplayEvidence } from "../../core/models/evidenceGuards";
import type { RideReplay } from "../../core/models/ride";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type ReplayScreenProps = {
  replay: RideReplay;
};

export function ReplayScreen({ replay }: ReplayScreenProps) {
  assertReplayEvidence(replay);
  const timelineEvents =
    replay.timelineEvents ||
    (["REQUESTED", "DRIVER_ACCEPTED", "ARRIVED", "STARTED", "COMPLETED"] as const).map(
      (label) => ({ label, verified: replay.replayVerified }),
    );

  return (
    <SurfacePanel>
      <Text style={styles.title}>Replay timeline</Text>
      <Text style={styles.verified}>
        {replay.replayVerified ? "Verified replay" : "Replay pending"}
      </Text>
      {replay.routeSummary ? (
        <Text style={styles.summary}>{replay.routeSummary}</Text>
      ) : null}
      {timelineEvents.map((event, index) => (
        <View key={`${replay.replayId}-${event.label}`} style={styles.step}>
          <Text style={event.verified ? styles.dotVerified : styles.dotPending}>
            {event.verified ? "●" : "○"}
          </Text>
          <View style={styles.stepBody}>
            <Text style={styles.stepText}>{event.label}</Text>
            <Text style={styles.stepDetail}>
              {replay.explanationSteps[index] || "Trace event verified by replay."}
            </Text>
          </View>
        </View>
      ))}
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  dotPending: {
    color: colors.muted,
    fontSize: 18,
    fontWeight: "900",
    width: 24,
  },
  dotVerified: {
    color: colors.success,
    fontSize: 18,
    fontWeight: "900",
    width: 24,
  },
  step: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.sm,
  },
  stepBody: {
    flex: 1,
    gap: spacing.xs,
  },
  stepDetail: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
  },
  stepText: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "900",
  },
  summary: {
    color: colors.secondary,
    fontSize: 15,
  },
  title: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: "800",
  },
  verified: {
    color: colors.success,
    fontSize: 15,
    fontWeight: "800",
  },
});
