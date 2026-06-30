import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { RideReplay } from "../../core/models/ride";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";
import { EvidenceSummaryCard } from "../widgets/EvidenceSummaryCard";
import { LifecycleTimeline, type LifecycleStep } from "../widgets/LifecycleTimeline";
import { MapPreviewCard } from "../widgets/MapPreviewCard";
import { TrustScoreCard } from "../widgets/TrustScoreCard";

type ReplayScreenProps = {
  replay: RideReplay;
};

export function ReplayScreen({ replay }: ReplayScreenProps) {
  const replayReady = Boolean(replay?.rideId && replay.replayId);
  const replayVerified = replayReady && replay.replayVerified === true;
  const timelineEvents =
    replay.timelineEvents ||
    (["REQUESTED", "DRIVER_ACCEPTED", "DRIVER_MATCHED", "ARRIVING", "ARRIVED", "STARTED", "COMPLETED"] as const).map(
      (label) => ({ label, verified: replayVerified }),
    );

  return (
    <SurfacePanel>
      <TrustScoreCard
        score={replayVerified ? 96 : 58}
        checks={["Route", "Timeline", "Receipt"]}
        title="Replay Verification"
      />
      <MapPreviewCard
        routeText={replay.routeSummary || "Route verification available after replay"}
        pickupConfirmed={replayVerified}
        dropoffConfirmed={replayVerified}
        gpsTraceAvailable={replayVerified}
      />
      <LifecycleTimeline steps={buildReplayTimeline(timelineEvents)} />
      <EvidenceSummaryCard
        summary={
          replayVerified
            ? "This trip replay matches the verified route and lifecycle events."
            : "Replay is still pending and should be reviewed before final trust is confirmed."
        }
      />
      <Text style={styles.title}>Replay details</Text>
      <Text style={styles.verified}>
        {replayVerified ? "Verified replay" : "Replay pending"}
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

function buildReplayTimeline(
  timelineEvents: Array<{ label: string; verified: boolean }>,
): LifecycleStep[] {
  return timelineEvents.map((event) => ({
    label: humanReplayLabel(event.label),
    completed: event.verified,
    current: !event.verified,
  }));
}

function humanReplayLabel(label: string): string {
  switch (label) {
    case "DRIVER_ACCEPTED":
      return "Accepted";
    case "DRIVER_MATCHED":
      return "Matched";
    case "ARRIVING":
      return "Arriving";
    case "ARRIVED":
      return "Arrived";
    default:
      return label.charAt(0) + label.slice(1).toLowerCase();
  }
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
