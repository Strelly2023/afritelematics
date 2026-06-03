import React from "react";
import { Text, View } from "react-native";
import AppHeader from "../../components/AppHeader";
import { theme } from "../../theme/theme";

export default function EarningsScreen() {
  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Earnings" subtitle="Earnings must be receipt-backed." />
      <Text>Verified earnings ledger entries will render here.</Text>
    </View>
  );
}
