import React, { useState } from "react";
import { Text, TextInput, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import StatusBadge from "../../components/StatusBadge";
import { getRideStatus } from "../../services/rideService";
import { useRide } from "../../state/RideContext";
import { theme } from "../../theme/theme";

export default function ActiveRideScreen() {
  const { activeRide, setActiveRide } = useRide();
  const [rideId, setRideId] = useState(activeRide?.ride_id || "");

  async function refresh() {
    const response = await getRideStatus(rideId);
    const ride = response.data || response;
    setActiveRide(ride);
  }

  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Active Ride" subtitle="Displays backend-confirmed ride state." />
      <TextInput
        value={rideId}
        onChangeText={setRideId}
        placeholder="Ride ID"
        style={{ borderWidth: 1, borderColor: theme.colors.border, padding: 12 }}
      />
      <AppButton title="Refresh Status" onPress={refresh} />
      {activeRide?.status ? <StatusBadge label={activeRide.status} /> : null}
      <Text>{activeRide ? JSON.stringify(activeRide, null, 2) : "No active ride loaded."}</Text>
    </View>
  );
}
