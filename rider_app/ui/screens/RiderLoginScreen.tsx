import React from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type RiderLoginScreenProps = {
  email: string;
  password: string;
  loading?: boolean;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onContinue: () => void | Promise<void>;
};

export function RiderLoginScreen({
  email,
  password,
  loading,
  onEmailChange,
  onPasswordChange,
  onContinue,
}: RiderLoginScreenProps) {
  return (
    <SurfacePanel>
      <View style={styles.header}>
        <Text style={styles.title}>Rider Login</Text>
        <Text style={styles.subtitle}>Access booking, verified trips, and receipts.</Text>
      </View>
      <TextInput
        autoCapitalize="none"
        keyboardType="email-address"
        onChangeText={onEmailChange}
        placeholder="Email"
        placeholderTextColor={colors.muted}
        style={styles.input}
        value={email}
      />
      <TextInput
        onChangeText={onPasswordChange}
        placeholder="Password"
        placeholderTextColor={colors.muted}
        secureTextEntry
        style={styles.input}
        value={password}
      />
      <PrimaryButton label={loading ? "Signing in" : "Continue"} onPress={onContinue} disabled={loading} />
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  header: {
    gap: spacing.xs,
  },
  input: {
    backgroundColor: colors.soft,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.ink,
    fontSize: 16,
    minHeight: 48,
    paddingHorizontal: spacing.md,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20,
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
});
