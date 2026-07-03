import React from "react";
import {
  Pressable,
  StyleSheet,
  Text,
  type StyleProp,
  type ViewStyle,
} from "react-native";

import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";
import { useMobileExcellence } from "../../../afriride_system/mobile/shared/mobileExcellence";

type PrimaryButtonProps = {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  tone?: "primary" | "secondary";
  style?: StyleProp<ViewStyle>;
};

export function PrimaryButton({
  label,
  onPress,
  disabled,
  tone = "primary",
  style,
}: PrimaryButtonProps) {
  const { theme } = useMobileExcellence();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: Boolean(disabled) }}
      accessibilityLabel={label}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        tone === "secondary" ? styles.secondary : styles.primary,
        tone === "primary" ? { backgroundColor: theme.primary, borderColor: theme.primary } : null,
        disabled ? styles.disabled : null,
        pressed ? styles.pressed : null,
        style,
      ]}
    >
      <Text style={styles.label}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    borderRadius: 20,
    borderWidth: 1,
    minHeight: 48,
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  disabled: {
    opacity: 0.5,
  },
  label: {
    color: colors.panel,
    fontSize: 16,
    fontWeight: "800",
  },
  pressed: {
    opacity: 0.82,
  },
  primary: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  secondary: {
    backgroundColor: colors.secondary,
    borderColor: colors.secondary,
  },
});
