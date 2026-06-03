import React from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type FieldProps = {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder?: string;
};

export function Field({
  label,
  value,
  onChangeText,
  placeholder,
}: FieldProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.sm,
  },
  input: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.ink,
    minHeight: 48,
    paddingHorizontal: spacing.md,
  },
  label: {
    color: colors.secondary,
    fontSize: 14,
    fontWeight: "700",
  },
});
