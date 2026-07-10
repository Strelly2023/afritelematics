import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { MapPreviewCard } from "../widgets/MapPreviewCard";
import type { DiagnosticsSnapshot } from "../../core/models/pilotEvidence";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";
import type { ConnectivityCheck } from "../../core/api/client";

type DiagnosticsScreenProps = {
  diagnostics: DiagnosticsSnapshot;
  loading: boolean;
  onStartShift: () => void;
  apiBaseUrl: string;
  connectionChecks: ConnectivityCheck[];
  checkingConnection: boolean;
  onTestConnection: () => void;
};

export function DiagnosticsScreen({
  diagnostics,
  loading,
  onStartShift,
  apiBaseUrl,
  connectionChecks,
  checkingConnection,
  onTestConnection,
}: DiagnosticsScreenProps) {
  return (
    <SurfacePanel>
      <View style={styles.header}>
        <Text style={styles.title}>Live diagnostics</Text>
        <Text style={diagnostics.shiftStarted ? styles.online : styles.pending}>
          {diagnostics.shiftStarted ? "Shift evidence active" : "Shift not started"}
        </Text>
      </View>

      <MapPreviewCard
        routeText={
          diagnostics.lastLocation
            ? `${diagnostics.lastLocation.latitude.toFixed(4)}, ${diagnostics.lastLocation.longitude.toFixed(4)}`
            : "Location awaiting first GPS fix"
        }
        progressPct={diagnostics.locationSamples > 0 ? 66 : 12}
        statusLabel={diagnostics.shiftStarted ? "GPS evidence" : "Shift pending"}
        etaText={diagnostics.shiftStarted ? "Live driver telemetry" : "Start shift to activate"}
        liveLabel={diagnostics.shiftStarted ? "Tracking" : "Idle"}
        pickupConfirmed={diagnostics.locationSamples > 0}
        dropoffConfirmed={diagnostics.shiftStarted}
        gpsTraceAvailable={diagnostics.locationSamples > 0}
      />

      <PrimaryButton
        label="Start evidence shift"
        onPress={onStartShift}
        disabled={loading || diagnostics.shiftStarted}
      />

      <View style={styles.connectionPanel}>
        <View style={styles.header}>
          <Text style={styles.panelTitle}>API connectivity</Text>
          <Text style={styles.muted}>{apiBaseUrl}</Text>
        </View>
        <PrimaryButton
          label={checkingConnection ? "Testing connection..." : "Test Connection"}
          onPress={onTestConnection}
          disabled={checkingConnection}
        />
        {connectionChecks.length === 0 ? (
          <Text style={styles.muted}>
            Run a connection test to verify API host, TLS policy, and health endpoint reachability.
          </Text>
        ) : (
          <View style={styles.connectionGrid}>
            {connectionChecks.map((check) => (
              <View
                key={check.label}
                style={[
                  styles.connectionCheck,
                  check.status === "pass" ? styles.connectionPass : styles.connectionFail,
                ]}
              >
                <Text style={styles.connectionLabel}>{check.label}</Text>
                <Text style={check.status === "pass" ? styles.online : styles.error}>
                  {check.status.toUpperCase()}
                </Text>
                <Text style={styles.muted}>{check.detail}</Text>
              </View>
            ))}
          </View>
        )}
      </View>

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

      {diagnostics.shiftStarted &&
      diagnostics.locationSamples === 0 &&
      diagnostics.gpsSignalLossEvents > 0 ? (
        <Text style={styles.warning}>
          GPS evidence unavailable in this runtime. Rebuild the native driver app or use
          Expo Go with location support before production readiness can pass.
        </Text>
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
  connectionCheck: {
    borderRadius: 8,
    borderWidth: 1,
    gap: 4,
    minWidth: 150,
    padding: spacing.md,
  },
  connectionFail: {
    backgroundColor: "#fff1f1",
    borderColor: "#e8a4a4",
  },
  connectionGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  connectionLabel: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: "900",
  },
  connectionPanel: {
    backgroundColor: colors.soft,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.md,
  },
  connectionPass: {
    backgroundColor: "#eef7f3",
    borderColor: "#b7e3cc",
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
  panelTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "900",
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  warning: {
    color: colors.secondary,
    fontSize: 14,
    fontWeight: "800",
    lineHeight: 20,
  },
});
