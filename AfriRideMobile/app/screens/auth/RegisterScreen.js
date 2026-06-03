import React, { useState } from "react";
import { TextInput, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import { useAuth } from "../../state/AuthContext";
import { useRole } from "../../state/RoleContext";
import { theme } from "../../theme/theme";

export default function RegisterScreen({ navigation }) {
  const [userId, setUserId] = useState("R1");
  const { register } = useAuth();
  const { role } = useRole();

  async function submit() {
    await register({ userId, role });
  }

  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Register" subtitle="For test users only." />
      <TextInput
        value={userId}
        onChangeText={setUserId}
        placeholder="Assigned ID"
        style={{ borderWidth: 1, borderColor: theme.colors.border, padding: 12 }}
      />
      <AppButton title="Register" onPress={submit} />
    </View>
  );
}
