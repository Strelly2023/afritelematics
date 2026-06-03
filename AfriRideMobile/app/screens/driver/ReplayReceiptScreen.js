import React, { useState } from "react";
import { TextInput, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import ReplayReceiptCard from "../../components/ReplayReceiptCard";
import { getReplayReceipt } from "../../services/replayService";
import { theme } from "../../theme/theme";

export default function ReplayReceiptScreen() {
  const [rideId, setRideId] = useState("");
  const [replay, setReplay] = useState(null);

  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Replay Receipt" subtitle="Replay status is backend-issued only." />
      <TextInput value={rideId} onChangeText={setRideId} placeholder="Ride ID" style={{ borderWidth: 1, borderColor: theme.colors.border, padding: 12 }} />
      <AppButton title="Load Replay Receipt" onPress={async () => setReplay(await getReplayReceipt(rideId))} />
      <ReplayReceiptCard replay={replay} />
    </View>
  );
}
