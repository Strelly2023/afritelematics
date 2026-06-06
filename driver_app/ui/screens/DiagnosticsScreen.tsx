import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { DiagnosticsSnapshot } from "../../core/models/pilotEvidence";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type DiagnosticsScreenProps = {
  diagnostics: DiagnosticsSnapshot;
  loading: boolean;
  onStartShift: () => void;
};

export function DiagnosticsScreen({
  diagnostics,
  loading,
  onStartShift,
}: DiagnosticsScreenProps) {
  return (
    <SurfacePanel>
      <View style={styles.header}>
        <Text style={styles.title}>Live diagnostics</Text>
        <Text style={diagnostics.shiftStarted ? styles.online : styles.pending}>
          {diagnostics.shiftStarted ? "Shift evidence active" : "Shift not started"}
        </Text>
      </View>

      <PrimaryButton
        label="Start evidence shift"
        onPress={onStartShift}
        disabled={loading || diagnostics.shiftStarted}
      />

      <View style={styles.grid}>
        <Metric label="Location samples" value={diagnostics.locationSamples} />
        <Metric label="Network samples" value={diagnostics.networkSamples} />
        <Metric label="Evidence sent" value={diagnostics.evidenceSubmitted} />
        <Metric label="Evidence failed" value={diagnostics.evidenceFailed} />
        <Metric label="Route deviations" value={diagnostics.routeDeviationEvents} />
        <Metric label="GPS signal loss" value={diagnostics.gpsSignalLossEvents} />
      </View>

      {diagnostics.lastEvidenceType ? (
        <Text style={styles.muted}>
          Last evidence: {diagnostics.lastEvidenceType}
        </Text>
      ) : null}

      {diagnostics.lastLocation ? (
        <Text style={styles.muted}>
          GPS: {diagnostics.lastLocation.latitude.toFixed(5)},{" "}
          {diagnostics.lastLocation.longitude.toFixed(5)}
        </Text>
      ) : null}

      {typeof diagnostics.lastGpsAccuracyM === "number" ? (
        <Text style={styles.muted}>
          Accuracy: {Math.round(diagnostics.lastGpsAccuracyM)}m
        </Text>
      ) : null}

      {typeof diagnostics.lastSpeedKph === "number" ? (
        <Text style={styles.muted}>
          Speed estimate: {Math.round(diagnostics.lastSpeedKph)} km/h
        </Text>
      ) : null}

      {diagnostics.lastError ? (
        <Text style={styles.error}>Evidence error: {diagnostics.lastError}</Text>
      ) : null}
    </SurfacePanel>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  error: {
    color: colors.danger,
    fontSize: 14,
    fontWeight: "800",
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  header: {
    gap: spacing.xs,
  },
  metric: {
    backgroundColor: colors.soft,
    borderRadius: 8,
    minWidth: 130,
    padding: spacing.md,
  },
  metricLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  metricValue: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  muted: {
    color: colors.muted,
    fontSize: 14,
  },
  online: {
    color: colors.success,
    fontSize: 14,
    fontWeight: "900",
  },
  pending: {
    color: colors.secondary,
    fontSize: 14,
    fontWeight: "900",
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
});
