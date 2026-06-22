import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { trustColors, trustSpacing } from "../theme/trustTokens";

export type LifecycleStep = {
  label: string;
  completed: boolean;
  current?: boolean;
};

type LifecycleTimelineProps = {
  steps: LifecycleStep[];
  title?: string;
};

export function LifecycleTimeline({ steps, title = "Ride Timeline" }: LifecycleTimelineProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      {steps.map((step) => (
        <View key={step.label} style={styles.step}>
          <View
            style={[
              styles.dot,
              step.completed ? styles.dotComplete : step.current ? styles.dotCurrent : styles.dotPending,
            ]}
          />
          <Text style={[styles.label, step.completed ? styles.labelComplete : null]}>
            {step.label}
          </Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: trustColors.CARD,
    borderColor: trustColors.BORDER,
    borderRadius: 8,
    borderWidth: 1,
    gap: trustSpacing.sm,
    padding: trustSpacing.lg,
  },
  dot: {
    borderRadius: 6,
    height: 12,
    width: 12,
  },
  dotComplete: {
    backgroundColor: trustColors.HIGH,
  },
  dotCurrent: {
    backgroundColor: trustColors.MEDIUM,
  },
  dotPending: {
    backgroundColor: trustColors.BORDER,
  },
  label: {
    color: trustColors.MUTED,
    fontSize: 15,
    fontWeight: "800",
  },
  labelComplete: {
    color: trustColors.TEXT,
  },
  step: {
    alignItems: "center",
    flexDirection: "row",
    gap: trustSpacing.sm,
  },
  title: {
    color: trustColors.TEXT,
    fontSize: 16,
    fontWeight: "900",
  },
});
