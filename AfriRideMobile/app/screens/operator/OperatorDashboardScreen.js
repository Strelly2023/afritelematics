import React from "react";
import { View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import { ROUTES } from "../../constants/routes";
import { theme } from "../../theme/theme";

export default function OperatorDashboardScreen({ navigation }) {
  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Operator" subtitle="Observation only. No manual truth override." />
      <AppButton title="Replay Monitor" onPress={() => navigation.navigate(ROUTES.REPLAY_MONITOR)} />
      <AppButton title="Evidence Viewer" onPress={() => navigation.navigate(ROUTES.EVIDENCE_VIEWER)} />
    </View>
  );
}
