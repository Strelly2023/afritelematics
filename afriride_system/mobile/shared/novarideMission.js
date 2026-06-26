import { createPlatformRuntime } from "./novarideKernel";

export const MISSION_PHASES = {
  RIDER: {
    BOOKING: "BOOKING",
    WAITING: "WAITING",
    ACTIVE: "ACTIVE",
    SETTLED: "SETTLED",
  },
  DRIVER: {
    OFFLINE: "OFFLINE",
    READY: "READY",
    ON_TRIP: "ON_TRIP",
    SETTLED: "SETTLED",
  },
  OPERATOR: {
    CONTROL: "CONTROL",
  },
};

function upper(value) {
  return String(value || "").toUpperCase();
}

export function derivePlatformMission(context = {}) {
  const runtime = createPlatformRuntime();
  const execution = runtime.execute(context);
  return {
    runtimeContext: execution.context,
    projection: execution.projection,
    runtimeProjections: execution.projections,
    platformDecision: execution.decision,
    trustGraph: execution.trustGraph,
    runtimeKernel: execution.runtime,
    runtimeIdentity: execution.runtime?.identity ? execution.runtime.identity() : execution.runtime,
    runtimeContracts: execution.contracts,
    runtimeState: execution.state,
    runtimeTimeline: execution.timeline,
    runtimeSignals: execution.signals,
    runtimeEvents: execution.eventLog,
    runtimeScheduler: execution.scheduler,
    runtimeProjectionStore: execution.projectionStore,
    runtimeHealth: runtime.health(),
    runtimeMetrics: runtime.metrics(),
    runtimeReplay: runtime.replay(),
    runtimeSnapshot: runtime.snapshot(),
  };
}

export function deriveRiderMission({
  ride,
  rideStatus,
  pickup,
  destination,
  evidence,
  receipt,
  historyCount,
  ...context
}) {
  const runtime = derivePlatformMission({
    ...context,
    rideStatus,
    pickup,
    destination,
    evidence,
    receipt,
    history: new Array(historyCount || 0).fill(null),
  });
  const status = upper(rideStatus);
  const phase =
    !ride || ["READY", "CANCELLED", "DECLINED"].includes(status)
      ? MISSION_PHASES.RIDER.BOOKING
      : ["ACCEPTED", "ARRIVED"].includes(status)
        ? MISSION_PHASES.RIDER.WAITING
        : ["STARTED", "IN_TRIP"].includes(status)
          ? MISSION_PHASES.RIDER.ACTIVE
          : MISSION_PHASES.RIDER.SETTLED;

  const route =
    phase === MISSION_PHASES.RIDER.BOOKING
      ? "Find demand"
      : phase === MISSION_PHASES.RIDER.WAITING
        ? "Passenger found"
        : phase === MISSION_PHASES.RIDER.ACTIVE
          ? "Navigate"
          : "Settlement";

  const assistant =
    phase === MISSION_PHASES.RIDER.BOOKING
      ? "High demand is likely around Docklands. Book now to improve pickup speed."
      : phase === MISSION_PHASES.RIDER.WAITING
        ? "Your driver is on the way. Keep notifications on for the next pickup update."
        : phase === MISSION_PHASES.RIDER.ACTIVE
          ? "Trip is live. Evidence and receipt will settle automatically after completion."
          : receipt
            ? "Settlement is complete. Your receipt and replay are ready if you need them."
            : "Ride state is synchronized. Refresh to check the latest backend status.";

  const primaryLabel =
    phase === MISSION_PHASES.RIDER.BOOKING
      ? "Request ride"
      : phase === MISSION_PHASES.RIDER.SETTLED
        ? "View receipt"
        : "Refresh status";

  const stageLabel =
    phase === MISSION_PHASES.RIDER.BOOKING
      ? "No Ride"
      : phase === MISSION_PHASES.RIDER.WAITING
        ? "Offer Received"
        : phase === MISSION_PHASES.RIDER.ACTIVE
          ? "Trip"
          : "Ready Again";

  return {
    phase,
    route,
    assistant,
    primaryLabel,
    stageLabel,
    trustLabel: evidence ? "Protected" : ride ? "Verified" : "Ready",
    missionTitle:
      phase === MISSION_PHASES.RIDER.BOOKING
        ? "Where to next?"
        : phase === MISSION_PHASES.RIDER.WAITING
          ? "Your driver is on the way"
          : phase === MISSION_PHASES.RIDER.ACTIVE
            ? "Trip in progress"
            : "Ride completed",
    missionSubtitle:
      phase === MISSION_PHASES.RIDER.BOOKING
        ? "Book fast, keep trust visible, and let the platform handle the rest."
        : phase === MISSION_PHASES.RIDER.WAITING
          ? `Pickup locked: ${pickup}`
          : phase === MISSION_PHASES.RIDER.ACTIVE
            ? `${pickup} → ${destination}`
            : "Receipt, replay, and evidence are available after completion.",
    summaryTone: phase === MISSION_PHASES.RIDER.ACTIVE ? "accent" : phase === MISSION_PHASES.RIDER.SETTLED ? "success" : "neutral",
    historyCount,
    platformDecision: runtime.platformDecision,
    trustGraph: runtime.trustGraph,
    runtimeContracts: runtime.runtimeContracts,
    runtimeKernel: runtime.runtimeKernel,
    runtimeIdentity: runtime.runtimeIdentity,
    runtimeProjections: runtime.runtimeProjections,
    runtimeTimeline: runtime.runtimeTimeline,
    runtimeSignals: runtime.runtimeSignals,
    runtimeScheduler: runtime.runtimeScheduler,
    runtimeProjectionStore: runtime.runtimeProjectionStore,
    runtimeHealth: runtime.runtimeHealth,
    runtimeMetrics: runtime.runtimeMetrics,
    runtimeReplay: runtime.runtimeReplay,
    runtimeCertification: runtime.runtimeCertification,
  };
}

export function deriveDriverMission({
  online,
  trip,
  tripStatus,
  ridesCount,
  displayName,
  pickup,
  destination,
  earningsAmount,
  ...context
}) {
  const runtime = derivePlatformMission({
    ...context,
    online,
    rideStatus: tripStatus,
    activeRideId: trip?.ride_id || null,
    pickup,
    destination,
  });
  const status = upper(tripStatus);
  const phase = !online
    ? MISSION_PHASES.DRIVER.OFFLINE
    : trip && ["STARTED", "IN_TRIP"].includes(status)
      ? MISSION_PHASES.DRIVER.ON_TRIP
      : ridesCount > 0
        ? MISSION_PHASES.DRIVER.READY
        : MISSION_PHASES.DRIVER.READY;

  const assistant =
    phase === MISSION_PHASES.DRIVER.OFFLINE
      ? "Go online when you’re ready. The queue will refresh and show the next best ride."
      : trip && ["ARRIVED"].includes(status)
        ? "You’ve arrived. Start the trip when the passenger is ready."
        : trip && ["STARTED", "IN_TRIP"].includes(status)
          ? "Trip is live. Keep navigation and trust evidence active until completion."
          : ridesCount > 0
            ? `You have ${ridesCount} assigned ride${ridesCount === 1 ? "" : "s"} ready to review.`
            : "Queue is clear. Refresh when you want the latest assigned ride snapshot.";

  const nextAction =
    phase === MISSION_PHASES.DRIVER.OFFLINE
      ? "Go online"
      : trip && ["ARRIVED"].includes(status)
        ? "Start trip"
        : trip && ["STARTED", "IN_TRIP"].includes(status)
          ? "Complete trip"
          : "Refresh queue";

  const missionTitle =
    phase === MISSION_PHASES.DRIVER.OFFLINE
      ? "Set yourself online"
      : trip && ["ARRIVED"].includes(status)
        ? "Arrived at pickup"
        : trip && ["STARTED", "IN_TRIP"].includes(status)
          ? "Trip in progress"
          : ridesCount > 0
            ? "Ride queue ready"
            : "Standing by";

  const missionSubtitle =
    phase === MISSION_PHASES.DRIVER.OFFLINE
      ? "Go online to begin receiving rides and move from standby to dispatch."
      : trip && ["STARTED", "IN_TRIP"].includes(status)
        ? `${pickup} → ${destination}`
        : ridesCount > 0
          ? "Assigned rides are waiting. Accept the next one when you’re ready."
          : "Refresh the queue for the latest assigned rides.";

  return {
    phase,
    assistant,
    nextAction,
    missionTitle,
    missionSubtitle,
    statusLabel: phase === MISSION_PHASES.DRIVER.OFFLINE ? "Offline" : phase === MISSION_PHASES.DRIVER.ON_TRIP ? "On trip" : ridesCount > 0 ? "Ready" : "Available",
    trustLabel: trip ? "Protected" : online ? "Verified" : "Ready",
    driverName: displayName,
    earningsAmount,
    platformDecision: runtime.platformDecision,
    trustGraph: runtime.trustGraph,
    runtimeContracts: runtime.runtimeContracts,
    runtimeKernel: runtime.runtimeKernel,
    runtimeIdentity: runtime.runtimeIdentity,
    runtimeProjections: runtime.runtimeProjections,
    runtimeTimeline: runtime.runtimeTimeline,
    runtimeSignals: runtime.runtimeSignals,
    runtimeScheduler: runtime.runtimeScheduler,
    runtimeProjectionStore: runtime.runtimeProjectionStore,
    runtimeHealth: runtime.runtimeHealth,
    runtimeMetrics: runtime.runtimeMetrics,
    runtimeReplay: runtime.runtimeReplay,
    runtimeCertification: runtime.runtimeCertification,
  };
}

export function deriveOperatorMission({ guards, activeRides, driversOnline, trustScore, ...context }) {
  const runtime = derivePlatformMission({
    ...context,
    guards,
    activeRides,
    driversOnline,
    trustScore,
  });
  const demandScore = Math.min(100, 42 + activeRides * 9 + driversOnline * 2);
  const demandLabel = demandScore >= 75 ? "HIGH" : demandScore >= 50 ? "RISING" : "NORMAL";
  const fatigueScore = Math.min(100, Math.max(0, activeRides * 7 - driversOnline * 3 + guards * 9));
  const paymentDelay = Math.min(100, Math.max(0, 2 + activeRides - Math.floor(driversOnline / 8)));

  const assistant =
    guards > 0
      ? `${guards} guard violation${guards === 1 ? "" : "s"} need attention. Open incidents first.`
      : activeRides > 0
        ? `Fleet is active with ${activeRides} live ride${activeRides === 1 ? "" : "s"} and ${driversOnline} driver${driversOnline === 1 ? "" : "s"} online.`
        : "Fleet is quiet. Refresh for the latest trust and replay state.";

  return {
    phase: MISSION_PHASES.OPERATOR.CONTROL,
    missionTitle: "Fleet Trust Control",
    missionSubtitle: "Operations, dispatch, evidence, and replay in one bounded control plane.",
    assistant,
    statusLabel: guards > 0 ? "Attention" : "Healthy",
    statusTone: guards > 0 ? "amber" : "success",
    demandLabel,
    demandScore,
    fatigueScore,
    paymentDelay,
    trustScore,
    platformDecision: runtime.platformDecision,
    trustGraph: runtime.trustGraph,
    runtimeContracts: runtime.runtimeContracts,
    runtimeKernel: runtime.runtimeKernel,
    runtimeIdentity: runtime.runtimeIdentity,
    runtimeTimeline: runtime.runtimeTimeline,
    runtimeSignals: runtime.runtimeSignals,
    runtimeHealth: runtime.runtimeHealth,
    runtimeMetrics: runtime.runtimeMetrics,
    runtimeReplay: runtime.runtimeReplay,
    runtimeCertification: runtime.runtimeCertification,
  };
}
