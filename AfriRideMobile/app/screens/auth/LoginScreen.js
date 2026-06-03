import React, { useState } from "react";
import { TextInput, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import { useAuth } from "../../state/AuthContext";
import { useRole } from "../../state/RoleContext";
import { ROUTES } from "../../constants/routes";
import { theme } from "../../theme/theme";

export default function LoginScreen({ navigation }) {
  const [userId, setUserId] = useState("R1");
  const { login } = useAuth();
  const { role } = useRole();

  async function submit() {
    await login({ userId, role });
  }

  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Login" subtitle="Select an assigned field-test identity." />
      <TextInput
        value={userId}
        onChangeText={setUserId}
        placeholder="Assigned ID"
        style={{ borderWidth: 1, borderColor: theme.colors.border, padding: 12 }}
      />
      <AppButton title="Login" onPress={submit} />
      <AppButton
        title="Register"
        variant="secondary"
        onPress={() => navigation.navigate(ROUTES.REGISTER)}
      />
    </View>
  );
}
