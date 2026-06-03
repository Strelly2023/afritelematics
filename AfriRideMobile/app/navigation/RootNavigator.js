import React, { useContext } from "react";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import SplashScreen from "../screens/splash/SplashScreen";
import AuthNavigator from "./AuthNavigator";
import RoleSelectionScreen from "../screens/role/RoleSelectionScreen";
import RiderNavigator from "./RiderNavigator";
import DriverNavigator from "./DriverNavigator";
import OperatorNavigator from "./OperatorNavigator";
import { AuthContext } from "../state/AuthContext";
import { RoleContext } from "../state/RoleContext";
import { ROLES } from "../constants/roles";
import { ROUTES } from "../constants/routes";

const Stack = createNativeStackNavigator();

export default function RootNavigator() {
  const { isAuthenticated, loading } = useContext(AuthContext);
  const { role } = useContext(RoleContext);

  if (loading) {
    return <SplashScreen />;
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!isAuthenticated ? (
        <Stack.Screen name={ROUTES.AUTH} component={AuthNavigator} />
      ) : !role ? (
        <Stack.Screen name={ROUTES.ROLE_SELECTION} component={RoleSelectionScreen} />
      ) : role === ROLES.RIDER ? (
        <Stack.Screen name={ROUTES.RIDER} component={RiderNavigator} />
      ) : role === ROLES.DRIVER ? (
        <Stack.Screen name={ROUTES.DRIVER} component={DriverNavigator} />
      ) : (
        <Stack.Screen name={ROUTES.OPERATOR} component={OperatorNavigator} />
      )}
    </Stack.Navigator>
  );
}
