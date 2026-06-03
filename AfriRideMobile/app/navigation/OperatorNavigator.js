import React from "react";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import OperatorDashboardScreen from "../screens/operator/OperatorDashboardScreen";
import ReplayMonitorScreen from "../screens/operator/ReplayMonitorScreen";
import EvidenceViewerScreen from "../screens/operator/EvidenceViewerScreen";
import { ROUTES } from "../constants/routes";

const Stack = createNativeStackNavigator();

export default function OperatorNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name={ROUTES.DASHBOARD} component={OperatorDashboardScreen} />
      <Stack.Screen name={ROUTES.REPLAY_MONITOR} component={ReplayMonitorScreen} />
      <Stack.Screen name={ROUTES.EVIDENCE_VIEWER} component={EvidenceViewerScreen} />
    </Stack.Navigator>
  );
}
