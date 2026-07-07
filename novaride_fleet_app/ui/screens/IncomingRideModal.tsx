import React from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";

import type { DriverRideRequest } from "../../core/models/driver";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type IncomingRideModalProps = {
  visible: boolean;
  request: DriverRideRequest | null;
  onAccept: () => void;
  onDecline: () => void;
  onClose?: () => void;
};

export function IncomingRideModal({
  visible,
  request,
  onAccept,
  onDecline,
  onClose,
}: IncomingRideModalProps) {
  if (!request) {
    return null;
  }

  return (
    <Modal animationType="fade" transparent visible={visible}>
      <Pressable style={styles.backdrop} onPress={onClose} />
      <View style={styles.center}>
        <View style={styles.card}>
          <Text style={styles.kicker}>Incoming ride</Text>
          <Text style={styles.route}>{request.pickupText} to {request.dropoffText}</Text>
          <Text style={styles.meta}>Rider: {request.riderName || "Verified rider"}</Text>
          <Text style={styles.meta}>ETA: {request.etaText || "Live dispatch"}</Text>
          <Text style={styles.fare}>{request.quotedTotalText || "Fare confirmed in backend"}</Text>

          <View style={styles.row}>
            <Badge label="Trip verified" />
            <Badge label="Driver verified" />
            <Badge label="Payment ready" />
          </View>

          <View style={styles.actions}>
            <PrimaryButton label="Accept" onPress={onAccept} />
            <PrimaryButton label="Decline" onPress={onDecline} tone="danger" />
          </View>

          <View style={styles.secondaryActions}>
            <Text style={styles.secondary}>Call</Text>
            <Text style={styles.secondary}>Chat</Text>
            <Text style={styles.secondary}>Share ride</Text>
          </View>
        </View>
      </View>
    </Modal>
  );
}

function Badge({ label }: { label: string }) {
  return (
    <View style={styles.badge}>
      <Text style={styles.badgeText}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  actions: {
    gap: spacing.sm,
  },
  backdrop: {
    backgroundColor: "rgba(15, 23, 42, 0.62)",
    ...StyleSheet.absoluteFillObject,
  },
  badge: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
  },
  badgeText: {
    color: colors.success,
    fontSize: 12,
    fontWeight: "900",
  },
  card: {
    backgroundColor: colors.panel,
    borderRadius: 16,
    gap: spacing.md,
    maxWidth: 520,
    padding: spacing.lg,
    width: "100%",
  },
  center: {
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
    ...StyleSheet.absoluteFillObject,
  },
  fare: {
    color: colors.success,
    fontSize: 16,
    fontWeight: "900",
  },
  kicker: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  meta: {
    color: colors.secondary,
    fontSize: 14,
    fontWeight: "700",
  },
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  route: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  secondary: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "800",
  },
  secondaryActions: {
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between",
  },
});
