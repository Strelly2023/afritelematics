import React, { useState } from "react";
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

export type NovaPayRoleConfig = Readonly<{
  appName: string;
  role: string;
  balanceLabel: string;
  balance: string;
  tabs: readonly string[];
  features: readonly string[];
  primaryFlows: readonly string[];
  sections: readonly {
    title: string;
    description: string;
    buttons: readonly string[];
  }[];
}>;

type FlowState = "idle" | "loading" | "success" | "error" | "offline";

export function NovaPayRoleApp({ config }: { config: NovaPayRoleConfig }) {
  const [dark, setDark] = useState(false);
  const [tab, setTab] = useState(config.tabs[0]);
  const [flow, setFlow] = useState(config.primaryFlows[0]);
  const [amount, setAmount] = useState("");
  const [recipient, setRecipient] = useState("");
  const [state, setState] = useState<FlowState>("idle");
  const [receipt, setReceipt] = useState("");
  const palette = dark ? darkTheme : lightTheme;
  const sendJourney = [
    "Continue with NovaID",
    "Phone, email, government ID, biometric, device trust, AML/KYC",
    "Recipient: contacts, QR, NovaID, mobile, email, bank account",
    "Destination: Australia to Democratic Republic of Congo",
    "Live FX rate with lock timer",
    "Delivery: NovaPay Wallet, mobile money, bank, cash pickup, card",
    "Funding: wallet, debit card, credit card, bank, Apple Pay, Google Pay",
    "Compliance, sanctions, fraud, risk, settlement routing",
    "Digital receipt and transaction certificate",
  ];
  const receiveJourney = [
    "Smart incoming transfer alert",
    "NovaID, passkey, PIN, or biometric login",
    "Review sender, amount, currency, exchange rate, reference, trust status",
    "Receive into wallet, bank, mobile money, debit card, business or merchant wallet",
    "Cash pickup with collection code and QR collection code",
    "Digital signature verification and receipt generation",
    "Post-receipt actions: send, withdraw, bills, QR Pay, airtime, history, support",
  ];
  const transferScenario = {
    sender: "Djuma Kikombe",
    senderCountry: "Australia",
    recipient: "Kaskile Emanuel",
    recipientCountry: "Democratic Republic of Congo",
    sendAmount: "AUD 100.00",
    fee: "AUD 2.99",
    exchangeRate: "1 AUD = live CDF quote",
    recipientReceives: "CDF calculated before confirmation",
    deliveryMethod: "Mobile Money",
    transferId: "NP-2026-00054882",
    deliveryStatus: "Delivered",
  } as const;
  const trackingSteps = ["Preparing", "Processing", "Sent", "Delivered"] as const;
  const evidenceSteps = [
    "Transfer Created",
    "Identity Verified (NovaID)",
    "Payment Authorized",
    "Ledger Recorded",
    "Digital Signature",
    "Receipt Generated",
    "Replay Evidence Stored",
    "Audit Package Available",
  ] as const;
  const activeSection = config.sections.find((section) => section.title === tab) ?? config.sections[0] ?? {
    title: tab,
    description: "",
    buttons: [],
  };

  const submit = () => {
    if (!amount || !recipient) {
      setState("error");
      return;
    }
    setState("loading");
    const receiptId = `NPR-${Date.now()}`;
    setReceipt(receiptId);
    setState("success");
  };

  return (
    <View style={[styles.screen, { backgroundColor: palette.background }]}>
      <StatusBar barStyle={dark ? "light-content" : "dark-content"} />
      <SafeAreaView style={styles.safe}>
        <View style={styles.header}>
          <View>
            <Text style={[styles.brand, { color: palette.text }]}>NovaPay</Text>
            <Text style={[styles.role, { color: palette.muted }]}>{config.appName.toUpperCase()}</Text>
          </View>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Toggle light or dark mode"
            onPress={() => setDark((value) => !value)}
            style={[styles.mode, { backgroundColor: palette.surface }]}
          >
            <Text>{dark ? "☀" : "☾"}</Text>
          </Pressable>
        </View>
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.identity}>
            <Text style={styles.identityText}>✓ NovaID verified · Secure session</Text>
          </View>
          <View style={styles.balance}>
            <Text style={styles.balanceLabel}>{config.balanceLabel}</Text>
            <Text style={styles.balanceValue}>{config.balance}</Text>
            <Text style={styles.balanceMeta}>Ledger current · Risk low · Online</Text>
          </View>
          {config.role === "consumer" && (
            <View style={[styles.card, { backgroundColor: palette.surface }]}>
              <Text style={[styles.heading, { color: palette.text }]}>International transfer</Text>
              <Text style={{ color: palette.muted }}>
                Trust-first remittance with NovaID verification, live FX, compliance screening, end-to-end tracking,
                receipts, and signed transaction certificates.
              </Text>
              <View style={styles.flowColumns}>
                <View style={styles.flowColumn}>
                  <Text style={[styles.flowTitle, { color: palette.text }]}>Send money</Text>
                  {sendJourney.map((step) => (
                    <Text key={step} style={{ color: palette.muted }}>✓ {step}</Text>
                  ))}
                </View>
                <View style={styles.flowColumn}>
                  <Text style={[styles.flowTitle, { color: palette.text }]}>Receive money</Text>
                  {receiveJourney.map((step) => (
                    <Text key={step} style={{ color: palette.muted }}>✓ {step}</Text>
                  ))}
                </View>
              </View>
              <View style={styles.trustRail}>
                {["NovaID verified", "Device trusted", "AML clear", "FX locked", "Receipt signed"].map((item) => (
                  <Text key={item} style={styles.trustPill}>{item}</Text>
                ))}
              </View>
              <View accessibilityLabel="Djuma Kikombe to Kaskile Emanuel transfer scenario" style={styles.scenarioPanel}>
                <Text style={[styles.flowTitle, { color: palette.text }]}>Send AUD 100 to DR Congo</Text>
                <View style={styles.transferRows}>
                  {[
                    ["Sender", transferScenario.sender],
                    ["From", transferScenario.senderCountry],
                    ["Recipient", transferScenario.recipient],
                    ["To", transferScenario.recipientCountry],
                    ["Receive method", transferScenario.deliveryMethod],
                    ["You send", transferScenario.sendAmount],
                    ["Transfer fee", transferScenario.fee],
                    ["Exchange rate", transferScenario.exchangeRate],
                    ["Recipient receives", transferScenario.recipientReceives],
                    ["Transfer ID", transferScenario.transferId],
                    ["Status", transferScenario.deliveryStatus],
                  ].map(([label, value]) => (
                    <View key={label} style={[styles.transferRow, { borderBottomColor: palette.border }]}>
                      <Text style={{ color: palette.muted }}>{label}</Text>
                      <Text style={[styles.transferValue, { color: palette.text }]}>{value}</Text>
                    </View>
                  ))}
                </View>
                <Text style={[styles.flowTitle, { color: palette.text }]}>Real-time tracking</Text>
                <View style={styles.trustRail}>
                  {trackingSteps.map((step) => (
                    <Text key={step} style={styles.trustPill}>{step}</Text>
                  ))}
                </View>
                <Text style={[styles.flowTitle, { color: palette.text }]}>Receiver notification</Text>
                <Text style={{ color: palette.muted }}>
                  SMS: NovaPay transfer from Djuma Kikombe. Reference NP-2026-00054882. Collect via Mobile Money or Agent.
                </Text>
                <Text style={[styles.flowTitle, { color: palette.text }]}>NovaTrust verification</Text>
                {evidenceSteps.map((step) => (
                  <Text key={step} style={{ color: palette.muted }}>✓ {step}</Text>
                ))}
              </View>
            </View>
          )}
          <Text style={[styles.heading, { color: palette.text }]}>Quick actions</Text>
          <View style={styles.grid}>
            {config.primaryFlows.map((item) => (
              <Pressable
                key={item}
                accessibilityRole="button"
                accessibilityLabel={`NovaPay ${item}`}
                onPress={() => {
                  setFlow(item);
                  setState("idle");
                }}
                style={[styles.action, { backgroundColor: flow === item ? "#5B3DF5" : palette.surface }]}
              >
                <Text style={{ color: flow === item ? "#fff" : palette.text }}>{item}</Text>
              </Pressable>
            ))}
          </View>
          <View style={[styles.card, { backgroundColor: palette.surface }]}>
            <Text style={[styles.heading, { color: palette.text }]}>{activeSection.title}</Text>
            <Text style={{ color: palette.muted }}>{activeSection.description}</Text>
            <View style={styles.grid}>
              {activeSection.buttons.map((button) => (
                <Pressable
                  key={button}
                  accessibilityRole="button"
                  accessibilityLabel={button}
                  onPress={() => setState("idle")}
                  style={[styles.action, { backgroundColor: palette.surface }]}
                >
                  <Text style={{ color: palette.text }}>{button}</Text>
                </Pressable>
              ))}
            </View>
          </View>
          <View style={[styles.card, { backgroundColor: palette.surface }]}>
            <Text style={[styles.heading, { color: palette.text }]}>{flow}</Text>
            <TextInput
              accessibilityLabel={`${flow} recipient`}
              value={recipient}
              onChangeText={setRecipient}
              placeholder="Phone, NovaPay ID, account, or QR"
              placeholderTextColor={palette.muted}
              style={[styles.input, { color: palette.text, borderColor: palette.border }]}
            />
            <TextInput
              accessibilityLabel={`${flow} amount`}
              value={amount}
              onChangeText={setAmount}
              placeholder="Amount"
              placeholderTextColor={palette.muted}
              keyboardType="decimal-pad"
              style={[styles.input, { color: palette.text, borderColor: palette.border }]}
            />
            <Pressable accessibilityRole="button" accessibilityLabel={`Confirm ${flow}`} onPress={submit} style={styles.submit}>
              <Text style={styles.submitText}>Confirm {flow}</Text>
            </Pressable>
            {state === "loading" && <Text style={styles.notice}>Processing securely…</Text>}
            {state === "error" && <Text style={styles.error}>Enter a recipient and amount.</Text>}
            {state === "offline" && <Text style={styles.notice}>Saved offline. It will sync safely.</Text>}
            {state === "success" && (
              <View style={styles.success}>
                <Text style={styles.successText}>✓ Payment successful</Text>
                <Text style={styles.receipt}>Digital receipt {receipt}</Text>
                <Text style={styles.receipt}>Proof-of-payment available</Text>
              </View>
            )}
          </View>
          <Text style={[styles.heading, { color: palette.text }]}>All services</Text>
          <View style={[styles.card, { backgroundColor: palette.surface }]}>
            {config.features.map((feature) => (
              <Pressable
                key={feature}
                accessibilityRole="button"
                accessibilityLabel={`Open ${feature}`}
                onPress={() => setTab(feature)}
                style={[styles.feature, { borderBottomColor: palette.border }]}
              >
                <Text style={{ color: palette.text }}>{feature}</Text>
                <Text style={{ color: palette.muted }}>›</Text>
              </Pressable>
            ))}
          </View>
          <Text style={[styles.empty, { color: palette.muted }]}>Transaction timeline · No pending items</Text>
        </ScrollView>
        <View style={[styles.tabs, { backgroundColor: palette.surface }]}>
          {config.tabs.map((item) => (
            <Pressable key={item} accessibilityRole="tab" accessibilityLabel={`${item} tab`} onPress={() => setTab(item)}>
              <Text style={{ color: tab === item ? "#5B3DF5" : palette.muted, fontWeight: "700" }}>{item}</Text>
            </Pressable>
          ))}
        </View>
      </SafeAreaView>
    </View>
  );
}

const lightTheme = { background: "#F4F6FB", surface: "#FFFFFF", text: "#15182A", muted: "#687086", border: "#DDE2EC" };
const darkTheme = { background: "#101321", surface: "#1B2033", text: "#F7F8FC", muted: "#AAB2C8", border: "#343B51" };
const styles = StyleSheet.create({
  screen: { flex: 1 },
  safe: { flex: 1 },
  header: { padding: 20, flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  brand: { fontSize: 28, fontWeight: "900" },
  role: { fontSize: 11, fontWeight: "800", letterSpacing: 1.2 },
  mode: { width: 42, height: 42, borderRadius: 21, alignItems: "center", justifyContent: "center" },
  content: { padding: 18, paddingBottom: 100, gap: 16 },
  identity: { backgroundColor: "#E8FBF2", borderRadius: 12, padding: 12 },
  identityText: { color: "#087A50", fontWeight: "700" },
  balance: { backgroundColor: "#5B3DF5", borderRadius: 22, padding: 22 },
  balanceLabel: { color: "#DCD6FF", fontWeight: "700" },
  balanceValue: { color: "#FFFFFF", fontSize: 34, fontWeight: "900", marginVertical: 8 },
  balanceMeta: { color: "#DCD6FF", fontSize: 12 },
  heading: { fontSize: 18, fontWeight: "800" },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  action: { padding: 14, borderRadius: 14, minWidth: "46%", flexGrow: 1 },
  card: { padding: 16, borderRadius: 18, gap: 12 },
  input: { borderWidth: 1, borderRadius: 12, padding: 14 },
  submit: { backgroundColor: "#5B3DF5", padding: 15, borderRadius: 12, alignItems: "center" },
  submitText: { color: "#FFFFFF", fontWeight: "800" },
  notice: { color: "#8A6500" },
  error: { color: "#C93647" },
  success: { backgroundColor: "#E8FBF2", borderRadius: 12, padding: 12 },
  successText: { color: "#087A50", fontWeight: "800" },
  receipt: { color: "#345448", marginTop: 4 },
  feature: { paddingVertical: 13, borderBottomWidth: 1, flexDirection: "row", justifyContent: "space-between" },
  empty: { textAlign: "center", padding: 18 },
  tabs: { padding: 18, flexDirection: "row", justifyContent: "space-around" },
  flowColumns: { gap: 14 },
  flowColumn: { gap: 6 },
  flowTitle: { fontWeight: "900", marginTop: 4 },
  trustRail: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  trustPill: { backgroundColor: "#E8FBF2", color: "#087A50", paddingHorizontal: 10, paddingVertical: 7, borderRadius: 8, fontWeight: "800" },
  scenarioPanel: { borderWidth: 1, borderColor: "#DDE2EC", borderRadius: 12, padding: 12, gap: 8 },
  transferRows: { gap: 0 },
  transferRow: { paddingVertical: 8, borderBottomWidth: 1, gap: 2 },
  transferValue: { fontWeight: "800" },
});
