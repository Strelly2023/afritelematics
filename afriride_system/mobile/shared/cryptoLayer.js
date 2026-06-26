import { stableCanonicalize, stableStringify } from "./canonicalize.js";
import { sha256Hex } from "./novarideStorage.js";
import { toUtf8Bytes } from "./utf8.js";

function normalizeReplayHash(replay) {
  return replay?.replay_hash || replay?.replayHash || replay?.hash || null;
}

function canonicalReplaySummary(replay) {
  if (!replay || typeof replay !== "object") {
    return null;
  }

  return {
    ride_id: replay.ride_id ?? null,
    status: replay.status ?? null,
    assigned_driver: replay.assigned_driver ?? null,
    passenger_id: replay.passenger_id ?? null,
    transitions: Array.isArray(replay.transitions) ? replay.transitions : [],
    ordered: Boolean(replay.ordered),
    hash_chain_verified: Boolean(replay.hash_chain_verified),
    invariant_violations: Array.isArray(replay.invariant_violations) ? replay.invariant_violations : [],
    terminal_event_hash: replay.terminal_event_hash ?? null,
    authority_hash: replay.authority?.authority_hash ?? replay.authority_hash ?? null,
  };
}

function canonicalReplayEvents(replay) {
  const events = Array.isArray(replay?.events)
    ? replay.events
    : Array.isArray(replay?.eventLog)
      ? replay.eventLog
      : Array.isArray(replay?.trace_events)
        ? replay.trace_events
        : Array.isArray(replay?.canonical_events)
          ? replay.canonical_events
          : null;

  return events && events.length > 0 ? events : null;
}

function hasMeaningfulSummary(summary) {
  if (!summary) {
    return false;
  }

  return (
    summary.ride_id !== null ||
    summary.status !== null ||
    summary.assigned_driver !== null ||
    summary.passenger_id !== null ||
    (Array.isArray(summary.transitions) && summary.transitions.length > 0) ||
    summary.terminal_event_hash !== null ||
    summary.authority_hash !== null ||
    summary.ordered === true ||
    summary.hash_chain_verified === true ||
    (Array.isArray(summary.invariant_violations) && summary.invariant_violations.length > 0)
  );
}

async function digestText(text) {
  const normalized = String(text ?? "");

  if (globalThis.crypto?.subtle?.digest) {
    const bytes = toUtf8Bytes(normalized);
    const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest))
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");
  }

  return sha256Hex(normalized);
}

export async function computeReplayHash(replay) {
  const summary = canonicalReplaySummary(replay);
  if (hasMeaningfulSummary(summary)) {
    return digestText(stableStringify(stableCanonicalize(summary)));
  }

  const events = canonicalReplayEvents(replay);
  if (events) {
    return digestText(stableStringify(stableCanonicalize(events)));
  }

  return null;
}

export async function verifyReplayIntegrity(replay) {
  const expected = normalizeReplayHash(replay);
  if (!expected) {
    return {
      valid: false,
      level: "untrusted",
      reason: "Missing replay hash (integrity unverifiable)",
      expected: null,
      computed: null,
    };
  }

  const computed = await computeReplayHash(replay);
  if (!computed) {
    return {
      valid: null,
      reason: "Cannot compute replay hash",
      expected,
      computed: null,
    };
  }

  if (computed === expected) {
    return {
      valid: true,
      reason: "Hash verified",
      expected,
      computed,
    };
  }

  return {
    valid: false,
    reason: "Hash mismatch (tampering detected)",
    expected,
    computed,
  };
}

function base64UrlDecode(value) {
  const normalized = String(value ?? "").replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);

  if (typeof globalThis.atob === "function") {
    const binary = globalThis.atob(padded);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    return bytes;
  }

  if (typeof Buffer !== "undefined" && typeof Buffer.from === "function") {
    return new Uint8Array(Buffer.from(padded, "base64"));
  }

  return new Uint8Array();
}

export async function verifySignature(publicKey, message, signature) {
  if (!globalThis.crypto?.subtle?.verify || !publicKey || !signature) {
    return false;
  }

  try {
    const data = toUtf8Bytes(String(message ?? ""));
    const sigBuffer = base64UrlDecode(signature);

    if (publicKey?.kind === "jwk" || publicKey?.jwk) {
      const key = await globalThis.crypto.subtle.importKey(
        "jwk",
        publicKey.value || publicKey.jwk || publicKey,
        { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
        true,
        ["verify"],
      );

      return await globalThis.crypto.subtle.verify(
        { name: "RSASSA-PKCS1-v1_5" },
        key,
        sigBuffer,
        data,
      );
    }

    return await globalThis.crypto.subtle.verify(
      { name: "RSASSA-PKCS1-v1_5" },
      publicKey,
      sigBuffer,
      data,
    );
  } catch {
    return false;
  }
}

export async function performCryptoVerification(replay) {
  const hashCheck = await verifyReplayIntegrity(replay);

  if (hashCheck.valid === false) {
    return {
      valid: false,
      level: hashCheck.level || "critical",
      reason: hashCheck.reason,
      expectedHash: hashCheck.expected,
      computedHash: hashCheck.computed,
    };
  }

  if (hashCheck.valid === true) {
    return {
      valid: true,
      level: "cryptographic",
      reason: "Replay verified cryptographically",
      expectedHash: hashCheck.expected,
      computedHash: hashCheck.computed,
    };
  }

  return {
    valid: null,
    level: "unknown",
    reason: hashCheck.reason,
    expectedHash: hashCheck.expected,
    computedHash: hashCheck.computed,
  };
}
