import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { OperatorDashboard } from "../../core/models/operator";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type OperatorDashboardScreenProps = {
  dashboard: OperatorDashboard | null;
  loading: boolean;
  error: string;
  onRefresh: () => void;
};

export function OperatorDashboardScreen({
  dashboard,
  loading,
  error,
  onRefresh,
}: OperatorDashboardScreenProps) {
  return (
    <SurfacePanel>
      <View style={styles.header}>
        <View>
          <Text style={styles.eyebrow}>Operator dashboard</Text>
          <Text style={styles.title}>Fleet trust control</Text>
        </View>
        <PrimaryButton
          label={loading ? "Refreshing" : "Refresh"}
          onPress={onRefresh}
          disabled={loading}
          style={styles.refreshButton}
        />
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}
      {!dashboard ? <Text style={styles.muted}>Loading operator trust status</Text> : null}

      {dashboard ? (
        <>
          <View style={styles.grid}>
            <MetricCard
              label="Fleet Trust"
              value={`${dashboard.fleetTrustScore}`}
              detail={`${dashboard.activeDrivers} active drivers`}
            />
            <MetricCard
              label="Pilot Evidence"
              value={`${dashboard.evidencePacketsToday}`}
              detail={`${dashboard.pilotEvidence.shiftCount} evidence shifts`}
            />
            <MetricCard
              label="Replay Exceptions"
              value={`${dashboard.openReplayExceptions}`}
              detail={`${dashboard.replayExceptionRatePct}% exception rate`}
              tone={dashboard.openReplayExceptions > 0 ? "warn" : "good"}
            />
            <MetricCard
              label="Public Verification Status"
              value={dashboard.publicVerification.status.toUpperCase()}
              detail={`${dashboard.publicVerification.passRatePct}% pass rate`}
              tone={
                dashboard.publicVerification.status === "operational"
                  ? "good"
                  : "warn"
              }
            />
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Driver Trust Trends</Text>
            {dashboard.driverTrustTrend.map((point) => (
              <View key={point.label} style={styles.trendRow}>
                <Text style={styles.trendLabel}>{point.label}</Text>
                <View style={styles.trendTrack}>
                  <View
                    style={[
                      styles.trendBar,
                      { width: `${Math.max(8, Math.min(point.score, 100))}%` },
                    ]}
                  />
                </View>
                <Text style={styles.trendScore}>{point.score}</Text>
              </View>
            ))}
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Pilot Evidence</Text>
            <Text style={styles.muted}>
              Verified rides today: {dashboard.verifiedRidesToday}
            </Text>
            <Text style={styles.muted}>
              GPS signal loss: {dashboard.pilotEvidence.gpsSignalLossEvents}
            </Text>
            <Text style={styles.muted}>
              Route deviations: {dashboard.pilotEvidence.routeDeviationEvents}
            </Text>
            <Text style={styles.muted}>
              Latency breaches: {dashboard.pilotEvidence.latencyBreaches}
            </Text>
            <Text style={styles.muted}>
              Public verification checks: {dashboard.publicVerification.checksToday}
            </Text>
          </View>
        </>
      ) : null}
    </SurfacePanel>
  );
}

function MetricCard({
  label,
  value,
  detail,
  tone = "neutral",
}: {
  label: string;
  value: string;
  detail: string;
  tone?: "neutral" | "good" | "warn";
}) {
  return (
    <View
      style={[
        styles.metricCard,
        tone === "good" ? styles.goodCard : null,
        tone === "warn" ? styles.warnCard : null,
      ]}
    >
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricDetail}>{detail}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  error: {
    color: colors.danger,
    fontWeight: "800",
  },
  eyebrow: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  goodCard: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  header: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between",
  },
  metricCard: {
    backgroundColor: colors.soft,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    flexBasis: "48%",
    flexGrow: 1,
    gap: spacing.xs,
    minWidth: 140,
    padding: spacing.md,
  },
  metricDetail: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  metricLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: "900",
    textTransform: "uppercase",
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
  refreshButton: {
    minWidth: 112,
  },
  section: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    gap: spacing.sm,
    paddingTop: spacing.md,
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "900",
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  trendBar: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    height: 10,
  },
  trendLabel: {
    color: colors.secondary,
    fontSize: 13,
    fontWeight: "900",
    width: 42,
  },
  trendRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
  },
  trendScore: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "900",
    width: 34,
  },
  trendTrack: {
    backgroundColor: colors.soft,
    borderRadius: 999,
    flex: 1,
    height: 10,
  },
  warnCard: {
    backgroundColor: "#fff7ed",
    borderColor: "#fed7aa",
  },
});
