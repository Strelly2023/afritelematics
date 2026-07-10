import React from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from "react-native";

import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type BottomTabsProps<T extends string> = {
  tabs: Array<{ key: T; label: string }>;
  activeTab: T;
  onChange: (tab: T) => void;
};

export function BottomTabs<T extends string>({
  tabs,
  activeTab,
  onChange,
}: BottomTabsProps<T>) {
  const expanded = useWindowDimensions().width >= 840;
  const content = (
    <>
      {tabs.map((tab) => {
        const active = tab.key === activeTab;
        return (
          <Pressable
            accessibilityRole="tab"
            accessibilityState={{ selected: active }}
            accessibilityLabel={`${tab.label} tab`}
            key={tab.key}
            onPress={() => onChange(tab.key)}
            style={[styles.tab, expanded ? styles.railTab : null, active ? styles.activeTab : null]}
          >
            <Text
              numberOfLines={1}
              adjustsFontSizeToFit
              minimumFontScale={0.86}
              style={[styles.label, active ? styles.activeLabel : null]}
            >
              {tab.label}
            </Text>
          </Pressable>
        );
      })}
    </>
  );

  if (!expanded) {
    return (
      <ScrollView
        accessibilityRole="tablist"
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollBar}
      >
        {content}
      </ScrollView>
    );
  }

  return (
    <View
      accessibilityRole="tablist"
      style={[styles.bar, expanded ? styles.rail : null]}
    >
      {content}
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
  bar: {
    flexDirection: "row",
    gap: spacing.sm,
    justifyContent: "space-between",
  },
  label: {
    color: colors.secondary,
    fontSize: 13,
    fontWeight: "900",
  },
  rail: {
    flexDirection: "column",
    justifyContent: "flex-start",
  },
  railTab: {
    flex: 0,
    width: "100%",
  },
  scrollBar: {
    gap: spacing.sm,
    paddingHorizontal: spacing.xs,
  },
  tab: {
    alignItems: "center",
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 999,
    borderWidth: 1,
    flex: 1,
    justifyContent: "center",
    minHeight: 48,
    minWidth: 88,
    paddingHorizontal: spacing.sm,
  },
});
