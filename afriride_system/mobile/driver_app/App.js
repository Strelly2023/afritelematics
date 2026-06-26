import React, { useEffect, useMemo, useRef, useState } from "react";
import { Pressable, SafeAreaView, StyleSheet, Text, View } from "react-native";

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
  normalizeText,
  Pill,
  RouteGlyph,
  ProofPanel,
  ZkProofPanel,
  SectionCard,
  ShellScroll,
  Timeline,
  colors,
  statusTone,
  LoadingOverlay,
} from "../shared/novarideUi";
import { ProofWorkbench } from "../shared/verificationWorkbench";
import { deriveDriverMission } from "../shared/novarideMission";
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
  acceptRide,
  arriveRide,
  authenticateUser,
  completeTrip,
  getApiBaseUrl,
  getDriverAssignedRides,
  getDriverEarnings,
  getRideReceipt,
  getRideReplay,
  setApiBaseUrl,
  setDriverStatus,
  startTrip,
  updateLocalProfile,
} from "./apiClient";

const DEFAULT_DRIVER_ID = "driver-1";

export default function App() {
  const [apiBaseUrl, setBaseUrlState] = useState(getApiBaseUrl());
  const [driverId, setDriverId] = useState(DEFAULT_DRIVER_ID);
  const [displayName, setDisplayName] = useState("Driver One");
  const [vehicle, setVehicle] = useState("Toyota Pilot");
  const [rideId, setRideId] = useState("");
  const [online, setOnline] = useState(false);
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [rides, setRides] = useState([]);
  const [trip, setTrip] = useState(null);
  const [earnings, setEarnings] = useState(null);
  const [replay, setReplay] = useState(null);
  const [receipt, setReceipt] = useState(null);
  const [, setCryptoState] = useState(null);
  const [viewMode, setViewMode] = useState("live");
  const [proofCursor, setProofCursor] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const cryptoRequestRef = useRef(0);

  const tripStatus = trip?.status || (online ? "online" : "offline");
  const tripTone = statusTone(tripStatus);
  const tripLabel = humanizeStatus(tripStatus, online ? "Ready for rides" : "Offline");
  const assignedCount = rides.length;
  const earningsAmount = earnings?.available ?? earnings?.total ?? earnings?.balance ?? null;
  const currentVehicle = normalizeText(profile?.vehicle || vehicle, "Vehicle not set");
  const trustState = trip ? "Trip evidence available" : online ? "Operational" : "Offline";
  const normalizedReplay = useMemo(
    () => validateReplay(replay),
    [replay?.replay_valid, replay?.replay_verified, replay?.event_count, replay?.failures, replay?.confidence],
  );
  const primaryRideId = trip?.ride_id || rideId || "none";
  const deterministicUi = useMemo(
    () =>
      buildDeterministicUiSnapshot({
        source: "driver",
        title: "Driver proof mode",
        subtitle: "Replay, receipt, and trip state resolve to the same canonical snapshot.",
        replay: normalizedReplay,
        receipt,
        trustScore: trip ? 95 : online ? 90 : 84,
        confidence: online ? 92 : 70,
        status: tripStatus,
        activeRideId: primaryRideId,
        rideStatus: tripStatus,
        vehicle: currentVehicle,
      }, { cursor: proofCursor }),
    [
      currentVehicle,
      online,
      proofCursor,
      receipt,
      normalizedReplay,
      primaryRideId,
      trip,
      tripStatus,
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
      actor: "driver",
      user: { id: driverId, role: "DRIVER" },
      location: normalizeText(trip?.pickup || "Driver location unknown"),
      pickup: normalizeText(trip?.pickup || "Pickup"),
      destination: normalizeText(trip?.destination || "Destination"),
      weather: online ? "clear" : "unknown",
      traffic: trip && ["STARTED", "IN_TRIP"].includes(String(tripStatus).toUpperCase()) ? "heavy" : "moderate",
      demand: online ? "rising" : "idle",
      confidence: online ? 92 : 70,
      trustScore: trip ? 95 : online ? 90 : 84,
      evidence: Boolean(trip),
      replay: Boolean(replay),
      receipt: Boolean(receipt),
      activeRideId: primaryRideId,
      rideStatus: tripStatus,
      history: rides,
      activeRides: rides.length,
      driversOnline: online ? 1 : 0,
      guards: 0,
      replayScore: replay ? 100 : 97,
      paymentDelay: receipt ? 0 : 3,
      fatigue: online && rides.length > 3 ? 58 : 18,
      vehicle: currentVehicle,
    }),
    [currentVehicle, driverId, online, primaryRideId, receipt, replay, rides, trip, tripStatus],
  );
  const mission = useMemo(
    () =>
      deriveDriverMission({
        online,
        trip,
        tripStatus,
        ridesCount: rides.length,
        displayName,
        pickup: normalizeText(trip?.pickup || "Pickup"),
        destination: normalizeText(trip?.destination || "Destination"),
        earningsAmount,
        ...platformContext,
      }),
    [displayName, earningsAmount, online, platformContext, rides.length, trip, tripStatus],
  );
  const primaryLabel = !online
    ? "Go online"
    : trip && ["ARRIVED"].includes(String(tripStatus).toUpperCase())
      ? "Start trip"
      : trip && ["STARTED", "IN_TRIP"].includes(String(tripStatus).toUpperCase())
        ? "Complete trip"
        : "Refresh queue";
  const primaryAction = !online
    ? () => handleAvailability(true)
    : trip && ["ARRIVED"].includes(String(tripStatus).toUpperCase())
      ? handleStartRide
      : trip && ["STARTED", "IN_TRIP"].includes(String(tripStatus).toUpperCase())
        ? handleCompleteRide
        : handleLoadRides;
  const secondaryLabel = !online
    ? "Refresh queue"
    : trip && ["STARTED", "IN_TRIP"].includes(String(tripStatus).toUpperCase())
      ? "Receipt"
      : "Trust";
  const secondaryAction = !online
    ? handleLoadRides
    : trip && ["STARTED", "IN_TRIP"].includes(String(tripStatus).toUpperCase())
      ? handleLoadReceipt
      : handleLoadReplay;

  const timeline = useMemo(
    () => [
      {
        label: "Ride assigned",
        detail: normalizeText(trip?.ride_id || rideId, "No active trip"),
        done: Boolean(trip || rideId),
      },
      {
        label: "Arrived at pickup",
        detail: "Driver at pickup point",
        done: ["ARRIVED", "STARTED", "COMPLETED"].includes(String(tripStatus).toUpperCase()),
      },
      {
        label: "Trip started",
        detail: "Passenger onboard",
        done: ["STARTED", "COMPLETED"].includes(String(tripStatus).toUpperCase()),
      },
      {
        label: "Trip complete",
        detail: "Settlement and evidence stored",
        done: ["COMPLETED"].includes(String(tripStatus).toUpperCase()) || Boolean(receipt),
      },
    ],
    [receipt, rideId, trip, tripStatus],
  );

  const metrics = useMemo(
    () => [
      {
        label: "Availability",
        value: mission.statusLabel,
        detail: online ? "Dispatch enabled" : "Offline mode",
        tone: online ? "success" : "neutral",
      },
      {
        label: "Trip",
        value: tripLabel,
        detail: `Ride ${primaryRideId}`,
        tone: tripTone,
      },
      {
        label: "Queue",
        value: formatCount(assignedCount, "0"),
        detail: "Assigned rides",
        tone: "accent",
      },
      {
        label: "Earnings",
        value: formatMoney(earningsAmount),
        detail: "Live wallet snapshot",
        tone: earningsAmount ? "success" : "amber",
      },
    ],
    [assignedCount, earningsAmount, mission.statusLabel, online, primaryRideId, tripLabel, tripTone],
  );
  const replayHash = replay?.replay_hash || replay?.replayHash || replay?.hash || null;
  const receiptHash = receipt?.receipt_hash || receipt?.receiptHash || receipt?.hash || null;
  const proofVerdict = deterministicUi.proofMode.label;
  const proofTone = deterministicUi.proofMode.tone;
  const proofMetrics = useMemo(
    () => [
      {
        label: "Availability",
        value: online ? "Dispatch live" : "Offline",
        detail: mission.statusLabel,
        tone: online ? "success" : "neutral",
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
        label: "Receipt",
        value: receipt ? "Available" : "Pending",
        detail: receiptHash ? formatHash(receiptHash, "—") : "Settlement proof",
        tone: receipt ? "success" : "amber",
      },
      {
        label: "Queue",
        value: formatCount(assignedCount, "0"),
        detail: "Assigned rides",
        tone: assignedCount > 0 ? "accent" : "neutral",
      },
    ],
    [assignedCount, deterministicUi.checkpointLabel, deterministicUi.proofMode.reason, deterministicUi.proofMode.tone, deterministicUi.replayDetail, deterministicUi.replayState.status, deterministicUi.replayState.tone, deterministicUi.snapshotHash, deterministicUi.uiHash, mission.statusLabel, online, receipt, receiptHash],
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
        label: "UI hash",
        value: formatHash(deterministicUi.uiHash, "—"),
        tone: deterministicUi.uiHash ? "accent" : "muted",
      },
      {
        label: "Receipt hash",
        value: formatHash(receiptHash, "—"),
        tone: receiptHash ? "success" : "muted",
      },
    ]),
    [deterministicUi.snapshotHash, deterministicUi.uiHash, receiptHash, replayHash],
  );
  const canStepBack = deterministicUi.checkpoints.length > 1 && proofCursor > 0;
  const canStepForward =
    deterministicUi.checkpoints.length > 1 && proofCursor < deterministicUi.checkpoints.length - 1;

  const activeRideLabel = normalizeText(trip?.ride_id || rideId, "No active ride");

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
    await run("driver_login", async () => {
      const authenticated = await authenticateUser({
        role: "DRIVER",
        userId: driverId.trim(),
      });
      setSession(authenticated);
    });
  }

  async function handleProfileSave() {
    await run("driver_profile", async () => {
      const updated = await updateLocalProfile({
        role: "DRIVER",
        userId: driverId.trim(),
        profile: {
          driver_id: driverId.trim(),
          display_name: displayName.trim(),
          vehicle: vehicle.trim(),
        },
      });
      setProfile(updated.profile);
    });
  }

  async function handleAvailability(nextOnline) {
    await run("set_availability", async () => {
      const status = await setDriverStatus({
        driverId: driverId.trim(),
        online: nextOnline,
      });
      setOnline(Boolean(status.online));
      if (!nextOnline) {
        setRides([]);
      }
    });
  }

  async function handleLoadRides() {
    await run("load_rides", async () => {
      const assigned = await getDriverAssignedRides({ driverId: driverId.trim() });
      setRides(assigned.rides || []);
    });
  }

  async function handleAcceptRide(selectedRideId) {
    if (!selectedRideId) {
      setError("ride_id_required");
      return;
    }
    await run("accept_ride", async () => {
      const accepted = await acceptRide({
        driverId: driverId.trim(),
        rideId: selectedRideId,
      });
      setTrip(accepted);
      setRideId(selectedRideId);
      setRides((current) => current.filter((ride) => ride.ride_id !== selectedRideId));
      setReplay(null);
      setReceipt(null);
    });
  }

  async function handleArriveRide() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("arrive_trip", async () => {
      const arrived = await arriveRide({
        driverId: driverId.trim(),
        rideId: rideId.trim(),
      });
      setTrip(arrived);
    });
  }

  async function handleStartRide() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("start_trip", async () => {
      const started = await startTrip({
        driverId: driverId.trim(),
        rideId: rideId.trim(),
      });
      setTrip(started);
    });
  }

  async function handleCompleteRide() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("complete_trip", async () => {
      const completed = await completeTrip({
        driverId: driverId.trim(),
        rideId: rideId.trim(),
      });
      setTrip(completed);
    });
  }

  async function handleLoadEarnings() {
    await run("driver_earnings", async () => {
      const snapshot = await getDriverEarnings({ driverId: driverId.trim() });
      setEarnings(snapshot);
    });
  }

  async function handleLoadReplay() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("driver_replay", async () => {
      const snapshot = await getRideReplay({
        role: "DRIVER",
        userId: driverId.trim(),
        rideId: rideId.trim(),
      });
      setReplay(snapshot);
    });
  }

  async function handleLoadReceipt() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("driver_receipt", async () => {
      const snapshot = await getRideReceipt({
        riderId: driverId.trim(),
        rideId: rideId.trim(),
      });
      setReceipt(snapshot);
    });
  }

  return (
    <AppShell>
      <SafeAreaView style={styles.screen}>
        <ShellScroll contentStyle={styles.content}>
          <MissionCard
            title={mission.missionTitle}
            subtitle={mission.missionSubtitle}
            step={mission.phase === "ON_TRIP" ? "Navigate" : mission.phase === "READY" ? "Passenger found" : mission.phase === "OFFLINE" ? "Find demand" : "Settlement"}
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
              title="Driver proof mode"
              subtitle="Replay, receipt, and trip state resolve to the same canonical snapshot."
              verdict={proofVerdict}
              verdictTone={proofTone}
              metrics={proofMetrics}
              hashes={proofHashes}
            >
              <View style={styles.proofActions}>
                <ActionButton title="Load replay" tone="secondary" onPress={handleLoadReplay} disabled={loading} flex />
                <ActionButton title="Load receipt" tone="secondary" onPress={handleLoadReceipt} disabled={loading} flex />
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
            <MapPanel title="Driver map" subtitle="Current trip and nearby demand context.">
            <View style={styles.mapLayer}>
              <View style={styles.mapLaneA} />
              <View style={styles.mapLaneB} />
              <View style={styles.mapMarkerA} />
              <View style={styles.mapMarkerB} />
              <View style={styles.mapInfoCard}>
                <Text style={styles.mapInfoLabel}>Passenger</Text>
                <Text style={styles.mapInfoValue}>{activeRideLabel}</Text>
              </View>
              <View style={styles.mapInfoCardAlt}>
                <Text style={styles.mapInfoLabel}>Arrival confidence</Text>
                <Text style={styles.mapInfoValue}>98%</Text>
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
          <SectionCard title="Dispatch" eyebrow="Availability" action={<Pill label={online ? "Receiving rides" : "Offline"} tone={online ? "success" : "neutral"} />}>
            <View style={styles.dispatchRow}>
              <ActionButton title="Go online" onPress={() => handleAvailability(true)} disabled={loading} flex />
              <ActionButton
                title="Go offline"
                tone="danger"
                onPress={() => handleAvailability(false)}
                disabled={loading}
                flex
              />
            </View>
            <ActionButton title="Refresh queue" tone="secondary" onPress={handleLoadRides} disabled={loading} />
            <Divider />
            <InfoRow label="Driver" value={normalizeText(displayName)} />
            <InfoRow label="Vehicle" value={currentVehicle} />
            <InfoRow label="Queue depth" value={formatCount(assignedCount, "0")} />
          </SectionCard>
          ) : null}

          {viewMode !== "diagnostics" ? (
            <NovaPayTransferPanel
              role="DRIVER"
              userId={driverId}
              title="NovaPay Receiver"
              subtitle="Verify incoming transfer receipts and inspect the canonical payment proof."
              defaultRecipientCountry="AU"
              defaultAmount="75.00"
              defaultSourceCurrency="AUD"
              defaultPayoutMethod="bank_deposit"
              defaultUseCase="fast_low_cost_international"
              mode="verify"
            />
          ) : null}

          {viewMode !== "diagnostics" ? (
          <SectionCard title="Live trip" eyebrow="Context" action={<Pill label={tripLabel} tone={tripTone} />}>
            <View style={styles.tripSurface}>
              <View style={styles.tripMeta}>
                <Text style={styles.tripTitle}>{activeRideLabel}</Text>
                <Text style={styles.tripSubtitle}>
                  {normalizeText(trip?.pickup || "Pickup not locked yet")} to {normalizeText(trip?.destination || "Destination not locked yet")}
                </Text>
              </View>
              <View style={styles.routeVisual}>
                <View style={styles.routeNode} />
                <View style={styles.routePath} />
                <View style={styles.routeNodeAlt} />
              </View>
              <View style={styles.tripRows}>
                <InfoRow label="Trip state" value={tripLabel} tone={tripTone === "danger" ? "danger" : "accent"} />
                <InfoRow label="Trust" value={trustState} tone="success" />
                <InfoRow label="Ride ID" value={activeRideLabel} />
              </View>
              <View style={styles.actionRow}>
                <ActionButton title="Arrive" tone="secondary" onPress={handleArriveRide} disabled={loading} flex />
                <ActionButton title="Start" tone="secondary" onPress={handleStartRide} disabled={loading} flex />
                <ActionButton title="Complete" onPress={handleCompleteRide} disabled={loading} flex />
              </View>
            </View>
          </SectionCard>
          ) : null}

          {viewMode !== "diagnostics" ? (
          <SectionCard title="Ride queue" eyebrow="Assigned rides" action={<Pill label={formatCount(rides.length)} tone="accent" />}>
            <Field label="Ride ID" value={rideId} onChangeText={setRideId} placeholder="Paste or accept from queue" />
            <ActionButton title="Accept by ride ID" onPress={() => handleAcceptRide(rideId.trim())} disabled={loading} />
            <Divider />
            {rides.length === 0 ? (
              <Text style={styles.emptyText}>No rides loaded yet. Refresh the queue or go online.</Text>
            ) : (
              rides.slice(0, 5).map((ride) => (
                <View key={ride.ride_id} style={styles.queueCard}>
                  <View style={styles.queueTopRow}>
                    <Text style={styles.queueTitle}>{ride.ride_id}</Text>
                    <Pill label={humanizeStatus(ride.status, "Assigned")} tone={statusTone(ride.status)} />
                  </View>
                  <Text style={styles.queueSubtitle}>
                    {normalizeText(ride.pickup)} to {normalizeText(ride.dropoff || ride.destination)}
                  </Text>
                  <Text style={styles.queueMeta}>Rider trust follows the queue item, not local state.</Text>
                  <View style={styles.queueActions}>
                    <ActionButton title="Accept" onPress={() => handleAcceptRide(ride.ride_id)} disabled={loading} flex />
                  </View>
                </View>
              ))
            )}
          </SectionCard>
          ) : null}

          {viewMode !== "diagnostics" ? (
          <SectionCard title="Journey" eyebrow="Trust timeline">
            <Timeline items={timeline} />
          </SectionCard>
          ) : null}

          {viewMode !== "diagnostics" ? (
          <SectionCard title="Wallet" eyebrow="Earnings" action={<Pill label="Live" tone="success" />}>
            <ActionButton title="Load earnings" onPress={handleLoadEarnings} disabled={loading} />
            <View style={{ marginTop: 8 }}>
              <InfoRow label="Available" value={formatMoney(earnings?.available ?? earnings?.balance)} tone="success" />
              <InfoRow label="Pending" value={formatMoney(earnings?.pending)} />
              <InfoRow label="Total" value={formatMoney(earningsAmount)} />
            </View>
            <JsonCard value={earnings} empty="No earnings snapshot loaded." />
          </SectionCard>
          ) : null}

          {viewMode !== "diagnostics" ? (
          <SectionCard title="Profile" eyebrow="Identity">
            <Field label="Driver ID" value={driverId} onChangeText={setDriverId} />
            <Field label="Display name" value={displayName} onChangeText={setDisplayName} />
            <Field label="Vehicle" value={vehicle} onChangeText={setVehicle} />
            <View style={styles.actionRow}>
              <ActionButton title="Login" tone="secondary" onPress={handleLogin} disabled={loading} flex />
              <ActionButton title="Save profile" onPress={handleProfileSave} disabled={loading} flex />
            </View>
            <JsonCard value={profile} empty="No profile saved yet." />
          </SectionCard>
          ) : null}

          {viewMode !== "live" ? (
          <ExpandableCard
            title="Evidence and diagnostics"
            eyebrow="Advanced"
            summary="Replay, receipt, and API base URL remain available but hidden from the primary flow."
            defaultOpen={viewMode === "proof"}
          >
            <View style={styles.actionRow}>
              <ActionButton title="Load replay" onPress={handleLoadReplay} disabled={loading} flex />
              <ActionButton title="Load receipt" tone="secondary" onPress={handleLoadReceipt} disabled={loading} flex />
            </View>
            <JsonCard value={replay} empty="Replay is available once a ride is associated." />
            <JsonCard value={receipt} empty="Receipt is available after trip completion." />
            <Field label="API base URL" value={apiBaseUrl} onChangeText={updateBaseUrl} />
            <InfoRow label="Session" value={session?.role || "anonymous"} />
            <InfoRow label="Current ride" value={activeRideLabel} />
            {error ? <Text style={styles.errorText}>{error}</Text> : null}
          </ExpandableCard>
          ) : null}

          {loading ? <LoadingOverlay label="Updating driver cockpit" /> : null}
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
    gap: 14,
    paddingBottom: 36,
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
    backgroundColor: "rgba(136, 239, 186, 0.16)",
  },
  tabText: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  tabTextActive: {
    color: colors.text,
  },
  dispatchRow: {
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
  mapLaneA: {
    position: "absolute",
    left: 20,
    top: 28,
    right: 20,
    height: 2,
    backgroundColor: "rgba(160, 187, 220, 0.18)",
  },
  mapLaneB: {
    position: "absolute",
    left: 20,
    bottom: 34,
    right: 20,
    height: 2,
    backgroundColor: "rgba(160, 187, 220, 0.18)",
  },
  mapMarkerA: {
    position: "absolute",
    left: 18,
    top: 18,
    width: 16,
    height: 16,
    borderRadius: 16,
    backgroundColor: colors.mint,
  },
  mapMarkerB: {
    position: "absolute",
    right: 18,
    bottom: 24,
    width: 16,
    height: 16,
    borderRadius: 16,
    backgroundColor: colors.amber,
  },
  mapInfoCard: {
    position: "absolute",
    left: 14,
    bottom: 12,
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
    top: 12,
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
  actionRow: {
    flexDirection: "row",
    gap: 10,
  },
  queueCard: {
    padding: 14,
    borderRadius: 18,
    backgroundColor: "rgba(255, 255, 255, 0.03)",
    borderWidth: 1,
    borderColor: colors.border,
    gap: 6,
  },
  queueTopRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
  },
  queueTitle: {
    flex: 1,
    color: colors.text,
    fontSize: 15,
    fontWeight: "800",
  },
  queueSubtitle: {
    color: colors.muted,
    fontSize: 13,
  },
  queueMeta: {
    color: colors.faint,
    fontSize: 12,
    lineHeight: 17,
  },
  queueActions: {
    flexDirection: "row",
    gap: 10,
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
