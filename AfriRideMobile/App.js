import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { Provider as PaperProvider } from "react-native-paper";
import RootNavigator from "./app/navigation/RootNavigator";
import theme from "./app/theme/theme";
import { AuthProvider } from "./app/state/AuthContext";
import { RoleProvider } from "./app/state/RoleContext";
import { RideProvider } from "./app/state/RideContext";

export default function App() {
  return (
    <PaperProvider theme={theme}>
      <AuthProvider>
        <RoleProvider>
          <RideProvider>
            <NavigationContainer>
              <RootNavigator />
            </NavigationContainer>
          </RideProvider>
        </RoleProvider>
      </AuthProvider>
    </PaperProvider>
  );
}
