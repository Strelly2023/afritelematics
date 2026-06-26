import { verifyReplay } from "./verificationLayer.js";

export const hasValue = (v) => v !== null && v !== undefined;

export const safeArray = (v) => (Array.isArray(v) ? v : []);

export function extractNumber(value, fallback = 0) {
  if (!hasValue(value)) {
    return fallback;
  }

  if (typeof value === "number") {
    return Number.isFinite(value) ? value : fallback;
  }

  if (typeof value === "string") {
    const parsed = parseFloat(value.replace(/%/g, "").trim());
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  return fallback;
}

export function formatCount(value, fallback = "0") {
  const numeric = extractNumber(value, Number.NaN);
  if (!Number.isFinite(numeric)) {
    return fallback;
  }

  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(numeric);
}

export function formatMoney(value, fallback = "0") {
  if (!hasValue(value) || value === "") {
    return fallback;
  }

  const formatIntegerWithGrouping = (text) =>
    text.replace(/\B(?=(\d{3})+(?!\d))/g, ",");

  if (typeof value === "string") {
    const cleaned = value.trim().replace(/,/g, "");
    if (!/^-?\d+(\.\d+)?$/.test(cleaned)) {
      return fallback;
    }

    const negative = cleaned.startsWith("-");
    const unsigned = negative ? cleaned.slice(1) : cleaned;
    const [integerPart, decimalPart] = unsigned.split(".");
    const grouped = formatIntegerWithGrouping(integerPart);
    const prefix = negative ? "-" : "";

    return `${prefix}${grouped}${decimalPart !== undefined ? `.${decimalPart}` : ""}`;
  }

  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return fallback;
  }

  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(numeric);
  } catch {
    return `$${numeric.toFixed(2)}`;
  }
}

export function formatHash(value, fallback = "—", visible = 8) {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  let text;

  if (typeof value === "string") {
    text = value.trim();
  } else if (typeof ArrayBuffer !== "undefined" && value instanceof ArrayBuffer) {
    text = Array.from(new Uint8Array(value))
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");
  } else if (typeof ArrayBuffer !== "undefined" && ArrayBuffer.isView?.(value)) {
    const bytes = new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
    text = Array.from(bytes)
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");
  } else {
    text = String(value).trim();
  }

  if (!text) {
    return fallback;
  }

  if (text.length <= visible * 2 + 1) {
    return text;
  }

  return `${text.slice(0, visible)}…${text.slice(-visible)}`;
}

export function deriveReplayState(replay) {
  if (!replay) {
    return {
      status: "Pending",
      tone: "amber",
      verified: false,
    };
  }

  if (replay.replay_valid === true) {
    return {
      status: "Verified",
      tone: "success",
      verified: true,
    };
  }

  if (replay.replay_valid === false) {
    return {
      status: "Invalid",
      tone: "danger",
      verified: false,
    };
  }

  return {
    status: "Loaded",
    tone: "accent",
    verified: false,
  };
}

export function deriveReplayDetail(replay) {
  if (!replay) {
    return "Canonical reconstruction";
  }

  if (hasValue(replay.failures)) {
    return `${formatCount(replay.failures)} failures`;
  }

  if (hasValue(replay.event_count)) {
    return `${formatCount(replay.event_count)} events`;
  }

  return "Canonical reconstruction";
}

export function deriveHashes(hashes) {
  return safeArray(hashes).filter((item) => item && item.label && hasValue(item.value));
}

export function deriveVerifiedState(replay) {
  const result = verifyReplay(replay);

  if (result.valid === true) {
    return {
      label: "✅ Verified",
      tone: "success",
      valid: true,
      reason: result.reason,
    };
  }

  if (result.valid === false) {
    return {
      label: "❌ Invalid",
      tone: "danger",
      valid: false,
      reason: result.reason,
    };
  }

  return {
    label: "⏳ Verifying",
    tone: "amber",
    valid: null,
    reason: result.reason,
  };
}

export function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function validateReplayEvent(event) {
  if (!isPlainObject(event)) return false;
  return (
    typeof event.id === "string" &&
    typeof event.timestamp === "string" &&
    typeof event.label === "string"
  );
}

export function validateReplayPayload(payload) {
  if (!isPlainObject(payload)) return false;
  if (payload.events !== undefined && !Array.isArray(payload.events)) return false;
  if (Array.isArray(payload.events) && !payload.events.every(validateReplayEvent)) return false;
  return true;
}

export function validateZkBundle(bundle) {
  if (!isPlainObject(bundle)) return false;
  const publicInputs = bundle.public_inputs;
  if (!isPlainObject(publicInputs)) return false;
  return typeof publicInputs.receipt_hash === "string" && publicInputs.receipt_hash.length > 0;
}

export function validateQrPayload(payload) {
  if (!isPlainObject(payload)) return false;
  if (payload.type !== "novatrust-qr-proof" && payload.type !== "novatrust-zk-qr") {
    return false;
  }
  if (typeof payload.qr_hash !== "string" || payload.qr_hash.length === 0) {
    return false;
  }
  return true;
}
