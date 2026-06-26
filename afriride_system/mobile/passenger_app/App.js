import React, { useEffect, useMemo, useRef, useState } from "react";
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";

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
  normalizeText,
  Pill,
  ModeStrip,
  RouteGlyph,
  SectionCard,
  ProofPanel,
  ZkProofPanel,
  ShellScroll,
  Timeline,
  colors,
  statusTone,
  LoadingOverlay,
} from "../shared/novarideUi";
import { ProofWorkbench } from "../shared/verificationWorkbench";
import { deriveRiderMission } from "../shared/novarideMission";
import { NovaPayTransferPanel } from "../shared/novapayTransfer";
import {
  deriveHashes,
  formatCount,
  formatHash,
  formatMoney,
} from "../shared/proofLayer";
import { buildDeterministicUiSnapshot } from "../shared/deterministicRenderer";
import { validateReplay } from "../shared/schemaLayer";
import { verifyReplayFull } from "../shared/verificationLayer";

import {
  authenticateUser,
  cancelRide,
  getApiBaseUrl,
  getRideEvidence,
  getRideReceipt,
  getRideReplay,
  getRideStatus,
  registerRider,
  requestRide,
  setApiBaseUrl,
  updateLocalProfile,
} from "./apiClient";

const DEFAULT_RIDER_ID = "rider-1";

export default function App() {
  const [apiBaseUrl, setBaseUrlState] = useState(getApiBaseUrl());
  const [riderId, setRiderId] = useState(DEFAULT_RIDER_ID);
  const [fullName, setFullName] = useState("Rider One");
  const [phoneNumber, setPhoneNumber] = useState("+61-400-000-000");
  const [pickup, setPickup] = useState("Southbank");
  const [destination, setDestination] = useState("Melbourne CBD");
  const [rideId, setRideId] = useState("");
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [ride, setRide] = useState(null);
  const [history, setHistory] = useState([]);
  const [receipt, setReceipt] = useState(null);
  const [replay, setReplay] = useState(null);
  const [evidence, setEvidence] = useState(null);
  const [, setCryptoState] = useState(null);
  const [viewMode, setViewMode] = useState("live");
  const [proofCursor, setProofCursor] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const cryptoRequestRef = useRef(0);

  const rideStatus = ride?.status || "ready";
  const rideTone = statusTone(rideStatus);
  const rideStage = humanizeStatus(rideStatus, "Ready to book");
  const currentRideId = ride?.ride_id || rideId || "none";
  const assignedDriver = normalizeText(ride?.assigned_driver || ride?.driver_name, "Searching for driver");
  const currentFare = receipt?.fare_total ?? receipt?.amount ?? receipt?.total ?? null;
  const trustState = evidence ? "Evidence synced" : ride ? "Trip protected" : "Ready";
  const normalizedReplay = useMemo(
    () => validateReplay(replay),
    [replay?.replay_valid, replay?.replay_verified, replay?.event_count, replay?.failures, replay?.confidence],
  );
  const deterministicUi = useMemo(
    () =>
      buildDeterministicUiSnapshot(
        {
          source: "passenger",
          title: "Passenger proof mode",
          subtitle: "Replay, receipt, and evidence collapse to one canonical projection.",
          replay: normalizedReplay,
          receipt,
          evidence,
          trustScore: evidence ? 99 : ride ? 94 : 90,
          confidence: evidence ? 99 : ride ? 94 : 90,
          status: rideStage,
          activeRideId: ride?.ride_id || rideId,
          rideStatus: rideStage,
        },
        { cursor: proofCursor },
      ),
    [
      evidence,
      normalizedReplay,
      proofCursor,
      receipt,
      ride?.ride_id,
      rideId,
      rideStage,
    ],
  );
  const zkBundle = useMemo(
    () =>
      receipt?.zk_receipt ||
      receipt?.zkReceipt ||
      receipt?.zk_bundle ||
      receipt?.zkBundle ||
      receipt?.proof?.zk_receipt ||
      receipt?.proof?.zkReceipt ||
      null,
    [receipt],
  );
  useEffect(() => {
    const maxCursor = Math.max(0, deterministicUi.checkpoints.length - 1);
    if (proofCursor > maxCursor) {
      setProofCursor(maxCursor);
    }
  }, [deterministicUi.checkpoints.length, proofCursor]);
  useEffect(() => {
    if (!replay) {
      setCryptoState(null);
      return;
    }

    const requestVersion = ++cryptoRequestRef.current;
    let cancelled = false;

    (async () => {
      const result = await verifyReplayFull(normalizedReplay);
      if (!cancelled && cryptoRequestRef.current === requestVersion) {
        setCryptoState(result);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [normalizedReplay]);
  const platformContext = useMemo(
    () => ({
      actor: "rider",
      user: { id: riderId, role: "RIDER" },
      location: normalizeText(ride?.pickup || pickup),
      pickup: normalizeText(ride?.pickup || pickup),
      destination: normalizeText(ride?.destination || destination),
      weather: ride ? "clear" : "mixed",
      traffic: ride && ["STARTED", "IN_TRIP"].includes(String(rideStatus).toUpperCase()) ? "moderate" : "light",
      demand: ride ? "normal" : "high",
      confidence: ride ? 94 : 88,
      trustScore: evidence ? 99 : ride ? 94 : 90,
      evidence: Boolean(evidence),
      replay: Boolean(replay),
      receipt: Boolean(receipt),
      activeRideId: currentRideId,
      rideStatus,
      history,
      activeRides: history.length,
      driversOnline: ride?.assigned_driver ? 1 : 0,
      guards: 0,
      replayScore: replay ? 100 : 98,
      paymentDelay: receipt ? 0 : 2,
      fatigue: 0,
    }),
    [currentRideId, destination, evidence, history, pickup, receipt, replay, ride, rideStatus, riderId],
  );
  const mission = useMemo(
    () =>
      deriveRiderMission({
        ride,
        rideStatus,
        pickup: normalizeText(ride?.pickup || pickup),
        destination: normalizeText(ride?.destination || destination),
        evidence,
        receipt,
        historyCount: history.length,
        ...platformContext,
      }),
    [destination, evidence, history.length, platformContext, pickup, receipt, ride, rideStatus],
  );
  const primaryLabel = mission.primaryLabel;
  const primaryAction =
    !ride || mission.phase === "BOOKING"
      ? handleRequestRide
      : mission.phase === "SETTLED"
        ? handleFetchReceipt
        : handleRefreshStatus;
  const secondaryActionLabel = !ride || mission.phase === "BOOKING" ? "Track" : "Trust";
  const secondaryAction = !ride || mission.phase === "BOOKING" ? handleRefreshStatus : handleFetchEvidence;

  const timeline = useMemo(
    () => [
      {
        label: "Request submitted",
        detail: pickup,
        done: Boolean(ride),
      },
      {
        label: "Driver assigned",
        detail: assignedDriver,
        done: ["ACCEPTED", "ARRIVED", "STARTED", "COMPLETED"].includes(String(rideStatus).toUpperCase()),
      },
      {
        label: "Trip in motion",
        detail: destination,
        done: ["STARTED", "COMPLETED"].includes(String(rideStatus).toUpperCase()),
      },
      {
        label: "Settlement recorded",
        detail: "Receipt and replay are available after completion",
        done: Boolean(receipt),
      },
    ],
    [assignedDriver, destination, pickup, receipt, ride, rideStatus],
  );

  const metrics = useMemo(
    () => [
      {
        label: "Status",
        value: mission.stageLabel,
        detail: rideStage,
        tone: rideTone,
      },
      {
        label: "Trust",
        value: trustState,
        detail: evidence ? "Replay and evidence synchronized" : "Protected by backend receipts",
        tone: evidence ? "success" : "accent",
      },
      {
        label: "Fare",
        value: formatMoney(currentFare),
        detail: receipt ? "Receipt available" : "Updates after completion",
        tone: currentFare ? "success" : "amber",
      },
      {
        label: "Trips",
        value: formatCount(history.length, "0"),
        detail: "Recent rides",
        tone: "neutral",
      },
    ],
    [currentFare, evidence, history.length, mission.stageLabel, rideStage, rideTone, receipt, trustState],
  );
  const proofVerdict = replay
    ? deterministicUi.proofMode.label
    : evidence
      ? "Evidence ready"
      : ride
        ? "Proof pending"
        : "Awaiting trip";
  const proofTone = replay
    ? deterministicUi.proofMode.tone
    : evidence
      ? "accent"
      : "amber";
  const replayHash =
    replay?.replay_hash || replay?.replayHash || replay?.hash || replay?.authority?.authority_hash || null;
  const receiptHash = receipt?.receipt_hash || receipt?.receiptHash || receipt?.hash || null;
  const evidenceHash =
    evidence?.authority?.authority_hash || evidence?.authority_hash || evidence?.authorityHash || null;
  const proofMetrics = useMemo(
    () => [
      {
        label: "Trust score",
        value: `${deterministicUi.trustScore}%`,
        detail: "Deterministic runtime confidence",
        tone: deterministicUi.trustScore >= 95 ? "success" : "accent",
      },
      {
        label: "Replay",
        value: deterministicUi.replayState.status,
        detail: deterministicUi.replayDetail,
        tone: deterministicUi.replayState.tone,
      },
      {
        label: "Integrity",
        value:
          deterministicUi.proofMode.tone === "danger"
            ? "No proof"
            : deterministicUi.proofMode.tone === "success"
              ? "Verified"
              : deterministicUi.proofMode.tone === "danger"
                ? "Tampered"
                : "Verifying",
        detail: deterministicUi.proofMode.reason,
        tone: deterministicUi.proofMode.tone,
      },
      {
        label: "Projection",
        value: formatHash(deterministicUi.uiHash, "—"),
        detail: deterministicUi.checkpointLabel,
        tone: "accent",
      },
      {
        label: "Evidence",
        value: evidence ? "Synced" : "Pending",
        detail: evidence ? "Proof bundle present" : "Integrity bundle not loaded",
        tone: evidence ? "success" : "amber",
      },
      {
        label: "Receipt",
        value: receipt ? "Available" : "Pending",
        detail: receiptHash ? formatHash(receiptHash, "—") : "Settlement proof",
        tone: receipt ? "success" : "neutral",
      },
    ],
    [deterministicUi.checkpointLabel, deterministicUi.proofMode.reason, deterministicUi.proofMode.tone, deterministicUi.replayDetail, deterministicUi.replayState.status, deterministicUi.replayState.tone, deterministicUi.snapshotHash, deterministicUi.trustScore, deterministicUi.uiHash, evidence, receipt, receiptHash],
  );
  const proofHashes = useMemo(
    () => deriveHashes([
      {
        label: "Replay hash",
        value: formatHash(replayHash, "—"),
        tone: replayHash ? "accent" : "muted",
      },
      {
        label: "Snapshot hash",
        value: formatHash(deterministicUi.snapshotHash, "—"),
        tone: deterministicUi.snapshotHash ? "success" : "muted",
      },
      {
        label: "Receipt hash",
        value: formatHash(receiptHash, "—"),
        tone: receiptHash ? "success" : "muted",
      },
      {
        label: "UI hash",
        value: formatHash(deterministicUi.uiHash, "—"),
        tone: deterministicUi.uiHash ? "accent" : "muted",
      },
      {
        label: "Evidence hash",
        value: formatHash(evidenceHash, "—"),
        tone: evidenceHash ? "success" : "muted",
      },
    ]),
    [deterministicUi.snapshotHash, deterministicUi.uiHash, evidenceHash, receiptHash, replayHash],
  );
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

  async function handleLogin() {
    await run("login_rider", async () => {
      const authenticated = await authenticateUser({
        role: "RIDER",
        userId: riderId.trim(),
      });
      setSession(authenticated);
    });
  }

  async function handleRegister() {
    await run("register_rider", async () => {
      const registered = await registerRider({
        riderId: riderId.trim(),
        fullName: fullName.trim(),
        phoneNumber: phoneNumber.trim(),
      });
      setSession(registered);
      setProfile(registered.profile);
    });
  }

  async function handleProfileSave() {
    await run("update_profile", async () => {
      const updated = await updateLocalProfile({
        role: "RIDER",
        userId: riderId.trim(),
        profile: {
          rider_id: riderId.trim(),
          full_name: fullName.trim(),
          phone_number: phoneNumber.trim(),
        },
      });
      setProfile(updated.profile);
    });
  }

  async function handleRequestRide() {
    await run("request_ride", async () => {
      const created = await requestRide({
        passengerId: riderId.trim(),
        pickup,
        destination,
        rideId: rideId.trim() || undefined,
      });
      setRide(created);
      setRideId(created.ride_id);
      setReceipt(null);
      setReplay(null);
      setEvidence(null);
      setHistory((current) => [created, ...current.filter((item) => item.ride_id !== created.ride_id)]);
    });
  }

  async function handleRefreshStatus() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("refresh_status", async () => {
      const current = await getRideStatus({
        riderId: riderId.trim(),
        rideId: rideId.trim(),
      });
      setRide(current);
      setHistory((existing) => [current, ...existing.filter((item) => item.ride_id !== current.ride_id)]);
    });
  }

  async function handleCancelRide() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("cancel_ride", async () => {
      const cancelled = await cancelRide({
        passengerId: riderId.trim(),
        rideId: rideId.trim(),
      });
      setRide(cancelled);
      setReceipt(null);
      setReplay(null);
      setEvidence(null);
    });
  }

  async function handleFetchReceipt() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("fetch_receipt", async () => {
      const fetched = await getRideReceipt({
        riderId: riderId.trim(),
        rideId: rideId.trim(),
      });
      setReceipt(fetched);
    });
  }

  async function handleFetchReplay() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("fetch_replay", async () => {
      const fetched = await getRideReplay({
        role: "RIDER",
        userId: riderId.trim(),
        rideId: rideId.trim(),
      });
      setReplay(fetched);
    });
  }

  async function handleFetchEvidence() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("fetch_evidence", async () => {
      const fetched = await getRideEvidence({
        role: "RIDER",
        userId: riderId.trim(),
        rideId: rideId.trim(),
      });
      setEvidence(fetched);
    });
  }

  return (
    <AppShell>
      <SafeAreaView style={styles.screen}>
        <ShellScroll contentStyle={styles.content}>
          <MissionCard
            title={mission.missionTitle}
            subtitle={mission.missionSubtitle}
            step={mission.route}
            trust={mission.trustLabel}
            assistant={mission.assistant}
            actionLabel={primaryLabel}
            onPress={primaryAction}
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
              title="Deterministic proof"
              subtitle="Replay, receipt, and evidence resolve to a single canonical projection."
              verdict={proofVerdict}
              verdictTone={proofTone}
              metrics={proofMetrics}
              hashes={proofHashes}
            >
              <View style={styles.proofActions}>
                <ActionButton title="Load replay" tone="secondary" onPress={handleFetchReplay} disabled={loading} flex />
                <ActionButton title="Load evidence" tone="secondary" onPress={handleFetchEvidence} disabled={loading} flex />
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
              <ZkProofPanel bundle={zkBundle} receipt={receipt} bridge={receipt?.bridge || receipt?.zk_bridge || null} />
            </ProofPanel>
              <ProofWorkbench canonicalState={{ source: "mobile", replay: normalizedReplay, receipt, evidence: receipt?.evidence || null, zk_receipt: zkBundle }} replaySnapshot={deterministicUi} receipt={receipt} zkBundle={zkBundle} />
            </>
          ) : null}

          {viewMode !== "diagnostics" ? (
            <MapPanel
              title="Trip map"
              subtitle="Spatial context for the current ride."
            >
              <View style={styles.mapLayer}>
                <View style={styles.mapChipA} />
                <View style={styles.mapChipB} />
                <View style={styles.mapChipC} />
                <View style={styles.mapChipD} />
                <View style={styles.mapInfoCard}>
                  <Text style={styles.mapInfoLabel}>Driver</Text>
                  <Text style={styles.mapInfoValue}>{assignedDriver}</Text>
                </View>
                <View style={styles.mapInfoCardAlt}>
                  <Text style={styles.mapInfoLabel}>ETA Confidence</Text>
                  <Text style={styles.mapInfoValue}>±40 sec</Text>
                </View>
              </View>
            </MapPanel>
          ) : null}

          <MetricBand items={metrics} />

          {viewMode !== "diagnostics" ? (
            <SectionCard
              title="Platform decision"
              eyebrow="Runtime"
              action={<Pill label={`${mission.platformDecision.confidence}%`} tone="accent" />}
            >
              <InfoRow label="Recommendation" value={mission.platformDecision.label} tone="accent" />
              <InfoRow label="Reason" value={mission.platformDecision.reason} />
              <InfoRow label="Trust graph" value={mission.trustGraph.platform.graphHealth} />
            </SectionCard>
          ) : null}

          {viewMode === "diagnostics" ? (
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
          ) : null}

          {viewMode === "diagnostics" ? (
            <SectionCard title="Runtime health" eyebrow="Lifecycle" action={<Pill label={normalizeText(mission.runtimeHealth?.status, "healthy")} tone="success" />}>
              <InfoRow label="Events" value={formatCount(mission.runtimeHealth?.eventCount, "0")} />
              <InfoRow label="Queue depth" value={formatCount(mission.runtimeHealth?.queueDepth, "0")} />
              <InfoRow label="Average exec" value={`${formatCount(mission.runtimeMetrics?.averageExecutionMs, "0")} ms`} />
              <InfoRow label="Replay" value={formatCount(mission.runtimeReplay?.events?.length || mission.runtimeReplay?.length || 0, "0")} />
              <InfoRow label="Certified" value={mission.runtimeCertification?.certified ? "Yes" : "Pending"} />
              <InfoRow label="Runtime ID" value={normalizeText(mission.runtimeIdentity?.id, "unknown")} />
            </SectionCard>
          ) : null}

          {viewMode !== "diagnostics" ? (
            <SectionCard title="Book a ride" eyebrow="Request" action={<Pill label="Fast pickup" tone="accent" />}>
              <Field label="Pickup" value={pickup} onChangeText={setPickup} placeholder="Southbank" />
              <Field
                label="Destination"
                value={destination}
                onChangeText={setDestination}
                placeholder="Melbourne CBD"
              />
              <Field
                label="Ride ID (optional)"
                value={rideId}
                onChangeText={setRideId}
                placeholder="Auto-generated if empty"
              />
              <View style={styles.actionRow}>
                <ActionButton title="Request ride" onPress={handleRequestRide} disabled={loading} flex />
                <ActionButton title="Track ride" tone="secondary" onPress={handleRefreshStatus} disabled={loading} flex />
              </View>
            </SectionCard>
          ) : null}

          {viewMode !== "diagnostics" ? (
            <NovaPayTransferPanel
              role="RIDER"
              userId={riderId}
              title="NovaPay Wallet"
              subtitle="Send verified transfers with transparent pricing, bank deposit, cash pickup, and mobile-money routes."
              defaultRecipientCountry="KE"
              defaultAmount="100.00"
              defaultSourceCurrency="AUD"
              defaultPayoutMethod="bank_deposit"
              defaultUseCase="transparent_pricing"
              mode="send"
            />
          ) : null}

          {viewMode !== "diagnostics" ? (
            <SectionCard title="Trip journey" eyebrow="Live" action={<Pill label={rideStage} tone={rideTone} />}>
              <View style={styles.routeCard}>
                <RouteGlyph />
                <View style={{ flex: 1, gap: 8 }}>
                  <InfoRow label="Pickup" value={normalizeText(ride?.pickup || pickup)} tone="accent" />
                  <InfoRow
                    label="Destination"
                    value={normalizeText(ride?.destination || destination)}
                    tone="success"
                  />
                  <InfoRow label="Driver" value={assignedDriver} tone="muted" />
                  <InfoRow label="Trust" value={trustState} tone={evidence ? "success" : "accent"} />
                </View>
              </View>
              <Divider />
              <Timeline items={timeline} />
              <View style={styles.actionRow}>
                <ActionButton title="Refresh" tone="secondary" onPress={handleRefreshStatus} disabled={loading} flex />
                <ActionButton title="Cancel" tone="danger" onPress={handleCancelRide} disabled={loading} />
              </View>
            </SectionCard>
          ) : null}

          {viewMode !== "diagnostics" ? (
            <SectionCard title="Recent rides" eyebrow="History">
              {history.length === 0 ? (
                <Text style={styles.emptyText}>No ride history loaded yet.</Text>
              ) : (
                history.slice(0, 4).map((entry) => (
                  <View key={entry.ride_id} style={styles.historyCard}>
                    <View style={styles.historyTopRow}>
                      <Text style={styles.historyTitle}>{entry.ride_id}</Text>
                      <Pill label={humanizeStatus(entry.status, "Recorded")} tone={statusTone(entry.status)} />
                    </View>
                    <Text style={styles.historySubtitle}>
                      {normalizeText(entry.pickup)} to {normalizeText(entry.destination)}
                    </Text>
                    <Text style={styles.historyMeta}>
                      Assigned driver {normalizeText(entry.assigned_driver, "pending")}
                    </Text>
                  </View>
                ))
              )}
            </SectionCard>
          ) : null}

          {viewMode !== "live" ? (
            <ExpandableCard
              title="Receipt and evidence"
              eyebrow="Verification"
              summary="Available after a ride is confirmed or completed."
              defaultOpen={viewMode === "proof"}
            >
              <ActionButton title="Load receipt" onPress={handleFetchReceipt} disabled={loading} />
              <ActionButton title="Load replay" tone="secondary" onPress={handleFetchReplay} disabled={loading} />
              <ActionButton title="Load evidence" tone="secondary" onPress={handleFetchEvidence} disabled={loading} />
              <JsonCard value={receipt} empty="No receipt loaded yet." />
              <JsonCard value={replay} empty="No replay loaded." />
              <JsonCard value={evidence} empty="No evidence loaded." />
            </ExpandableCard>
          ) : null}

          {viewMode === "diagnostics" ? (
            <ExpandableCard
              title="Account and diagnostics"
              eyebrow="Advanced"
              summary="Login, registration, profile, and API base URL remain available but hidden by default."
            >
              <Field label="API base URL" value={apiBaseUrl} onChangeText={updateBaseUrl} />
              <Field label="Rider ID" value={riderId} onChangeText={setRiderId} />
              <Field label="Full name" value={fullName} onChangeText={setFullName} />
              <Field label="Phone number" value={phoneNumber} onChangeText={setPhoneNumber} />
              <View style={styles.actionRow}>
                <ActionButton title="Login" tone="secondary" onPress={handleLogin} disabled={loading} flex />
                <ActionButton title="Register" onPress={handleRegister} disabled={loading} flex />
              </View>
              <ActionButton title="Save profile" tone="secondary" onPress={handleProfileSave} disabled={loading} />
              <JsonCard value={profile} empty="No profile saved yet." />
            </ExpandableCard>
          ) : null}

          {loading ? <LoadingOverlay label="Updating ride experience" /> : null}
          {error ? <Text style={styles.errorText}>{error}</Text> : null}
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
  stack: {
    gap: 14,
  },
  tabStrip: {
    flexDirection: "row",
    gap: 8,
    padding: 6,
    borderRadius: 20,
    backgroundColor: "rgba(255, 255, 255, 0.04)",
    borderWidth: 1,
    borderColor: colors.border,
  },
  tabItem: {
    flex: 1,
    borderRadius: 14,
    paddingVertical: 11,
    alignItems: "center",
    justifyContent: "center",
  },
  tabItemActive: {
    backgroundColor: "rgba(102, 227, 255, 0.16)",
  },
  tabText: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  tabTextActive: {
    color: colors.text,
  },
  actionRow: {
    flexDirection: "row",
    gap: 10,
  },
  mapLayer: {
    flex: 1,
    position: "relative",
    minHeight: 180,
  },
  mapChipA: {
    position: "absolute",
    left: 18,
    top: 22,
    width: 14,
    height: 14,
    borderRadius: 14,
    backgroundColor: colors.mint,
  },
  mapChipB: {
    position: "absolute",
    right: 22,
    top: 54,
    width: 14,
    height: 14,
    borderRadius: 14,
    backgroundColor: colors.accent,
  },
  mapChipC: {
    position: "absolute",
    left: 52,
    bottom: 44,
    width: 14,
    height: 14,
    borderRadius: 14,
    backgroundColor: colors.amber,
  },
  mapChipD: {
    position: "absolute",
    right: 48,
    bottom: 28,
    width: 14,
    height: 14,
    borderRadius: 14,
    backgroundColor: colors.success,
  },
  mapInfoCard: {
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
  mapInfoCardAlt: {
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
  routeCard: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
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
  quickActions: {
    flexDirection: "row",
    gap: 10,
  },
  tripSurface: {
    gap: 16,
  },
  tripMeta: {
    gap: 4,
  },
  tripTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: "800",
  },
  tripSubtitle: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
  },
  routeVisual: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 8,
  },
  routeNode: {
    width: 16,
    height: 16,
    borderRadius: 16,
    backgroundColor: colors.mint,
  },
  routeNodeAlt: {
    width: 16,
    height: 16,
    borderRadius: 16,
    backgroundColor: colors.amber,
  },
  routePath: {
    flex: 1,
    height: 2,
    borderRadius: 2,
    backgroundColor: "rgba(160, 187, 220, 0.32)",
  },
  tripRows: {
    gap: 4,
  },
  historyCard: {
    padding: 14,
    borderRadius: 18,
    backgroundColor: "rgba(255, 255, 255, 0.03)",
    borderWidth: 1,
    borderColor: colors.border,
    gap: 6,
  },
  historyTopRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
  },
  historyTitle: {
    flex: 1,
    color: colors.text,
    fontSize: 15,
    fontWeight: "800",
  },
  historySubtitle: {
    color: colors.muted,
    fontSize: 13,
  },
  historyMeta: {
    color: colors.faint,
    fontSize: 12,
  },
  trustBanner: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
  },
  trustTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "800",
    marginBottom: 6,
  },
  trustText: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
  },
  emptyText: {
    color: colors.muted,
    fontSize: 13,
  },
  errorText: {
    color: colors.danger,
    fontSize: 13,
    fontWeight: "700",
  },
});
