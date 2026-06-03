import React from "react";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import RiderHomeScreen from "../screens/rider/RiderHomeScreen";
import RequestRideScreen from "../screens/rider/RequestRideScreen";
import ActiveRideScreen from "../screens/rider/ActiveRideScreen";
import RideHistoryScreen from "../screens/rider/RideHistoryScreen";
import { ROUTES } from "../constants/routes";

const Stack = createNativeStackNavigator();

export default function RiderNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name={ROUTES.RIDER_HOME} component={RiderHomeScreen} />
      <Stack.Screen name={ROUTES.REQUEST_RIDE} component={RequestRideScreen} />
      <Stack.Screen name={ROUTES.ACTIVE_RIDE} component={ActiveRideScreen} />
      <Stack.Screen name={ROUTES.RIDE_HISTORY} component={RideHistoryScreen} />
    </Stack.Navigator>
  );
}
