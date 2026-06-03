import React from "react";
import { Pressable, Text } from "react-native";
import { theme } from "../theme/theme";

export default function AppButton({ title, onPress, variant = "primary" }) {
  const isPrimary = variant === "primary";
  return (
    <Pressable
      onPress={onPress}
      style={{
        alignItems: "center",
        backgroundColor: isPrimary ? theme.colors.primary : "#EEF2F6",
        borderRadius: theme.radius,
        minHeight: 46,
        justifyContent: "center",
        paddingHorizontal: theme.spacing.md,
      }}
    >
      <Text style={{ color: isPrimary ? "#FFFFFF" : theme.colors.text, fontWeight: "700" }}>
        {title}
      </Text>
    </Pressable>
  );
}
