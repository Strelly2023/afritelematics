import React, { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { getDriverIntelligence } from "../../core/api/intelligence.service";
import type { DriverIntelligenceFeed } from "../../core/models/intelligence";
import type { DriverAvailability, EarningsSummary } from "../../core/models/driver";
import type { DiagnosticsSnapshot } from "../../core/models/pilotEvidence";
import { MapPreviewCard } from "../widgets/MapPreviewCard";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type DriverHomeScreenProps = {
  availability: DriverAvailability | null;
  earnings: EarningsSummary | null;
  diagnostics: DiagnosticsSnapshot;
  loading: boolean;
  onGoAvailable: () => void;
  onGoOffline: () => void;
  onStartShift: () => void;
};

export function DriverHomeScreen({
  availability,
  earnings,
  diagnostics,
  loading,
  onGoAvailable,
  onGoOffline,
  onStartShift,
}: DriverHomeScreenProps) {
  const trustScore = availability?.trustScore || earnings?.trustScore || 94;
  const trips = earnings?.rideCount || availability?.verifiedRides || 0;
  const isAvailable = availability?.status === "available";
  const sessionLabel = !diagnostics.shiftStarted
    ? "SHIFT READY"
    : isAvailable
      ? "ACTIVE"
      : "SHIFT STARTED";
  const tripStateLabel = isAvailable ? "Awaiting dispatch" : "No active trip";
  const [intelligence, setIntelligence] = useState<DriverIntelligenceFeed | null>(null);

  useEffect(() => {
    let active = true;
    void getDriverIntelligence()
      .then((feed) => {
        if (active) {
          setIntelligence(feed);
        }
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [availability?.status, diagnostics.shiftStarted, diagnostics.locationSamples]);

  return (
    <View style={styles.stack}>
      <SurfacePanel>
        <Text style={isAvailable ? styles.online : styles.offline}>
          {isAvailable ? "ONLINE" : "OFFLINE"}
        </Text>
        <Text style={styles.title}>Driver dashboard</Text>
        <Text style={styles.subtitle}>Fast status, cleaner controls, and trust-first operations.</Text>
        <View style={styles.sessionRow}>
          <Tag label={sessionLabel} />
          <Tag label={tripStateLabel} />
        </View>
      </SurfacePanel>

      {intelligence ? (
        <SurfacePanel>
          <Text style={styles.sectionTitle}>Operational intelligence</Text>
          <Text style={styles.intelHeadline}>
            {intelligence.demand_level === "high"
              ? "High demand area"
              : intelligence.demand_level === "moderate"
                ? "Steady demand"
                : "Low demand"}
          </Text>
          <Text style={styles.intelMeta}>Zone: {intelligence.zone}</Text>
          <Text style={styles.intelMeta}>Surge: x{intelligence.surge.toFixed(1)}</Text>
          <Text style={styles.intelMeta}>Trust score: {intelligence.trust_score}</Text>
          {intelligence.predictive_positioning ? (
            <>
              <Text style={styles.sectionTitle}>Predictive positioning</Text>
              <Text style={styles.intelHeadline}>
                {intelligence.predictive_positioning.mode === "fully_autonomous"
                  ? "Fully autonomous positioning"
                  : intelligence.predictive_positioning.mode === "guided"
                    ? "Guided positioning"
                    : "Positioning held"}
              </Text>
              <Text style={styles.intelMeta}>Target zone: {intelligence.predictive_positioning.target_zone}</Text>
              <Text style={styles.intelMeta}>Confidence: {Math.round(intelligence.predictive_positioning.confidence * 100)}%</Text>
              <Text style={styles.recommendation}>{intelligence.predictive_positioning.instruction}</Text>
            </>
          ) : null}
          {intelligence.city_automation ? (
            <>
              <Text style={styles.sectionTitle}>City-wide AI automation</Text>
              <Text style={styles.intelHeadline}>
                {intelligence.city_automation.mode === "zero_operator"
                  ? "Zero-operator mode active"
                  : intelligence.city_automation.mode === "city_autonomous"
                    ? "City autonomy active"
                    : intelligence.city_automation.mode === "city_supervised"
                      ? "City automation supervised"
                      : "City automation held"}
              </Text>
              <Text style={styles.intelMeta}>
                Coverage score: {Math.round(intelligence.city_automation.coverage_score)}%
              </Text>
              <Text style={styles.intelMeta}>Recommended zone: {intelligence.city_automation.recommended_zone}</Text>
              <Text style={styles.recommendation}>{intelligence.city_automation.instruction}</Text>
              <Text style={styles.alert}>{intelligence.city_automation.reason}</Text>
            </>
          ) : null}
          {intelligence.multi_city_orchestration ? (
            <>
              <Text style={styles.sectionTitle}>Multi-city orchestration</Text>
              <Text style={styles.intelHeadline}>
                {intelligence.multi_city_orchestration.mode === "global_zero_operator"
                  ? "Global zero-operator mode"
                  : intelligence.multi_city_orchestration.mode === "global_autonomous"
                    ? "Global autonomous orchestration"
                    : intelligence.multi_city_orchestration.mode === "global_supervised"
                      ? "Global orchestration supervised"
                      : "Global orchestration held"}
              </Text>
              <Text style={styles.intelMeta}>
                Cities: {intelligence.multi_city_orchestration.city_count} / active{" "}
                {intelligence.multi_city_orchestration.active_city_count}
              </Text>
              <Text style={styles.intelMeta}>
                Coverage score: {Math.round(intelligence.multi_city_orchestration.global_coverage_score)}%
              </Text>
              <Text style={styles.recommendation}>{intelligence.multi_city_orchestration.instruction}</Text>
              <Text style={styles.alert}>{intelligence.multi_city_orchestration.reason}</Text>
            </>
          ) : null}
          {intelligence.digital_twin ? (
            <>
              <Text style={styles.sectionTitle}>Digital twin</Text>
              <Text style={styles.intelHeadline}>
                {intelligence.digital_twin.mode === "global_closed_loop"
                  ? "Global closed loop"
                  : intelligence.digital_twin.mode === "city_closed_loop"
                    ? "City closed loop"
                    : intelligence.digital_twin.mode === "predictive_closed_loop"
                      ? "Predictive closed loop"
                      : "Shadow sync"}
              </Text>
              <Text style={styles.intelMeta}>
                Live sync score: {Math.round(intelligence.digital_twin.live_sync_score)}%
              </Text>
              <Text style={styles.intelMeta}>
                Twin health: {Math.round(intelligence.digital_twin.twin_health_score)}%
              </Text>
              <Text style={styles.intelMeta}>
                Next state: {intelligence.digital_twin.prediction.next_state}
              </Text>
              <Text style={styles.recommendation}>{intelligence.digital_twin.recommendation}</Text>
              <Text style={styles.alert}>{intelligence.digital_twin.reason}</Text>
            </>
          ) : null}
          {intelligence.self_improving_loop ? (
            <>
              <Text style={styles.sectionTitle}>Self-improving AI loop</Text>
              <Text style={styles.intelHeadline}>
                {intelligence.self_improving_loop.mode === "learning"
                  ? "Learning"
                  : intelligence.self_improving_loop.mode === "recalibrating"
                    ? "Recalibrating"
                    : "Watching"}
              </Text>
              <Text style={styles.intelMeta}>Outcome score: {intelligence.self_improving_loop.outcome_score}</Text>
              <Text style={styles.intelMeta}>Band: {intelligence.self_improving_loop.band}</Text>
              <Text style={styles.recommendation}>{intelligence.self_improving_loop.measurement_summary}</Text>
            </>
          ) : null}
          <View style={styles.alerts}>
            {intelligence.alerts.map((alert) => (
              <Text key={alert} style={styles.alert}>
                {alert}
              </Text>
            ))}
          </View>
          <View style={styles.complianceRow}>
            <Tag label={`Vehicle ${intelligence.compliance.vehicle}`} />
            <Tag label={`Docs ${intelligence.compliance.documents}`} />
            <Tag label={`Inspection ${intelligence.compliance.inspection}`} />
          </View>
          <Text style={styles.recommendation}>{intelligence.recommendation}</Text>
        </SurfacePanel>
      ) : null}

      <MapPreviewCard
        routeText={
          diagnostics.lastLocation
            ? `${diagnostics.lastLocation.latitude.toFixed(4)}, ${diagnostics.lastLocation.longitude.toFixed(4)}`
            : "Waiting for GPS fix"
        }
        progressPct={diagnostics.lastLocation ? 72 : diagnostics.shiftStarted ? 35 : 10}
        statusLabel={diagnostics.shiftStarted ? "Driver telemetry" : "Driver setup"}
        etaText={availability?.updatedAt ? `Updated ${new Date(availability.updatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Shift ready"}
        liveLabel={isAvailable ? "Dispatchable" : diagnostics.shiftStarted ? "Shift active" : "Idle"}
        pickupConfirmed={diagnostics.locationSamples > 0}
        dropoffConfirmed={diagnostics.shiftStarted}
        gpsTraceAvailable={diagnostics.locationSamples > 0}
      />

      <SurfacePanel>
        <View style={styles.metricsRow}>
          <Metric label="Earnings" value={earnings?.totalText || "AUD 0"} />
          <Metric label="Trips" value={`${trips}`} />
          <Metric label="Trust" value={`${trustScore}`} />
          <Metric label="Rating" value="4.97" />
        </View>
        <View style={styles.actions}>
          <PrimaryButton
            label={isAvailable ? "Available" : "Go available"}
            onPress={onGoAvailable}
            disabled={loading || !diagnostics.shiftStarted || isAvailable}
          />
          <PrimaryButton
            label="Go offline"
            onPress={onGoOffline}
            disabled={loading || !isAvailable}
            tone="danger"
          />
          <PrimaryButton
            label={diagnostics.shiftStarted ? "Shift started" : "Start shift"}
            onPress={onStartShift}
            disabled={loading || diagnostics.shiftStarted}
          />
          {!diagnostics.shiftStarted ? (
            <Text style={styles.actionHint}>
              Start the shift to enable GPS, telemetry, and availability.
            </Text>
          ) : null}
        </View>
      </SurfacePanel>
    </View>
  );
}

function Tag({ label }: { label: string }) {
  return (
    <View style={styles.tag}>
      <Text style={styles.tagText}>{label}</Text>
    </View>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  actions: {
    gap: spacing.sm,
  },
  alert: {
    color: colors.secondary,
    fontSize: 13,
    fontWeight: "700",
  },
  alerts: {
    gap: spacing.xs,
  },
  complianceRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  intelHeadline: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: "900",
  },
  intelMeta: {
    color: colors.secondary,
    fontSize: 14,
    fontWeight: "700",
  },
  metric: {
    backgroundColor: colors.soft,
    borderRadius: 8,
    flexGrow: 1,
    gap: spacing.xs,
    minWidth: "48%",
    padding: spacing.md,
  },
  metricLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  metricValue: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: "900",
  },
  metricsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  online: {
    color: colors.success,
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0,
    textTransform: "uppercase",
  },
  offline: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 1.2,
  },
  sessionRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  actionHint: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  recommendation: {
    color: colors.primary,
    fontSize: 14,
    fontWeight: "800",
  },
  sectionTitle: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  stack: {
    gap: spacing.md,
  },
  tag: {
    backgroundColor: colors.soft,
    borderRadius: 999,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
  },
  tagText: {
    color: colors.secondary,
    fontSize: 12,
    fontWeight: "800",
  },
  subtitle: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20,
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
});
