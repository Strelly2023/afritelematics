import React from "react";
import { View } from "react-native";
import { theme } from "../theme/theme";

export default function AppCard({ children, style }) {
  return (
    <View
      style={[
        {
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.border,
          borderRadius: theme.radius,
          borderWidth: 1,
          padding: theme.spacing.md,
          gap: theme.spacing.sm,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}
