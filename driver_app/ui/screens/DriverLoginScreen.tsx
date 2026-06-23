import React from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type DriverLoginScreenProps = {
  email: string;
  password: string;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onContinue: () => void;
};

export function DriverLoginScreen({
  email,
  password,
  onEmailChange,
  onPasswordChange,
  onContinue,
}: DriverLoginScreenProps) {
  return (
    <SurfacePanel>
      <View style={styles.header}>
        <Text style={styles.title}>Driver Login</Text>
        <Text style={styles.subtitle}>
          Access verified trips, earnings, vehicle status, and pilot diagnostics.
        </Text>
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
      <PrimaryButton label="Continue" onPress={onContinue} />
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
