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

  return (
    <SurfacePanel>
      <Text style={styles.title}>Replay</Text>
      <Text style={styles.verified}>
        {replay.replayVerified ? "Verified replay" : "Replay pending"}
      </Text>
      {replay.routeSummary ? (
        <Text style={styles.summary}>{replay.routeSummary}</Text>
      ) : null}
      {replay.explanationSteps.map((step, index) => (
        <View key={`${replay.replayId}-${index}`} style={styles.step}>
          <Text style={styles.stepNumber}>{index + 1}</Text>
          <Text style={styles.stepText}>{step}</Text>
        </View>
      ))}
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  step: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.sm,
  },
  stepNumber: {
    color: colors.primary,
    fontWeight: "800",
    width: 24,
  },
  stepText: {
    color: colors.secondary,
    flex: 1,
    fontSize: 15,
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
