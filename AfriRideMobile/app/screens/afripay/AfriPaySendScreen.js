import React, { useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppCard from "../../components/AppCard";
import StatusBadge from "../../components/StatusBadge";
import { createNovaPayPayment, quoteNovaPayFx } from "../../services/afripayService";
import { theme } from "../../theme/theme";

export default function NovaPaySendScreen() {
  const [amount, setAmount] = useState("100.00");
  const [recipient, setRecipient] = useState("burundi.merchant.001");
  const [quote, setQuote] = useState(null);
  const [receipt, setReceipt] = useState(null);
  const [error, setError] = useState(null);

  const reference = useMemo(() => `mobile.novapay.${Date.now()}`, []);

  async function handleQuote() {
    setError(null);
    try {
      const response = await quoteNovaPayFx({
        amount,
        from_currency: "AUD",
        to_currency: "BIF",
      });
      setQuote(response);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSend() {
    setError(null);
    try {
      const response = await createNovaPayPayment({
        payer_id: "mobile.user.001",
        payee_id: recipient,
        amount,
        currency: "AUD",
        reference,
        preference: "balanced",
        metadata: { channel: "mobile" },
      });
      setReceipt(response);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Send Money</Text>

      <AppCard>
        <Text style={styles.label}>Recipient</Text>
        <TextInput value={recipient} onChangeText={setRecipient} style={styles.input} autoCapitalize="none" />
        <Text style={styles.label}>Amount AUD</Text>
        <TextInput value={amount} onChangeText={setAmount} style={styles.input} keyboardType="decimal-pad" />
        <View style={styles.actions}>
          <AppButton title="Quote" variant="secondary" onPress={handleQuote} />
          <AppButton title="Send" onPress={handleSend} />
        </View>
      </AppCard>

      {quote ? (
        <AppCard>
          <Text style={styles.cardTitle}>FX lock</Text>
          <Text style={styles.value}>{quote.amount_out.currency} {quote.amount_out.amount}</Text>
          <Text style={styles.muted}>{quote.locked_reference}</Text>
        </AppCard>
      ) : null}

      {receipt ? (
        <AppCard>
          <View style={styles.receiptHeader}>
            <Text style={styles.cardTitle}>Backend receipt</Text>
            <StatusBadge label={receipt.status} tone="success" />
          </View>
          <Text style={styles.muted}>Reference {receipt.reference}</Text>
          {receipt.journal_reference ? (
            <Text style={styles.muted}>Journal {receipt.journal_reference}</Text>
          ) : null}
          {receipt.routes.map((route) => (
            <View key={route.external_reference} style={styles.routeRow}>
              <Text style={styles.routeProvider}>{route.provider}</Text>
              <Text style={styles.muted}>{route.rail}</Text>
              <Text style={styles.routeAmount}>{route.amount.currency} {route.amount.amount}</Text>
            </View>
          ))}
        </AppCard>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { backgroundColor: theme.colors.background },
  content: { gap: theme.spacing.md, padding: theme.spacing.md },
  title: { color: theme.colors.text, fontSize: 24, fontWeight: "800" },
  label: { color: theme.colors.muted, fontSize: 13, fontWeight: "700" },
  input: {
    borderColor: theme.colors.border,
    borderRadius: theme.radius,
    borderWidth: 1,
    color: theme.colors.text,
    fontSize: 16,
    minHeight: 44,
    paddingHorizontal: theme.spacing.md,
  },
  actions: { flexDirection: "row", gap: theme.spacing.sm, marginTop: theme.spacing.sm },
  cardTitle: { color: theme.colors.text, fontSize: 17, fontWeight: "800" },
  value: { color: theme.colors.text, fontSize: 24, fontWeight: "800" },
  muted: { color: theme.colors.muted, fontSize: 13 },
  receiptHeader: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  routeRow: { borderTopColor: theme.colors.border, borderTopWidth: 1, gap: 2, paddingTop: theme.spacing.sm },
  routeProvider: { color: theme.colors.text, fontSize: 15, fontWeight: "800" },
  routeAmount: { color: theme.colors.text, fontSize: 15, fontWeight: "700" },
  error: { color: theme.colors.danger, fontSize: 14, fontWeight: "700" },
});
