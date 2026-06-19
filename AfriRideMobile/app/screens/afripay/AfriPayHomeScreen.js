import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppCard from "../../components/AppCard";
import StatusBadge from "../../components/StatusBadge";
import { ROUTES } from "../../constants/routes";
import { theme } from "../../theme/theme";

const balances = [
  { currency: "AUD", amount: "1,240.00", label: "Australia wallet" },
  { currency: "BIF", amount: "2,180,000", label: "Burundi wallet" },
  { currency: "USD", amount: "430.20", label: "Trade wallet" },
];

export default function NovaPayHomeScreen({ navigation }) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>NovaPay</Text>
        <StatusBadge label="Live settlement off" tone="warning" />
      </View>

      <AppCard style={styles.balancePanel}>
        <Text style={styles.panelLabel}>Available balance</Text>
        <Text style={styles.primaryBalance}>AUD 1,240.00</Text>
        <Text style={styles.muted}>Multi-currency wallet with deterministic backend receipts.</Text>
      </AppCard>

      <View style={styles.actions}>
        <AppButton title="Send money" onPress={() => navigation.navigate(ROUTES.AFRIPAY_SEND)} />
        <AppButton title="Treasury" variant="secondary" onPress={() => navigation.navigate(ROUTES.AFRIPAY_TREASURY)} />
        <AppButton title="Audit proofs" variant="secondary" onPress={() => navigation.navigate(ROUTES.AFRIPAY_AUDIT)} />
      </View>

      <Text style={styles.sectionTitle}>Wallets</Text>
      {balances.map((item) => (
        <AppCard key={item.currency} style={styles.walletRow}>
          <View>
            <Text style={styles.walletCurrency}>{item.currency}</Text>
            <Text style={styles.muted}>{item.label}</Text>
          </View>
          <Text style={styles.walletAmount}>{item.amount}</Text>
        </AppCard>
      ))}

      <Text style={styles.sectionTitle}>Activity</Text>
      <AppCard>
        <View style={styles.activityRow}>
          <View>
            <Text style={styles.activityTitle}>Split route remittance</Text>
            <Text style={styles.muted}>Mobile money + bank rail</Text>
          </View>
          <Text style={styles.success}>Success</Text>
        </View>
      </AppCard>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { backgroundColor: theme.colors.background },
  content: { gap: theme.spacing.md, padding: theme.spacing.md },
  header: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  title: { color: theme.colors.text, fontSize: 28, fontWeight: "800" },
  balancePanel: { backgroundColor: "#F5FBF9" },
  panelLabel: { color: theme.colors.muted, fontSize: 13, fontWeight: "600" },
  primaryBalance: { color: theme.colors.text, fontSize: 32, fontWeight: "800" },
  muted: { color: theme.colors.muted, fontSize: 13 },
  actions: { flexDirection: "row", gap: theme.spacing.sm },
  sectionTitle: { color: theme.colors.text, fontSize: 18, fontWeight: "700", marginTop: theme.spacing.sm },
  walletRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  walletCurrency: { color: theme.colors.text, fontSize: 16, fontWeight: "800" },
  walletAmount: { color: theme.colors.text, fontSize: 16, fontWeight: "700" },
  activityRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  activityTitle: { color: theme.colors.text, fontSize: 15, fontWeight: "700" },
  success: { color: theme.colors.success, fontSize: 13, fontWeight: "800" },
});
