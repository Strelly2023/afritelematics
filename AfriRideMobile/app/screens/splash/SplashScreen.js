import React from "react";
import { Text, View } from "react-native";
import AppHeader from "../../components/AppHeader";
import { theme } from "../../theme/theme";

export default function SplashScreen() {
  return (
    <View style={{ flex: 1, justifyContent: "center", padding: theme.spacing.lg, gap: 18 }}>
      <AppHeader
        title="AfriRide Mobile"
        subtitle="Role-separated constitutional display surface"
      />
      <Text>Backend proof decides. Replay verifies. Mobile displays.</Text>
      <Text>Loading confirmed session state...</Text>
    </View>
  );
}
