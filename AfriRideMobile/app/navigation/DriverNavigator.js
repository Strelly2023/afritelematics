import React from "react";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import DriverHomeScreen from "../screens/driver/DriverHomeScreen";
import AssignedRideScreen from "../screens/driver/AssignedRideScreen";
import ActiveTripScreen from "../screens/driver/ActiveTripScreen";
import EarningsScreen from "../screens/driver/EarningsScreen";
import ReplayReceiptScreen from "../screens/driver/ReplayReceiptScreen";
import { ROUTES } from "../constants/routes";

const Stack = createNativeStackNavigator();

export default function DriverNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name={ROUTES.DRIVER_HOME} component={DriverHomeScreen} />
      <Stack.Screen name={ROUTES.ASSIGNED_RIDE} component={AssignedRideScreen} />
      <Stack.Screen name={ROUTES.ACTIVE_TRIP} component={ActiveTripScreen} />
      <Stack.Screen name={ROUTES.EARNINGS} component={EarningsScreen} />
      <Stack.Screen name={ROUTES.REPLAY_RECEIPT} component={ReplayReceiptScreen} />
    </Stack.Navigator>
  );
}
