import React from "react";
import { View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import { ROUTES } from "../../constants/routes";
import { theme } from "../../theme/theme";

export default function DriverHomeScreen({ navigation }) {
  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Driver" subtitle="Act on assigned backend ride state." />
      <AppButton title="Assigned Ride" onPress={() => navigation.navigate(ROUTES.ASSIGNED_RIDE)} />
      <AppButton title="Active Trip" onPress={() => navigation.navigate(ROUTES.ACTIVE_TRIP)} />
      <AppButton title="Earnings" onPress={() => navigation.navigate(ROUTES.EARNINGS)} />
      <AppButton title="Replay Receipt" onPress={() => navigation.navigate(ROUTES.REPLAY_RECEIPT)} />
    </View>
  );
}
