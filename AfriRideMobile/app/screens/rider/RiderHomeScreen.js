import React from "react";
import { View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import { ROUTES } from "../../constants/routes";
import { theme } from "../../theme/theme";

export default function RiderHomeScreen({ navigation }) {
  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Rider" subtitle="Request and observe backend-confirmed rides." />
      <AppButton title="Request Ride" onPress={() => navigation.navigate(ROUTES.REQUEST_RIDE)} />
      <AppButton title="Active Ride" onPress={() => navigation.navigate(ROUTES.ACTIVE_RIDE)} />
      <AppButton title="Ride History" onPress={() => navigation.navigate(ROUTES.RIDE_HISTORY)} />
    </View>
  );
}
