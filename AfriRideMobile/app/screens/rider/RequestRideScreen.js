import React, { useState } from "react";
import { Text, TextInput, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import { requestRide } from "../../services/rideService";
import { useRide } from "../../state/RideContext";
import { theme } from "../../theme/theme";

export default function RequestRideScreen() {
  const [riderId, setRiderId] = useState("R1");
  const [result, setResult] = useState(null);
  const { setActiveRide } = useRide();

  async function submit() {
    const response = await requestRide({
      passenger_id: riderId,
      pickup: "Pilot pickup",
      destination: "Pilot destination",
    });
    const ride = response.data || response;
    setResult(ride);
    setActiveRide(ride);
  }

  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Request Ride" subtitle="Request is submitted to backend authority." />
      <TextInput
        value={riderId}
        onChangeText={setRiderId}
        placeholder="Rider ID"
        style={{ borderWidth: 1, borderColor: theme.colors.border, padding: 12 }}
      />
      <AppButton title="Submit Request" onPress={submit} />
      {result ? <Text>{JSON.stringify(result, null, 2)}</Text> : null}
    </View>
  );
}
