export function replayStatusLabel(replay) {
  if (!replay) return "PENDING";
  return replay.replay_verified || replay.status === "PASS" ? "VERIFIED" : "INVALID";
}
