import React from "react";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import RiderHomeScreen from "../screens/rider/RiderHomeScreen";
import RequestRideScreen from "../screens/rider/RequestRideScreen";
import ActiveRideScreen from "../screens/rider/ActiveRideScreen";
import RideHistoryScreen from "../screens/rider/RideHistoryScreen";
import NovaPayHomeScreen from "../screens/afripay/AfriPayHomeScreen";
import NovaPaySendScreen from "../screens/afripay/AfriPaySendScreen";
import NovaPayTreasuryScreen from "../screens/afripay/AfriPayTreasuryScreen";
import NovaPayAuditScreen from "../screens/afripay/AfriPayAuditScreen";
import { ROUTES } from "../constants/routes";

const Stack = createNativeStackNavigator();

export default function RiderNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name={ROUTES.RIDER_HOME} component={RiderHomeScreen} />
      <Stack.Screen name={ROUTES.REQUEST_RIDE} component={RequestRideScreen} />
      <Stack.Screen name={ROUTES.ACTIVE_RIDE} component={ActiveRideScreen} />
      <Stack.Screen name={ROUTES.RIDE_HISTORY} component={RideHistoryScreen} />
      <Stack.Screen name={ROUTES.AFRIPAY_HOME} component={NovaPayHomeScreen} options={{ title: "NovaPay" }} />
      <Stack.Screen name={ROUTES.AFRIPAY_SEND} component={NovaPaySendScreen} options={{ title: "Send Money" }} />
      <Stack.Screen name={ROUTES.AFRIPAY_TREASURY} component={NovaPayTreasuryScreen} options={{ title: "Treasury" }} />
      <Stack.Screen name={ROUTES.AFRIPAY_AUDIT} component={NovaPayAuditScreen} options={{ title: "Audit Proofs" }} />
    </Stack.Navigator>
  );
}
