import React from "react";
import { View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import { ROLES } from "../../constants/roles";
import { useRole } from "../../state/RoleContext";
import { theme } from "../../theme/theme";

export default function RoleSelectionScreen() {
  const { setRole } = useRole();

  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Choose Role" subtitle="Role controls display surface only." />
      <AppButton title="Rider" onPress={() => setRole(ROLES.RIDER)} />
      <AppButton title="Driver" onPress={() => setRole(ROLES.DRIVER)} />
      <AppButton title="Operator" onPress={() => setRole(ROLES.OPERATOR)} />
    </View>
  );
}
