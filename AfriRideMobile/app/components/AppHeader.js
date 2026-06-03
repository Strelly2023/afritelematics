import React from "react";
import { Text, View } from "react-native";
import { theme } from "../theme/theme";

export default function AppHeader({ title, subtitle }) {
  return (
    <View style={{ gap: theme.spacing.xs }}>
      <Text style={{ color: theme.colors.text, fontSize: 26, fontWeight: "800" }}>
        {title}
      </Text>
      {subtitle ? (
        <Text style={{ color: theme.colors.muted, fontSize: 15 }}>{subtitle}</Text>
      ) : null}
    </View>
  );
}
