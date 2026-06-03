import React from "react";
import { Text } from "react-native";
import { theme } from "../theme/theme";

export default function StatusBadge({ label, tone = "neutral" }) {
  const color =
    tone === "success"
      ? theme.colors.success
      : tone === "danger"
        ? theme.colors.danger
        : theme.colors.muted;
  return (
    <Text
      style={{
        alignSelf: "flex-start",
        borderColor: color,
        borderRadius: 999,
        borderWidth: 1,
        color,
        fontWeight: "700",
        paddingHorizontal: 10,
        paddingVertical: 4,
      }}
    >
      {label}
    </Text>
  );
}
