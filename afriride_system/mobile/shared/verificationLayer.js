import { validateReplay } from "./schemaLayer.js";
import { performCryptoVerification } from "./cryptoLayer.js";

export function verifyReplay(rawReplay) {
  const replay = validateReplay(rawReplay);

  if (!replay) {
    return {
      valid: null,
      reason: "Missing replay",
      replay: null,
    };
  }

  if (replay.replay_valid === true) {
    return {
      valid: true,
      reason: "Replay verified",
      replay,
    };
  }

  if (replay.replay_valid === false) {
    return {
      valid: false,
      reason: "Replay marked invalid",
      replay,
    };
  }

  if (replay.event_count !== undefined && replay.event_count < 0) {
    return {
      valid: false,
      reason: "Negative event count",
      replay,
    };
  }

  if (replay.failures !== undefined && replay.failures > 0) {
    return {
      valid: null,
      reason: "Replay has minor inconsistencies",
      replay,
    };
  }

  return {
    valid: null,
    reason: "Replay incomplete",
    replay,
  };
}

export function verifyReplayFromNormalized(replay) {
  if (!replay) {
    return {
      valid: null,
      reason: "Missing replay",
      replay: null,
    };
  }

  if (replay.replay_valid === true) {
    return {
      valid: true,
      reason: "Replay verified",
      replay,
    };
  }

  if (replay.replay_valid === false) {
    return {
      valid: false,
      reason: "Replay marked invalid",
      replay,
    };
  }

  if (replay.event_count !== undefined && replay.event_count < 0) {
    return {
      valid: false,
      reason: "Negative event count",
      replay,
    };
  }

  if (replay.failures !== undefined && replay.failures > 0) {
    return {
      valid: null,
      reason: "Replay has minor inconsistencies",
      replay,
    };
  }

  return {
    valid: null,
    reason: "Replay incomplete",
    replay,
  };
}

export async function verifyReplayFull(replay) {
  const logical = verifyReplayFromNormalized(replay);
  const crypto = await performCryptoVerification(replay);

  if (crypto.valid === false) {
    return {
      valid: false,
      level: "tampered",
      reason: crypto.reason,
      logical,
      crypto,
    };
  }

  if (logical.valid === false) {
    return {
      valid: false,
      level: "logical",
      reason: logical.reason,
      logical,
      crypto,
    };
  }

  if (logical.valid === true && crypto.valid === true) {
    return {
      valid: true,
      level: "secure",
      reason: "Fully verified",
      logical,
      crypto,
    };
  }

  return {
    valid: null,
    level: "partial",
    reason: logical.reason || crypto.reason,
    logical,
    crypto,
  };
}
