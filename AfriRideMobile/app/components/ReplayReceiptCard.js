import React from "react";
import { Text } from "react-native";
import AppCard from "./AppCard";
import StatusBadge from "./StatusBadge";
import { replayStatusLabel } from "../utils/replayStatus";

export default function ReplayReceiptCard({ replay }) {
  const label = replayStatusLabel(replay);
  return (
    <AppCard>
      <StatusBadge label={label} tone={label === "VERIFIED" ? "success" : "danger"} />
      <Text>Replay ID: {replay?.replay_id || "Not issued"}</Text>
      <Text>Replay hash: {replay?.replay_hash || "Not available"}</Text>
    </AppCard>
  );
}
