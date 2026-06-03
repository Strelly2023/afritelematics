import React, { useState } from "react";
import { Text, TextInput, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import { acceptRide } from "../../services/rideService";
import { theme } from "../../theme/theme";

export default function AssignedRideScreen() {
  const [rideId, setRideId] = useState("");
  const [driverId, setDriverId] = useState("D1");
  const [result, setResult] = useState(null);

  async function accept() {
    setResult(await acceptRide(rideId, { driver_id: driverId }));
  }

  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Assigned Ride" subtitle="Accept request through backend contract." />
      <TextInput value={rideId} onChangeText={setRideId} placeholder="Ride ID" style={{ borderWidth: 1, borderColor: theme.colors.border, padding: 12 }} />
      <TextInput value={driverId} onChangeText={setDriverId} placeholder="Driver ID" style={{ borderWidth: 1, borderColor: theme.colors.border, padding: 12 }} />
      <AppButton title="Accept Ride" onPress={accept} />
      {result ? <Text>{JSON.stringify(result, null, 2)}</Text> : null}
    </View>
  );
}
