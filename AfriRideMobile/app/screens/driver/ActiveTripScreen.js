import React, { useState } from "react";
import { Text, TextInput, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import { completeRide, startRide } from "../../services/rideService";
import { theme } from "../../theme/theme";

export default function ActiveTripScreen() {
  const [rideId, setRideId] = useState("");
  const [driverId, setDriverId] = useState("D1");
  const [result, setResult] = useState(null);

  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Active Trip" subtitle="State transitions require backend confirmation." />
      <TextInput value={rideId} onChangeText={setRideId} placeholder="Ride ID" style={{ borderWidth: 1, borderColor: theme.colors.border, padding: 12 }} />
      <TextInput value={driverId} onChangeText={setDriverId} placeholder="Driver ID" style={{ borderWidth: 1, borderColor: theme.colors.border, padding: 12 }} />
      <AppButton title="Start Trip" onPress={async () => setResult(await startRide(rideId, { driver_id: driverId }))} />
      <AppButton title="Complete Trip" onPress={async () => setResult(await completeRide(rideId, { driver_id: driverId }))} />
      {result ? <Text>{JSON.stringify(result, null, 2)}</Text> : null}
    </View>
  );
}
