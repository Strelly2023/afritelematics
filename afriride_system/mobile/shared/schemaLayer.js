export function isBoolean(value) {
  return typeof value === "boolean";
}

export function normalizeBoolean(value) {
  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    const normalized = value.toLowerCase().trim();
    if (normalized === "true") {
      return true;
    }
    if (normalized === "false") {
      return false;
    }
  }

  return undefined;
}

export function normalizeReplayVerdict(input) {
  const verdict = normalizeBoolean(input?.replay_valid);
  if (verdict !== undefined) {
    return verdict;
  }

  return normalizeBoolean(input?.replay_verified);
}

export function isNumberLike(value) {
  if (typeof value === "number") {
    return Number.isFinite(value);
  }

  if (typeof value === "string") {
    const parsed = Number.parseFloat(value.replace(/%/g, "").trim());
    return Number.isFinite(parsed);
  }

  return false;
}

export function validateReplay(input) {
  if (!input || typeof input !== "object") {
    return null;
  }

  const replay = {};

  replay.replay_valid = normalizeReplayVerdict(input);

  if (isNumberLike(input.event_count)) {
    replay.event_count = Number(input.event_count);
  }

  if (isNumberLike(input.failures)) {
    replay.failures = Number(input.failures);
  }

  if (isNumberLike(input.confidence)) {
    replay.confidence = Number(input.confidence);
  } else {
    replay.confidence = 0;
  }

  return replay;
}
