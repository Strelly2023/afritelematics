import React, { useEffect, useMemo, useState } from "react";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";

import {
  ActionButton,
  AppShell,
  Divider,
  ExpandableCard,
  Field,
  humanizeStatus,
  InfoRow,
  JsonCard,
  MetricBand,
  MapPanel,
  MissionCard,
  ModeStrip,
  Pill,
  ProofPanel,
  ZkProofPanel,
  SectionCard,
  ShellScroll,
  Timeline,
  colors,
  normalizeText,
  statusTone,
  LoadingOverlay,
} from "../shared/novarideUi";
import { ProofWorkbench } from "../shared/verificationWorkbench";
import { deriveOperatorMission } from "../shared/novarideMission";
import { NovaPayTransferPanel } from "../shared/novapayTransfer";
import {
  deriveHashes,
  extractNumber,
  formatCount,
  formatHash,
} from "../shared/proofLayer";
import { buildDeterministicUiSnapshot } from "../shared/deterministicRenderer";

import {
  getActiveRides,
  getApiBaseUrl,
  getDriversSnapshot,
  getEvidenceHealth,
  getGuardViolations,
  getPilotMetrics,
  getReplayHealth,
  getSystemHealth,
  getTrustMetrics,
  setApiBaseUrl,
  setDriverStatus,
} from "../shared/apiClient";

const DEFAULT_OPERATOR_ID = "operator-1";

const EMPTY_STATE = {
  systemHealth: null,
  activeRides: [],
  drivers: [],
  replayHealth: null,
  evidenceHealth: null,
  trustMetrics: null,
  pilotMetrics: null,
  guardViolations: [],
};

export default function App() {
  const [apiBaseUrl, setBaseUrlState] = useState(getApiBaseUrl());
  const [operatorId, setOperatorId] = useState(DEFAULT_OPERATOR_ID);
  const [managedDriverId, setManagedDriverId] = useState("driver-1");
  const [state, setState] = useState(EMPTY_STATE);
  const [viewMode, setViewMode] = useState("live");
  const [proofCursor, setProofCursor] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const summary = useMemo(() => {
    const guards = state.guardViolations.length;
    const driversOnline = state.systemHealth?.drivers_online ?? state.trustMetrics?.drivers_online ?? 0;
    const activeRides = state.systemHealth?.active_rides ?? state.activeRides.length;
    const trustScore = state.trustMetrics?.trust_score ?? state.systemHealth?.trust_score ?? 0;
    const replayScore = extractNumber(
      state.replayHealth?.replay_success_rate ??
        state.replayHealth?.consistency ??
        state.replayHealth?.match_rate ??
        100,
    );
    return { guards, driversOnline, activeRides, trustScore, replayScore };
  }, [state]);

  const metrics = useMemo(
    () => [
      {
        label: "Fleet trust",
        value: `${formatCount(summary.trustScore, "0")}/100`,
        detail: "Derived from backend trust metrics",
        tone: summary.trustScore >= 95 ? "success" : summary.trustScore >= 85 ? "accent" : "amber",
      },
      {
        label: "Drivers online",
        value: formatCount(summary.driversOnline, "0"),
        detail: "Dispatch capacity",
        tone: "success",
      },
      {
        label: "Active rides",
        value: formatCount(summary.activeRides, "0"),
        detail: "Operational load",
        tone: summary.activeRides > 0 ? "accent" : "neutral",
      },
      {
        label: "Open incidents",
        value: formatCount(summary.guards, "0"),
        detail: "Guard violations",
        tone: summary.guards > 0 ? "danger" : "success",
      },
    ],
    [summary.activeRides, summary.driversOnline, summary.guards, summary.trustScore],
  );
  const platformContext = useMemo(
    () => ({
      actor: "operator",
      user: { id: operatorId, role: "OPERATOR" },
      location: "fleet-control",
      weather: summary.guards > 0 ? "mixed" : "clear",
      traffic: summary.activeRides > 15 ? "heavy" : "moderate",
      demand: summary.activeRides > 12 ? "high" : "normal",
      confidence: summary.trustScore || 88,
      trustScore: summary.trustScore,
      evidence: summary.replayScore >= 99,
      replay: summary.replayScore >= 99,
      receipt: true,
      activeRideId: null,
      rideStatus: "CONTROL",
      activeRides: summary.activeRides,
      driversOnline: summary.driversOnline,
      guards: summary.guards,
      replayScore: summary.replayScore,
      paymentDelay: 0.4,
      fatigue: summary.guards > 0 ? 55 : 18,
    }),
    [operatorId, summary.activeRides, summary.driversOnline, summary.guards, summary.replayScore, summary.trustScore],
  );
  const mission = useMemo(
    () =>
      deriveOperatorMission({
        guards: summary.guards,
        activeRides: summary.activeRides,
        driversOnline: summary.driversOnline,
        trustScore: summary.trustScore,
        ...platformContext,
      }),
    [platformContext, summary.activeRides, summary.driversOnline, summary.guards, summary.trustScore],
  );

  const insights = useMemo(
    () => [
      {
        label: "Demand Forecast",
        value: `${mission.demandLabel} +${Math.max(8, mission.demandScore - 40)}%`,
        detail: "Expected in 18 minutes",
        tone: mission.demandScore >= 75 ? "amber" : "accent",
      },
      {
        label: "Driver Fatigue",
        value: mission.fatigueScore >= 60 ? "Potential issue" : mission.fatigueScore >= 30 ? "Monitor" : "Normal",
        detail: mission.fatigueScore >= 60 ? "Recommend break" : "Operational",
        tone: mission.fatigueScore >= 60 ? "amber" : "success",
      },
      {
        label: "Payment Delay",
        value: `${mission.paymentDelay.toFixed(1)}%`,
        detail: mission.paymentDelay > 5 ? "Investigate settlement latency" : "Normal",
        tone: mission.paymentDelay > 5 ? "amber" : "success",
      },
      {
        label: "Replay Integrity",
        value: `${summary.replayScore.toFixed(0)}%`,
        detail: "Healthy",
        tone: summary.replayScore >= 99 ? "success" : "accent",
      },
    ],
    [mission.demandLabel, mission.demandScore, mission.fatigueScore, mission.paymentDelay, summary.replayScore],
  );
  const replayHash =
    state.replayHealth?.replay_hash ||
    state.replayHealth?.replayHash ||
    state.replayHealth?.hash ||
    state.replayHealth?.authority?.authority_hash ||
    null;
  const evidenceHash =
    state.evidenceHealth?.authority?.authority_hash ||
    state.evidenceHealth?.authority_hash ||
    state.evidenceHealth?.authorityHash ||
    null;
  const trustHash =
    state.trustMetrics?.authority?.authority_hash ||
    state.trustMetrics?.authority_hash ||
    state.trustMetrics?.authorityHash ||
    null;
  const deterministicUi = useMemo(
    () =>
      buildDeterministicUiSnapshot(
        {
          source: "operator",
          title: "Fleet proof mode",
          subtitle: "Trust, replay, and evidence resolve to one canonical fleet snapshot.",
          replay: state.replayHealth,
          receipt: state.evidenceHealth,
          evidence: state.evidenceHealth,
          trustScore: summary.trustScore,
          confidence: summary.trustScore,
          status: "CONTROL",
          activeRideId: null,
          rideStatus: "CONTROL",
        },
        { cursor: proofCursor },
      ),
    [proofCursor, state.evidenceHealth, state.replayHealth, summary.trustScore],
  );
  const zkBundle = useMemo(
    () =>
      state.evidenceHealth?.zk_receipt ||
      state.evidenceHealth?.zkReceipt ||
      state.evidenceHealth?.zk_bundle ||
      state.evidenceHealth?.zkBundle ||
      state.evidenceHealth?.proof?.zk_receipt ||
      state.evidenceHealth?.proof?.zkReceipt ||
      null,
    [state.evidenceHealth],
  );
  useEffect(() => {
    const maxCursor = Math.max(0, deterministicUi.checkpoints.length - 1);
    if (proofCursor > maxCursor) {
      setProofCursor(maxCursor);
    }
  }, [deterministicUi.checkpoints.length, proofCursor]);
  const proofMetrics = useMemo(
    () => [
      {
        label: "Fleet trust",
        value: `${formatCount(deterministicUi.trustScore, "0")}/100`,
        detail: "Canonical trust snapshot",
        tone: deterministicUi.trustScore >= 95 ? "success" : "accent",
      },
      {
        label: "Replay",
        value: deterministicUi.replayState.status,
        detail: deterministicUi.replayDetail,
        tone: deterministicUi.replayState.tone,
      },
      {
        label: "Drivers",
        value: formatCount(summary.driversOnline, "0"),
        detail: "Dispatch capacity",
        tone: "success",
      },
      {
        label: "Projection",
        value: formatHash(deterministicUi.uiHash, "—"),
        detail: deterministicUi.checkpointLabel,
        tone: "accent",
      },
    ],
    [deterministicUi.checkpointLabel, deterministicUi.replayDetail, deterministicUi.replayState.status, deterministicUi.replayState.tone, deterministicUi.snapshotHash, deterministicUi.trustScore, deterministicUi.uiHash, summary.driversOnline],
  );
  const proofHashes = useMemo(
    () => deriveHashes([
      { label: "Replay hash", value: formatHash(replayHash, "—"), tone: replayHash ? "accent" : "muted" },
      { label: "Evidence hash", value: formatHash(evidenceHash, "—"), tone: evidenceHash ? "success" : "muted" },
      { label: "Trust hash", value: formatHash(trustHash, "—"), tone: trustHash ? "success" : "muted" },
      { label: "Snapshot hash", value: formatHash(deterministicUi.snapshotHash, "—"), tone: deterministicUi.snapshotHash ? "success" : "muted" },
      { label: "UI hash", value: formatHash(deterministicUi.uiHash, "—"), tone: deterministicUi.uiHash ? "accent" : "muted" },
    ]),
    [deterministicUi.snapshotHash, deterministicUi.uiHash, evidenceHash, replayHash, trustHash],
  );
  const proofVerdict = deterministicUi.proofMode.label;
  const proofTone = deterministicUi.proofMode.tone;
  const canStepBack = deterministicUi.checkpoints.length > 1 && proofCursor > 0;
  const canStepForward =
    deterministicUi.checkpoints.length > 1 && proofCursor < deterministicUi.checkpoints.length - 1;

  function updateBaseUrl(value) {
    setBaseUrlState(value);
    setApiBaseUrl(value);
  }

  async function run(label, action) {
    setLoading(true);
    setError("");
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : `${label}_failed`);
    } finally {
      setLoading(false);
    }
  }

  async function refresh() {
    await run("operator_refresh", async () => {
      const nextOperatorId = operatorId.trim();
      const [
        systemHealth,
        activeRidesPayload,
        driversPayload,
        replayHealth,
        evidenceHealth,
        trustMetrics,
        pilotMetrics,
        guardsPayload,
      ] = await Promise.all([
        getSystemHealth({ operatorId: nextOperatorId }),
        getActiveRides({ operatorId: nextOperatorId }),
        getDriversSnapshot({ operatorId: nextOperatorId }),
        getReplayHealth({ operatorId: nextOperatorId }),
        getEvidenceHealth({ operatorId: nextOperatorId }),
        getTrustMetrics({ operatorId: nextOperatorId }),
        getPilotMetrics({ operatorId: nextOperatorId }),
        getGuardViolations({ operatorId: nextOperatorId }),
      ]);

      setState({
        systemHealth,
        activeRides: activeRidesPayload.rides || [],
        drivers: driversPayload.drivers || [],
        replayHealth,
        evidenceHealth,
        trustMetrics,
        pilotMetrics,
        guardViolations: guardsPayload.violations || [],
      });
    });
  }

  async function setManagedDriverOnline(online) {
    await run("driver_management", async () => {
      await setDriverStatus({
        driverId: managedDriverId.trim(),
        online,
      });
      await refresh();
    });
  }

  return (
    <AppShell>
      <SafeAreaView style={styles.screen}>
        <ShellScroll contentStyle={styles.content}>
          <MissionCard
            title={mission.missionTitle}
            subtitle={mission.missionSubtitle}
            step={`Fleet trust ${formatCount(summary.trustScore, "0")}/100`}
            trust={mission.statusLabel}
            assistant={mission.assistant}
            actionLabel="Refresh fleet"
            onPress={refresh}
          />

          <ModeStrip
            modes={[
              { value: "live", label: "Live" },
              { value: "proof", label: "Proof" },
              { value: "diagnostics", label: "Diagnostics" },
            ]}
            active={viewMode}
            onChange={setViewMode}
          />

          {viewMode === "proof" ? (
            <>
              <ProofPanel
              title="Fleet proof mode"
              subtitle="Trust, replay, and evidence are rendered from the same canonical state."
              verdict={proofVerdict}
              verdictTone={proofTone}
              metrics={proofMetrics}
              hashes={proofHashes}
            >
              <View style={styles.proofActions}>
                <ActionButton title="Refresh fleet" onPress={refresh} disabled={loading} flex />
                <ActionButton title="Load replay health" tone="secondary" onPress={refresh} disabled={loading} flex />
              </View>
              <View style={styles.snapshotControls}>
                <ActionButton title="Prev snapshot" tone="secondary" onPress={() => setProofCursor((current) => Math.max(0, current - 1))} disabled={!canStepBack} flex />
                <ActionButton title="Latest snapshot" onPress={() => setProofCursor(Math.max(0, deterministicUi.checkpoints.length - 1))} disabled={deterministicUi.checkpoints.length === 0} flex />
                <ActionButton title="Next snapshot" tone="secondary" onPress={() => setProofCursor((current) => Math.min(deterministicUi.checkpoints.length - 1, current + 1))} disabled={!canStepForward} flex />
              </View>
              <InfoRow label="Checkpoint" value={deterministicUi.checkpointLabel} />
              <InfoRow label="As of" value={deterministicUi.asOf || "Latest"} />
              <InfoRow label="UI snapshot" value={formatHash(deterministicUi.snapshotHash, "—")} />
              <InfoRow label="Trust score" value={`${formatCount(deterministicUi.trustScore, "0")}/100`} />
              <Divider />
              <Timeline items={deterministicUi.timeline} />
              <Divider />
              <ZkProofPanel bundle={zkBundle} receipt={state.evidenceHealth} bridge={state.evidenceHealth?.bridge || state.evidenceHealth?.zk_bridge || null} />
            </ProofPanel>
              <ProofWorkbench canonicalState={{ source: "mobile", replay: normalizedReplay, receipt, evidence: receipt?.evidence || null, zk_receipt: zkBundle }} replaySnapshot={deterministicUi} receipt={receipt} zkBundle={zkBundle} />
            </>
          ) : null}

          <MapPanel title="Fleet heatmap" subtitle="Demand, incidents, trust, replay, and vehicles.">
            <View style={styles.mapLayer}>
              <View style={styles.mapBlobA} />
              <View style={styles.mapBlobB} />
              <View style={styles.mapBlobC} />
              <View style={styles.mapBlobD} />
              <View style={styles.mapLabelCard}>
                <Text style={styles.mapInfoLabel}>Demand</Text>
                <Text style={styles.mapInfoValue}>{mission.demandLabel}</Text>
              </View>
              <View style={styles.mapLabelCardAlt}>
                <Text style={styles.mapInfoLabel}>Replay</Text>
                <Text style={styles.mapInfoValue}>{summary.replayScore.toFixed(0)}%</Text>
              </View>
            </View>
          </MapPanel>

          <MetricBand items={metrics} />

          <SectionCard title="Platform decision" eyebrow="Runtime" action={<Pill label={`${mission.platformDecision.confidence}%`} tone="accent" />}>
            <InfoRow label="Recommendation" value={mission.platformDecision.label} tone="accent" />
            <InfoRow label="Reason" value={mission.platformDecision.reason} />
            <InfoRow label="Trust graph" value={mission.trustGraph.platform.graphHealth} />
          </SectionCard>

          <SectionCard
            title="Runtime kernel"
            eyebrow="Platform runtime"
            action={<Pill label={`${mission.runtimeSignals?.eventCount || 0} events`} tone="success" />}
          >
            <InfoRow label="Kernel" value={normalizeText(mission.runtimeKernel?.name, "NovaRuntime")} />
            <InfoRow label="Version" value={normalizeText(mission.runtimeKernel?.version, "1.0.0")} />
            <InfoRow label="Contract" value={normalizeText(mission.runtimeContracts?.runtime?.version, "1.0.0")} />
            <InfoRow label="Plugin count" value={formatCount(mission.runtimeSignals?.pluginCount, "0")} />
            <InfoRow label="Queue depth" value={formatCount(mission.runtimeSignals?.queueDepth, "0")} />
            <InfoRow label="Projection store" value={formatCount(Object.keys(mission.runtimeProjectionStore || {}).length, "0")} />
          </SectionCard>

          <SectionCard title="Runtime health" eyebrow="Lifecycle" action={<Pill label={normalizeText(mission.runtimeHealth?.status, "healthy")} tone="success" />}>
            <InfoRow label="Events" value={formatCount(mission.runtimeHealth?.eventCount, "0")} />
            <InfoRow label="Queue depth" value={formatCount(mission.runtimeHealth?.queueDepth, "0")} />
            <InfoRow label="Average exec" value={`${formatCount(mission.runtimeMetrics?.averageExecutionMs, "0")} ms`} />
            <InfoRow label="Replay" value={formatCount(mission.runtimeReplay?.events?.length || mission.runtimeReplay?.length || 0, "0")} />
            <InfoRow label="Certified" value={mission.runtimeCertification?.certified ? "Yes" : "Pending"} />
            <InfoRow label="Runtime ID" value={normalizeText(mission.runtimeIdentity?.id, "unknown")} />
          </SectionCard>

          <SectionCard title="Control room" eyebrow="Dispatch" action={<Pill label="Live reload" tone="success" />}>
            <Field label="API base URL" value={apiBaseUrl} onChangeText={updateBaseUrl} />
            <Field label="Operator ID" value={operatorId} onChangeText={setOperatorId} />
            <View style={styles.actionRow}>
              <ActionButton title="Refresh state" onPress={refresh} disabled={loading} flex />
              <ActionButton title="Set driver online" tone="secondary" onPress={() => setManagedDriverOnline(true)} disabled={loading} flex />
            </View>
            <InfoRow label="Drivers online" value={formatCount(summary.driversOnline, "0")} />
            <InfoRow label="Active rides" value={formatCount(summary.activeRides, "0")} />
            <InfoRow label="Open incidents" value={formatCount(summary.guards, "0")} tone={summary.guards > 0 ? "danger" : "success"} />
          </SectionCard>

          <NovaPayTransferPanel
            role="OPERATOR"
            userId={operatorId}
            title="NovaPay Control"
            subtitle="Monitor quotes, payout methods, fees, limits, and canonical transfer receipts."
            defaultRecipientCountry="KE"
            defaultAmount="1000.00"
            defaultSourceCurrency="AUD"
            defaultPayoutMethod="cash_pickup"
            defaultUseCase="large_international"
            mode="ops"
          />

          <SectionCard title="Fleet overview" eyebrow="Status">
            {state.systemHealth ? (
              <>
                <InfoRow label="Service" value={normalizeText(state.systemHealth.status, "healthy")} />
                <InfoRow label="Replay" value={normalizeText(state.replayHealth?.status || state.replayHealth?.health, "unknown")} />
                <InfoRow label="Evidence" value={normalizeText(state.evidenceHealth?.status || state.evidenceHealth?.health, "unknown")} />
                <InfoRow label="Pilot metrics" value={normalizeText(state.pilotMetrics?.status || state.pilotMetrics?.health, "unknown")} />
              </>
            ) : (
              <Text style={styles.emptyText}>Refresh to load fleet health.</Text>
            )}
          </SectionCard>

          <SectionCard title="Operational intelligence" eyebrow="Forecast">
            <MetricBand items={insights} />
          </SectionCard>

          <SectionCard title="Active rides" eyebrow="Dispatch queue">
            {state.activeRides.length === 0 ? (
              <Text style={styles.emptyText}>No active rides.</Text>
            ) : (
              state.activeRides.slice(0, 6).map((ride) => (
                <View key={ride.ride_id} style={styles.itemCard}>
                  <View style={styles.itemTopRow}>
                    <Text style={styles.itemTitle}>{ride.ride_id}</Text>
                    <Pill label={humanizeStatus(ride.state || ride.status, "Active")} tone={statusTone(ride.state || ride.status)} />
                  </View>
                  <Text style={styles.itemText}>Driver: {normalizeText(ride.driver_id || ride.driver, "unassigned")}</Text>
                  <Text style={styles.itemText}>Rider: {normalizeText(ride.rider_id || ride.rider, "unknown")}</Text>
                  <Text style={styles.itemText}>
                    {normalizeText(ride.pickup)} to {normalizeText(ride.dropoff || ride.destination)}
                  </Text>
                </View>
              ))
            )}
          </SectionCard>

          <SectionCard title="Drivers" eyebrow="Availability">
            <Field label="Managed driver ID" value={managedDriverId} onChangeText={setManagedDriverId} />
            <View style={styles.actionRow}>
              <ActionButton title="Set online" onPress={() => setManagedDriverOnline(true)} disabled={loading} flex />
              <ActionButton title="Set offline" tone="danger" onPress={() => setManagedDriverOnline(false)} disabled={loading} flex />
            </View>
            {state.drivers.length === 0 ? (
              <Text style={styles.emptyText}>No driver snapshot loaded.</Text>
            ) : (
              state.drivers.slice(0, 6).map((driver) => (
                <View key={driver.driver_id} style={styles.itemCard}>
                  <View style={styles.itemTopRow}>
                    <Text style={styles.itemTitle}>{driver.driver_id}</Text>
                    <Pill label={humanizeStatus(driver.status, "Ready")} tone={statusTone(driver.status)} />
                  </View>
                  <Text style={styles.itemText}>Active rides: {(driver.active_ride_ids || []).join(", ") || "none"}</Text>
                  <Text style={styles.itemText}>Completed rides: {formatCount(driver.completed_rides, "0")}</Text>
                </View>
              ))
            )}
          </SectionCard>

          <ExpandableCard title="Evidence, replay, and incidents" eyebrow="Advanced" summary="Operational payloads stay hidden until you need them.">
            <JsonCard value={state.replayHealth} empty="No replay health loaded." />
            <JsonCard value={state.evidenceHealth} empty="No evidence health loaded." />
            <JsonCard
              value={{
                systemHealth: state.systemHealth,
                trustMetrics: state.trustMetrics,
                pilotMetrics: state.pilotMetrics,
                guardViolations: state.guardViolations,
              }}
              empty="No operations surface loaded."
            />
          </ExpandableCard>

          {loading ? <LoadingOverlay label="Refreshing fleet control" /> : null}
          {error ? <Text style={styles.error}>{error}</Text> : null}
        </ShellScroll>
      </SafeAreaView>
    </AppShell>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "transparent",
  },
  content: {
    paddingBottom: 36,
    gap: 14,
  },
  actionRow: {
    flexDirection: "row",
    gap: 10,
  },
  proofActions: {
    flexDirection: "row",
    gap: 10,
  },
  snapshotControls: {
    flexDirection: "row",
    gap: 10,
    marginTop: 10,
  },
  mapLayer: {
    flex: 1,
    minHeight: 180,
    position: "relative",
  },
  mapBlobA: {
    position: "absolute",
    left: 16,
    top: 18,
    width: 100,
    height: 100,
    borderRadius: 100,
    backgroundColor: "rgba(102, 227, 255, 0.12)",
  },
  mapBlobB: {
    position: "absolute",
    right: 20,
    top: 36,
    width: 120,
    height: 120,
    borderRadius: 120,
    backgroundColor: "rgba(136, 239, 186, 0.10)",
  },
  mapBlobC: {
    position: "absolute",
    left: 24,
    bottom: 24,
    width: 140,
    height: 140,
    borderRadius: 140,
    backgroundColor: "rgba(255, 201, 120, 0.08)",
  },
  mapBlobD: {
    position: "absolute",
    right: 28,
    bottom: 18,
    width: 92,
    height: 92,
    borderRadius: 92,
    backgroundColor: "rgba(102, 227, 255, 0.08)",
  },
  mapLabelCard: {
    position: "absolute",
    left: 14,
    bottom: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 16,
    backgroundColor: "rgba(10, 18, 30, 0.84)",
    borderWidth: 1,
    borderColor: colors.border,
  },
  mapLabelCardAlt: {
    position: "absolute",
    right: 14,
    top: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 16,
    backgroundColor: "rgba(10, 18, 30, 0.84)",
    borderWidth: 1,
    borderColor: colors.border,
  },
  mapInfoLabel: {
    color: colors.muted,
    fontSize: 11,
    textTransform: "uppercase",
    letterSpacing: 0.9,
    fontWeight: "800",
  },
  mapInfoValue: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "800",
    marginTop: 4,
  },
  emptyText: {
    color: colors.muted,
    fontSize: 13,
  },
  error: {
    color: colors.danger,
    fontSize: 13,
    fontWeight: "700",
  },
  itemCard: {
    padding: 14,
    borderRadius: 18,
    backgroundColor: "rgba(255,255,255,0.03)",
    borderWidth: 1,
    borderColor: colors.border,
    gap: 6,
  },
  itemTopRow: {
    flexDirection: "row",
    gap: 8,
    alignItems: "flex-start",
  },
  itemTitle: {
    flex: 1,
    color: colors.text,
    fontSize: 15,
    fontWeight: "800",
  },
  itemText: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
  },
});
