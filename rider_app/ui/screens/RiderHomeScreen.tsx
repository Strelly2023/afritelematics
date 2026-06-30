import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { getPassengerIntelligence } from "../../core/api/intelligence.service";
import type { PassengerIntelligenceFeed } from "../../core/models/intelligence";
import { MapPreviewCard } from "../widgets/MapPreviewCard";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type RiderHomeScreenProps = {
  pickup: string;
  dropoff: string;
  loading: boolean;
  onPickupChange: (value: string) => void;
  onDropoffChange: (value: string) => void;
  onRequestRide: () => void;
};

const rideOptions = [
  { label: "Economy", eta: "5 min", price: "UGX 18,000" },
  { label: "Comfort", eta: "4 min", price: "UGX 25,000" },
  { label: "XL", eta: "6 min", price: "UGX 35,000" },
];

const quickStops = ["Home", "Work", "Airport"];

export function RiderHomeScreen({
  pickup,
  dropoff,
  loading,
  onPickupChange,
  onDropoffChange,
  onRequestRide,
}: RiderHomeScreenProps) {
  const [intelligence, setIntelligence] = useState<PassengerIntelligenceFeed | null>(null);
  const intelligenceAlerts = Array.isArray(intelligence?.alerts)
    ? intelligence.alerts
    : [];

  useEffect(() => {
    let active = true;
    void getPassengerIntelligence()
      .then((feed) => {
        if (active) {
          setIntelligence(feed);
        }
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [pickup, dropoff]);

  return (
    <View style={styles.screen}>
      {intelligence ? (
        <SurfacePanel>
          <Text style={styles.sectionTitle}>System intelligence</Text>
          <Text style={styles.systemStatus}>System status: {intelligence.system_status}</Text>
          <Text style={styles.intelMeta}>Safety score: {intelligence.safety_score}%</Text>
          <Text style={styles.intelMeta}>Demand: {humanDemand(intelligence.demand)}</Text>
          <Text style={styles.intelMeta}>ETA confidence: {intelligence.eta_confidence}</Text>
          {intelligence.predictive_positioning ? (
            <>
              <Text style={styles.sectionTitle}>Predictive positioning</Text>
              <Text style={styles.systemStatus}>
                {intelligence.predictive_positioning.mode === "fully_autonomous"
                  ? "Fully autonomous driver positioning"
                  : intelligence.predictive_positioning.mode === "guided"
                    ? "Guided positioning active"
                    : "Positioning held"}
              </Text>
              <Text style={styles.intelMeta}>Target zone: {intelligence.predictive_positioning.target_zone}</Text>
              <Text style={styles.intelMeta}>
                Confidence: {Math.round(intelligence.predictive_positioning.confidence * 100)}%
              </Text>
              <Text style={styles.recommendation}>{intelligence.predictive_positioning.instruction}</Text>
              <Text style={styles.alert}>{intelligence.predictive_positioning.reason}</Text>
            </>
          ) : null}
          {intelligence.city_automation ? (
            <>
              <Text style={styles.sectionTitle}>City-wide AI automation</Text>
              <Text style={styles.systemStatus}>
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
              <Text style={styles.systemStatus}>
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
              <Text style={styles.systemStatus}>
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
              <Text style={styles.intelMeta}>Next state: {intelligence.digital_twin.prediction?.next_state || "syncing"}</Text>
              <Text style={styles.recommendation}>{intelligence.digital_twin.recommendation}</Text>
              <Text style={styles.alert}>{intelligence.digital_twin.reason}</Text>
            </>
          ) : null}
          {intelligence.self_improving_loop ? (
            <>
              <Text style={styles.sectionTitle}>Self-improving AI loop</Text>
              <Text style={styles.systemStatus}>
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
          <View style={styles.trustRow}>
            <TrustPill label={intelligence.trust?.driver_verified ? "Driver verified" : "Driver review"} />
            <TrustPill label={intelligence.trust?.vehicle_verified ? "Vehicle verified" : "Vehicle review"} />
            <TrustPill label={intelligence.trust?.payment_secure ? "Payment secured" : "Payment review"} />
          </View>
          <View style={styles.alerts}>
            {intelligenceAlerts.map((alert) => (
              <Text key={alert} style={styles.alert}>
                {alert}
              </Text>
            ))}
          </View>
        </SurfacePanel>
      ) : null}

      <MapPreviewCard
        routeText={dropoff ? `${pickup} to ${dropoff}` : `${pickup} to your destination`}
        progressPct={24}
        statusLabel="Find a ride"
        etaText="Live fare after dispatch"
        liveLabel="Map first"
        pickupConfirmed={Boolean(pickup)}
        dropoffConfirmed={Boolean(dropoff)}
        gpsTraceAvailable={false}
      />

      <SurfacePanel>
        <Text style={styles.title}>Where are you going?</Text>
        <Text style={styles.subtitle}>Simple booking with a live map and verified trip flow.</Text>

        <TextInput
          placeholder="Pickup"
          placeholderTextColor={colors.muted}
          value={pickup}
          onChangeText={onPickupChange}
          style={styles.input}
        />
        <TextInput
          placeholder="Destination"
          placeholderTextColor={colors.muted}
          value={dropoff}
          onChangeText={onDropoffChange}
          style={styles.input}
        />

        <View style={styles.quickRow}>
          {quickStops.map((stop) => (
            <View key={stop} style={styles.quickChip}>
              <Text style={styles.quickLabel}>{stop}</Text>
            </View>
          ))}
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.optionRow}>
          {rideOptions.map((option) => (
            <View key={option.label} style={styles.optionCard}>
              <Text style={styles.optionTitle}>{option.label}</Text>
              <Text style={styles.optionMeta}>{option.eta}</Text>
              <Text style={styles.optionPrice}>{option.price}</Text>
            </View>
          ))}
        </ScrollView>

        <View style={styles.trustRow}>
          <TrustPill label="Trip verified" />
          <TrustPill label="Driver verified" />
          <TrustPill label="Payment verified" />
        </View>

        <PrimaryButton
          label={loading ? "Booking" : "Book ride"}
          onPress={onRequestRide}
          disabled={loading}
        />
      </SurfacePanel>
    </View>
  );
}

function TrustPill({ label }: { label: string }) {
  return (
    <View style={styles.trustPill}>
      <Text style={styles.trustText}>{label}</Text>
    </View>
  );
}

function humanDemand(demand: PassengerIntelligenceFeed["demand"]): string {
  switch (demand) {
    case "high":
      return "High demand";
    case "moderate":
      return "Moderate demand";
    case "low":
      return "Low demand";
  }
}

const styles = StyleSheet.create({
  input: {
    backgroundColor: colors.soft,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.ink,
    fontSize: 16,
    minHeight: 48,
    paddingHorizontal: spacing.md,
  },
  alert: {
    color: colors.secondary,
    fontSize: 13,
    fontWeight: "700",
  },
  alerts: {
    gap: spacing.xs,
  },
  intelMeta: {
    color: colors.secondary,
    fontSize: 14,
    fontWeight: "700",
  },
  sectionTitle: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  systemStatus: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "900",
  },
  optionCard: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    minWidth: 120,
    padding: spacing.md,
  },
  optionMeta: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  optionPrice: {
    color: colors.success,
    fontSize: 14,
    fontWeight: "900",
  },
  optionRow: {
    gap: spacing.sm,
    paddingVertical: spacing.xs,
  },
  optionTitle: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "900",
  },
  quickChip: {
    backgroundColor: colors.soft,
    borderRadius: 999,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  quickLabel: {
    color: colors.secondary,
    fontSize: 13,
    fontWeight: "800",
  },
  quickRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  recommendation: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: "800",
    lineHeight: 20,
  },
  screen: {
    gap: spacing.md,
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
  trustPill: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
  },
  trustRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  trustText: {
    color: colors.success,
    fontSize: 12,
    fontWeight: "900",
  },
});
