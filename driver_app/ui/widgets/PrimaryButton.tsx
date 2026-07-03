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
  tone?: "primary" | "danger";
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
        tone === "danger" ? styles.danger : styles.primary,
        tone === "primary" ? { backgroundColor: theme.primary } : null,
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
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.lg,
  },
  danger: {
    backgroundColor: colors.danger,
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
  },
});
