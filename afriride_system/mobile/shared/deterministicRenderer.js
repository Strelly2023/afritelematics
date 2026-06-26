import { stableCanonicalize } from "./canonicalize.js";
import { createSnapshotChecksum } from "./novarideStorage.js";
import { deriveReplayDetail, deriveReplayState, hasValue } from "./proofLayer.js";

function normalizeText(value, fallback = "—") {
  if (value === null || value === undefined) {
    return fallback;
  }

  const text = String(value).trim();
  return text.length > 0 ? text : fallback;
}

function compareStrings(left, right) {
  const leftText = String(left ?? "");
  const rightText = String(right ?? "");

  if (leftText < rightText) return -1;
  if (leftText > rightText) return 1;
  return 0;
}

function numberOr(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function normalizeForHash(value) {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeForHash(item));
  }

  if (value && typeof value === "object") {
    return Object.keys(value)
      .sort()
      .reduce((accumulator, key) => {
        accumulator[key] = normalizeForHash(value[key] === undefined ? null : value[key]);
        return accumulator;
      }, {});
  }

  return value === undefined ? null : value;
}

function parseTimestamp(value) {
  if (!value || typeof value !== "string") {
    return null;
  }

  const isoMatch = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/;
  if (!isoMatch.test(value)) {
    return null;
  }

  const timestamp = new Date(value);
  const millis = timestamp.getTime();
  return Number.isFinite(millis) ? millis : null;
}

function formatUtcTimestamp(value) {
  const millis = parseTimestamp(value);
  if (millis === null) {
    return "—";
  }

  return new Date(millis).toISOString().replace(".000Z", "Z");
}

function compareEvents(left, right) {
  const leftMillis = parseTimestamp(left.timestamp);
  const rightMillis = parseTimestamp(right.timestamp);

  if (leftMillis !== rightMillis) {
    if (leftMillis === null) return 1;
    if (rightMillis === null) return -1;
    return leftMillis - rightMillis;
  }

  const leftLabel = normalizeText(left.label, "");
  const rightLabel = normalizeText(right.label, "");
  if (leftLabel !== rightLabel) {
    return compareStrings(leftLabel, rightLabel);
  }

  const leftDetail = normalizeText(left.detail, "");
  const rightDetail = normalizeText(right.detail, "");
  if (leftDetail !== rightDetail) {
    return compareStrings(leftDetail, rightDetail);
  }

  const leftValue = normalizeText(left.value, "");
  const rightValue = normalizeText(right.value, "");
  if (leftValue !== rightValue) {
    return compareStrings(leftValue, rightValue);
  }

  const leftKey = eventFingerprint(left);
  const rightKey = eventFingerprint(right);
  return compareStrings(leftKey, rightKey);
}

function readReplayEvents(replay) {
  if (!replay || typeof replay !== "object") {
    return [];
  }

  const candidates = [
    replay.events,
    replay.timeline,
    replay.history,
    replay.entries,
    replay.steps,
    replay.proof?.events,
    replay.ledger_proof?.events,
    replay.replay?.events,
  ];

  for (const candidate of candidates) {
    if (Array.isArray(candidate) && candidate.length > 0) {
      return candidate;
    }
  }

  return [];
}

function canonicalizeEvent(event, index) {
  const timestamp = event?.timestamp ?? event?.local_timestamp ?? event?.time ?? event?.created_at ?? null;
  const label =
    event?.label ??
    event?.type ??
    event?.action ??
    event?.name ??
    event?.status ??
    `event-${index + 1}`;
  const detail = event?.detail ?? event?.message ?? event?.reason ?? event?.description ?? null;
  const value = hasValue(event?.value)
    ? event.value
    : hasValue(event?.result)
      ? event.result
      : hasValue(event?.status)
        ? event.status
        : null;

  return {
    index,
    id: normalizeText(event?.event_id ?? event?.id ?? event?.hash ?? `event-${index}`),
    label: normalizeText(label),
    detail: hasValue(detail) ? normalizeText(detail) : null,
    value: hasValue(value) ? normalizeText(value) : null,
    timestamp: hasValue(timestamp) ? normalizeText(timestamp) : null,
    timestamp_ms: parseTimestamp(timestamp),
    canonical: normalizeForHash({
      ...(event && typeof event === "object" ? event : {}),
    }),
  };
}

function eventFingerprint(event) {
  const canonical = event && typeof event === "object" && event.canonical !== undefined ? event.canonical : normalizeForHash(event);
  return JSON.stringify(canonical);
}

function collectReplaySnapshot(replay) {
  const canonicalEvents = readReplayEvents(replay).map(canonicalizeEvent);
  canonicalEvents.sort(compareEvents);

  return canonicalEvents;
}

function clampIndex(index, total) {
  if (total <= 0) {
    return 0;
  }

  return Math.max(0, Math.min(total - 1, index));
}

export function replayStateAt(replay, cursor = null) {
  const events = collectReplaySnapshot(replay);
  const total = events.length;

  if (total === 0) {
    const fallbackState = deriveReplayState(replay);
    return {
      cursor: 0,
      total,
      progress: 0,
      checkpointLabel: "Snapshot",
      asOf: null,
      status: fallbackState.status,
      tone: fallbackState.tone,
      replayState: fallbackState,
      replayDetail: deriveReplayDetail(replay),
      events: [],
      currentEvent: null,
      snapshotHash: createSnapshotChecksum({
        cursor: 0,
        total: 0,
        status: fallbackState.status,
        tone: fallbackState.tone,
        replayState: fallbackState,
        replayDetail: deriveReplayDetail(replay),
        events: [],
        currentEvent: null,
      }),
    };
  }

  let visibleEvents = events;
  let checkpointLabel = "Latest";
  let selectedCursor = total - 1;
  let asOf = events[events.length - 1]?.timestamp || null;

  if (typeof cursor === "number" && Number.isFinite(cursor)) {
    selectedCursor = clampIndex(Math.floor(cursor), total);
    visibleEvents = events.slice(0, selectedCursor + 1);
    checkpointLabel = `Event ${selectedCursor + 1}/${total}`;
    asOf = visibleEvents[visibleEvents.length - 1]?.timestamp || null;
  } else if (typeof cursor === "string" && cursor.trim()) {
    const trimmed = cursor.trim();
    const cursorMillis = parseTimestamp(trimmed);
    if (cursorMillis !== null) {
      visibleEvents = events.filter((event) => event.timestamp_ms === null || event.timestamp_ms <= cursorMillis);
      if (visibleEvents.length === 0) {
        visibleEvents = [events[0]];
      }
      selectedCursor = visibleEvents.length - 1;
      checkpointLabel = `As of ${formatUtcTimestamp(trimmed)}`;
      asOf = visibleEvents[visibleEvents.length - 1]?.timestamp || null;
    } else {
      const foundIndex = events.findIndex(
        (event) => event.id === trimmed || event.label === trimmed || event.value === trimmed,
      );
      if (foundIndex >= 0) {
        selectedCursor = foundIndex;
        visibleEvents = events.slice(0, foundIndex + 1);
        checkpointLabel = `Event ${foundIndex + 1}/${total}`;
        asOf = visibleEvents[visibleEvents.length - 1]?.timestamp || null;
      }
    }
  } else if (cursor && typeof cursor === "object") {
    if (Number.isFinite(Number(cursor.index))) {
      selectedCursor = clampIndex(Number(cursor.index), total);
      visibleEvents = events.slice(0, selectedCursor + 1);
      checkpointLabel = `Event ${selectedCursor + 1}/${total}`;
      asOf = visibleEvents[visibleEvents.length - 1]?.timestamp || null;
    } else if (cursor.timestamp) {
      return replayStateAt(replay, cursor.timestamp);
    }
  }

  const lastEvent = visibleEvents[visibleEvents.length - 1] || null;
  const fullReplayState = deriveReplayState(replay);
  const fullReplayDetail = deriveReplayDetail(replay);
  const rawStatus = normalizeText(lastEvent?.label || lastEvent?.value || fullReplayState.status, fullReplayState.status);
  const statusText = /complete|settle|verified|done|closed/i.test(rawStatus)
    ? "Verified"
    : /start|trip|live|active|in progress/i.test(rawStatus)
      ? "In progress"
      : /arriv/i.test(rawStatus)
        ? "Arrived"
        : /invalid|fail|tamper|reject/i.test(rawStatus)
          ? "Invalid"
          : rawStatus;
  const tone =
    /invalid|fail|tamper|reject/i.test(statusText)
      ? "danger"
      : /verified|complete|settle|done|closed/i.test(statusText)
        ? "success"
        : /arriv/i.test(statusText)
          ? "amber"
          : fullReplayState.tone;

  const snapshot = {
    cursor: selectedCursor,
    total,
    progress: total > 0 ? visibleEvents.length / total : 0,
    checkpointLabel,
    asOf,
    status: statusText,
    tone,
    replayState: fullReplayState,
    replayDetail: fullReplayDetail,
    currentEvent: lastEvent
      ? {
          id: lastEvent.id,
          label: lastEvent.label,
          detail: lastEvent.detail,
          value: lastEvent.value,
          timestamp: lastEvent.timestamp,
          canonical: lastEvent.canonical,
        }
      : null,
    events: visibleEvents.map((event) => ({
      id: event.id,
      label: event.label,
      detail: event.detail,
      value: event.value,
      timestamp: event.timestamp,
      canonical: event.canonical,
    })),
  };

  return {
    ...snapshot,
    snapshotHash: createSnapshotChecksum({
      checkpointLabel: snapshot.checkpointLabel,
      asOf: snapshot.asOf,
      cursor: snapshot.cursor,
      total: snapshot.total,
      status: snapshot.status,
      tone: snapshot.tone,
      replayState: snapshot.replayState,
      replayDetail: snapshot.replayDetail,
      currentEvent: snapshot.currentEvent,
      events: visibleEvents.map((event) => event.canonical),
    }),
  };
}

function deriveTrustScore(canonicalState, replaySnapshot) {
  const candidates = [
    canonicalState?.trustScore,
    canonicalState?.confidence,
    canonicalState?.mission?.platformDecision?.confidence,
    canonicalState?.mission?.trustScore,
  ];

  const base = candidates.find((value) => Number.isFinite(Number(value)));
  let score = Number.isFinite(Number(base)) ? Number(base) : 0;

  if (replaySnapshot?.replayState?.verified === true || replaySnapshot?.replayState?.status === "Verified") {
    score += 5;
  }

  if (canonicalState?.receipt) {
    score += 3;
  }

  if (canonicalState?.replay) {
    score += 2;
  }

  if (replaySnapshot?.replayState?.verified === false || replaySnapshot?.replayState?.status === "Invalid") {
    score -= 35;
  }

  if (replaySnapshot?.total > 0) {
    score += Math.min(5, replaySnapshot.total);
  }

  return Math.max(0, Math.min(100, Math.round(score)));
}

function buildProofMode(replaySnapshot, canonicalState) {
  const replayState = replaySnapshot?.replayState || deriveReplayState(canonicalState?.replay);
  const hasReceipt = Boolean(canonicalState?.receipt);

  if (replayState.verified === false || replayState.status === "Invalid") {
    return {
      label: "❌ Invalid",
      tone: "danger",
      reason: replaySnapshot?.replayDetail || "Canonical replay failed verification",
    };
  }

  if (replayState.verified === true && hasReceipt) {
    return {
      label: "🔐 Verified",
      tone: "success",
      reason: replaySnapshot?.replayDetail || "Canonical state verified",
    };
  }

  if (hasReceipt || replaySnapshot?.total > 0) {
    return {
      label: "⏳ Verifying",
      tone: "amber",
      reason: replaySnapshot?.replayDetail || "Deterministic state is loading",
    };
  }

  return {
    label: "Loaded",
    tone: "accent",
    reason: "Canonical snapshot available",
  };
}

export function buildDeterministicUiSnapshot(canonicalState = {}, options = {}) {
  const replay = canonicalState.replay || canonicalState.replayHealth || canonicalState.ledgerReplay || null;
  const receipt = canonicalState.receipt || canonicalState.evidence || canonicalState.proofReceipt || null;
  const replayCursor =
    options.cursor ??
    canonicalState.replayCursor ??
    canonicalState.snapshotCursor ??
    canonicalState.selectedCursor ??
    null;
  const replaySnapshot = replayStateAt(replay, replayCursor);
  const proofMode = buildProofMode(replaySnapshot, { ...canonicalState, replay, receipt });
  const trustScore = deriveTrustScore({ ...canonicalState, replay, receipt }, replaySnapshot);
  const replayHash =
    canonicalState.replayHash ||
    replay?.replay_hash ||
    replay?.replayHash ||
    replay?.hash ||
    null;
  const receiptHash =
    canonicalState.receiptHash ||
    receipt?.receipt_hash ||
    receipt?.receiptHash ||
    receipt?.hash ||
    null;
  const orderedEvents = [...replaySnapshot.events].sort((left, right) => {
    const leftMillis = parseTimestamp(left.timestamp);
    const rightMillis = parseTimestamp(right.timestamp);

    if (leftMillis !== rightMillis) {
      if (leftMillis === null) return 1;
      if (rightMillis === null) return -1;
      return leftMillis - rightMillis;
    }

    const leftId = normalizeText(left.id, "");
    const rightId = normalizeText(right.id, "");
    if (leftId !== rightId) {
      return compareStrings(leftId, rightId);
    }

    const leftLabel = normalizeText(left.label, "");
    const rightLabel = normalizeText(right.label, "");
    if (leftLabel !== rightLabel) {
      return compareStrings(leftLabel, rightLabel);
    }

    const leftKey = eventFingerprint(left);
    const rightKey = eventFingerprint(right);
    return compareStrings(leftKey, rightKey);
  });

  const checkpointCount = orderedEvents.length || 0;
  const checkpoints = Array.from({ length: checkpointCount }, (_, index) => ({
    index,
    label: `Event ${index + 1}`,
    timestamp: orderedEvents[index]?.timestamp || null,
  }));

  const cursorEvent = replaySnapshot.events[replaySnapshot.cursor] || null;
  const normalizedCursor = cursorEvent
    ? orderedEvents.findIndex((event) => eventFingerprint(event) === eventFingerprint(cursorEvent))
    : -1;
  const activeCursor = normalizedCursor >= 0 ? normalizedCursor : Math.min(replaySnapshot.cursor, Math.max(0, orderedEvents.length - 1));

  const timeline = orderedEvents.length
    ? orderedEvents.map((event, index) => ({
        label: event.label,
        detail: event.detail || event.timestamp || `Event-${event.id || index}`,
        value: event.value || event.timestamp || null,
        done: index <= activeCursor,
      }))
    : [
        {
          label: proofMode.label,
          detail: replaySnapshot.replayDetail,
          value: replaySnapshot.checkpointLabel,
          done: true,
        },
      ];

  const ui = {
    title: normalizeText(canonicalState.title, "Proof mode"),
    subtitle: normalizeText(canonicalState.subtitle, "Canonical state rendered deterministically"),
    status: replaySnapshot.status,
    trustScore,
    checkpointLabel: replaySnapshot.checkpointLabel,
    asOf: replaySnapshot.asOf,
    snapshotHash: replaySnapshot.snapshotHash,
    replayHash,
    receiptHash,
    proofMode,
    replayState: replaySnapshot.replayState,
    replayDetail: replaySnapshot.replayDetail,
    currentEvent: orderedEvents[activeCursor] || replaySnapshot.currentEvent,
    timeline,
    checkpoints,
  };

  const projectionForHash = {
    title: ui.title,
    subtitle: ui.subtitle,
    status: ui.status,
    trustScore: ui.trustScore,
    checkpointLabel: ui.checkpointLabel,
    asOf: ui.asOf,
    replayHash: ui.replayHash,
    receiptHash: ui.receiptHash,
    proofMode: ui.proofMode,
    replayState: ui.replayState,
    replayDetail: ui.replayDetail,
    currentEvent: ui.currentEvent,
    cursor: ui.currentEvent ? ui.currentEvent.timestamp || ui.currentEvent.id || ui.checkpointLabel : ui.checkpointLabel,
  };

  return {
    ...ui,
    uiHash: createSnapshotChecksum(
      stableCanonicalize(normalizeForHash(projectionForHash)),
    ),
  };
}

export function formatCheckpointLabel(snapshot) {
  if (!snapshot) {
    return "Snapshot";
  }

  const label = snapshot.checkpointLabel || "Snapshot";
  const asOf = snapshot.asOf ? ` · ${formatUtcTimestamp(snapshot.asOf)}` : "";
  return `${label}${asOf}`;
}
