import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

export function WalletScreen() {
  return (
    <SurfacePanel>
      <Text style={styles.title}>NovaPay Wallet</Text>
      <View style={styles.balanceCard}>
        <Text style={styles.balanceLabel}>Available balance</Text>
        <Text style={styles.balanceValue}>UGX 128,400</Text>
        <Text style={styles.balanceMeta}>Linked payment methods and instant settlement.</Text>
      </View>

      <View style={styles.methods}>
        <Method label="Visa ending 4242" status="Default" />
        <Method label="Mobile Money" status="Active" />
        <Method label="Business wallet" status="Ready" />
      </View>

      <View style={styles.actions}>
        <PrimaryButton label="Add payment" onPress={() => undefined} />
        <PrimaryButton label="Split fare" onPress={() => undefined} tone="secondary" />
      </View>
    </SurfacePanel>
  );
}

function Method({ label, status }: { label: string; status: string }) {
  return (
    <View style={styles.method}>
      <Text style={styles.methodLabel}>{label}</Text>
      <Text style={styles.methodStatus}>{status}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  actions: {
    gap: spacing.sm,
  },
  balanceCard: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.lg,
  },
  balanceLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  balanceMeta: {
    color: colors.secondary,
    fontSize: 14,
    lineHeight: 20,
  },
  balanceValue: {
    color: colors.success,
    fontSize: 28,
    fontWeight: "900",
  },
  method: {
    backgroundColor: colors.soft,
    borderRadius: 8,
    gap: spacing.xs,
    padding: spacing.md,
  },
  methodLabel: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "800",
  },
  methodStatus: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  methods: {
    gap: spacing.sm,
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
});
