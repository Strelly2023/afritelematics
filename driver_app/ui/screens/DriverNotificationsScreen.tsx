import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type DriverNotification = {
  id: string;
  title: string;
  detail: string;
  tone?: "success" | "info" | "review";
};

type DriverNotificationsScreenProps = {
  notifications: DriverNotification[];
};

export function DriverNotificationsScreen({
  notifications,
}: DriverNotificationsScreenProps) {
  return (
    <SurfacePanel>
      <Text style={styles.title}>Notifications</Text>
      {notifications.length === 0 ? (
        <Text style={styles.muted}>No alerts yet</Text>
      ) : null}
      {notifications.map((notification) => (
        <View key={notification.id} style={styles.notification}>
          <View
            style={[
              styles.dot,
              notification.tone === "review" ? styles.reviewDot : null,
              notification.tone === "info" ? styles.infoDot : null,
            ]}
          />
          <View style={styles.body}>
            <Text style={styles.notificationTitle}>{notification.title}</Text>
            <Text style={styles.muted}>{notification.detail}</Text>
          </View>
        </View>
      ))}
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  body: {
    flex: 1,
    gap: spacing.xs,
  },
  dot: {
    backgroundColor: colors.success,
    borderRadius: 6,
    height: 12,
    marginTop: 4,
    width: 12,
  },
  infoDot: {
    backgroundColor: colors.info,
  },
  muted: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 19,
  },
  notification: {
    alignItems: "flex-start",
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: "row",
    gap: spacing.sm,
    paddingTop: spacing.md,
  },
  notificationTitle: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "900",
  },
  reviewDot: {
    backgroundColor: colors.amber,
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
});
