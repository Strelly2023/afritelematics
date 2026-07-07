import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type ProductTabsProps<T extends string> = {
  tabs: Array<{ key: T; label: string }>;
  activeTab: T;
  onChange: (tab: T) => void;
};

export function ProductTabs<T extends string>({
  tabs,
  activeTab,
  onChange,
}: ProductTabsProps<T>) {
  return (
    <View style={styles.tabs}>
      {tabs.map((tab) => {
        const active = tab.key === activeTab;
        return (
          <Pressable
            accessibilityRole="button"
            key={tab.key}
            onPress={() => onChange(tab.key)}
            style={[styles.tab, active ? styles.activeTab : null]}
          >
            <Text style={[styles.label, active ? styles.activeLabel : null]}>
              {tab.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  activeLabel: {
    color: colors.panel,
  },
  activeTab: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  label: {
    color: colors.secondary,
    fontSize: 13,
    fontWeight: "900",
  },
  tab: {
    alignItems: "center",
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    minHeight: 40,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  tabs: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
});
