import React from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

export function WaitingForDriverScreen() {
  return (
    <SurfacePanel>
      <View style={styles.row}>
        <ActivityIndicator color={colors.primary} />
        <Text style={styles.text}>Waiting for driver confirmation</Text>
      </View>
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  row: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.md,
  },
  text: {
    color: colors.secondary,
    fontSize: 16,
    fontWeight: "700",
  },
});
