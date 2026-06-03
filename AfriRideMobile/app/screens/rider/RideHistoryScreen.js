import React from "react";
import { Text, View } from "react-native";
import AppHeader from "../../components/AppHeader";
import { theme } from "../../theme/theme";

export default function RideHistoryScreen() {
  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Ride History" subtitle="History must come from backend receipts." />
      <Text>Receipt-backed ride history will render here.</Text>
    </View>
  );
}
