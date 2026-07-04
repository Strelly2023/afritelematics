import React, { useMemo, useState } from "react";
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

export const NOVAPAY_AGENT_API_CONTRACTS = [
  "/v1/novapay/agents/profile",
  "/v1/novapay/agents/float",
  "/v1/novapay/agents/send-money",
  "/v1/novapay/agents/receive-money",
  "/v1/novapay/agents/cash-in",
  "/v1/novapay/agents/cash-out",
  "/v1/novapay/agents/qr",
  "/v1/novapay/agents/kyc",
  "/v1/novapay/agents/commissions",
  "/v1/novapay/agents/settlement",
  "/v1/novapay/agents/history",
  "/v1/novapay/agents/offline-queue",
  "/v1/novapay/agents/sync",
  "/v1/novapay/agents/compliance",
  "/v1/novapay/agents/receipts",
  "/v1/novapay/agents/supervisor-review",
] as const;

type AgentTab = "home" | "transfers" | "transactions" | "float" | "profile";

type ActionProps = {
  label: string;
  detail: string;
  onPress?: () => void;
};

type AlertStatus = "High Value Alert" | "Daily Limit Warning" | "AML Review Pending" | "Supervisor Review Required" | "Compliance Hold Active";

const quickActions = [
  { key: "send", label: "Send Money" },
  { key: "receive", label: "Receive Money" },
  { key: "cash-in", label: "Cash In" },
  { key: "cash-out", label: "Cash Out" },
  { key: "qr", label: "Scan QR" },
  { key: "verify", label: "Verify Customer" },
] as const;

const complianceAlerts: AlertStatus[] = [
  "High Value Alert",
  "Daily Limit Warning",
  "AML Review Pending",
  "Supervisor Review Required",
  "Compliance Hold Active",
];

const demoTransactions = [
  { id: "tx-001", amount: "UGX 120,000", customer: "Mary", status: "completed", trust: "verified" },
  { id: "tx-002", amount: "UGX 48,000", customer: "John", status: "pending", trust: "review" },
  { id: "tx-003", amount: "UGX 260,000", customer: "Grace", status: "offline", trust: "verified" },
];

export default function NovaPayAgentApp() {
  const [activeTab, setActiveTab] = useState<AgentTab>("home");

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <PilotModeBanner />
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.kicker}>NovaPay Agent App</Text>
            <Text style={styles.title}>Controlled Pilot Ready UI Surface</Text>
          </View>
          <View style={styles.badgeRow}>
            <TrustBadge status="verified" />
            <DeviceTrustChip status="trusted" />
          </View>
        </View>

        <View style={styles.statusRow}>
          <SyncStatusChip status="pending" pendingCount={3} />
          <Text style={styles.meta}>Pilot mode active</Text>
          <Text style={styles.meta}>Advisory only</Text>
        </View>

        <TabBar activeTab={activeTab} onChange={setActiveTab} />

        {activeTab === "home" ? (
          <AgentHomeDashboard
            agentName="Mary"
            agentId="agent-001"
            trustLevel="verified"
            deviceTrust="trusted"
            syncStatus="pending"
            pendingSync={3}
            floatBalance="UGX 4,520,000"
            walletBalance="UGX 180,000"
            commissionToday="UGX 82,500"
          />
        ) : null}

        {activeTab === "transfers" ? (
          <View style={styles.stack}>
            <SendMoneyScreen />
            <ReceiveMoneyScreen />
            <CashInScreen />
            <CashOutScreen />
            <QRScannerScreen />
          </View>
        ) : null}

        {activeTab === "transactions" ? (
          <View style={styles.stack}>
            <TransactionTimeline />
            <ReceiptVerificationCard />
            <ComplianceAlertPanel />
          </View>
        ) : null}

        {activeTab === "float" ? (
          <View style={styles.stack}>
            <FloatSummaryCard />
            <CommissionSummaryCard />
            <OfflineQueuePanel />
            <NovaAIInsightCard />
          </View>
        ) : null}

        {activeTab === "profile" ? (
          <AgentProfileScreen />
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

export function TrustBadge({ status }: { status: "verified" | "review" }) {
  return <Text style={styles.chip}>{status === "verified" ? "TrustBadge ✓" : "TrustBadge · review"}</Text>;
}

export function PilotModeBanner() {
  return <View style={styles.banner}><Text style={styles.bannerText}>PilotModeBanner — controlled pilot only</Text></View>;
}

export function SyncStatusChip({ status, pendingCount }: { status: "online" | "pending" | "offline"; pendingCount: number }) {
  return <Text style={styles.chip}>SyncStatusChip: {status} ({pendingCount} pending)</Text>;
}

export function DeviceTrustChip({ status }: { status: "trusted" | "review" }) {
  return <Text style={styles.chip}>DeviceTrustChip: {status}</Text>;
}

export function PrimaryActionGrid({ onAction }: { onAction?: (action: string) => void }) {
  return (
    <View style={styles.grid}>
      {quickActions.map((action) => (
        <Pressable key={action.key} style={styles.actionCard} onPress={() => onAction?.(action.key)}>
          <Text style={styles.actionTitle}>{action.label}</Text>
          <Text style={styles.actionDetail}>Pilot-safe request surface</Text>
        </Pressable>
      ))}
    </View>
  );
}

export function CustomerVerificationCard() {
  return (
    <Card title="CustomerVerificationCard">
      <Text style={styles.body}>Identity status, face match, KYC status, risk level, device trust.</Text>
      <Text style={styles.meta}>NovaID owns identity, MFA, biometrics, and KYC.</Text>
    </Card>
  );
}

export function FloatSummaryCard() {
  return (
    <Card title="FloatSummaryCard">
      <Text style={styles.body}>Current float, reserve float, pending settlements, commission balance.</Text>
      <Text style={styles.meta}>Display-only summary; NovaPay Core owns ledger state.</Text>
    </Card>
  );
}

export function TransactionTimeline() {
  return (
    <Card title="TransactionTimeline">
      <Text style={styles.body}>Created → Identity Verified → Policy Approved → Payment Executed → Receipt Generated.</Text>
      <Text style={styles.meta}>Timeline is informational and replay-backed.</Text>
    </Card>
  );
}

export function OfflineQueuePanel() {
  return (
    <Card title="OfflineQueuePanel">
      <Text style={styles.body}>Pending uploads, retry queue, conflict detection, idempotency keys, duplicate prevention.</Text>
      <Text style={styles.meta}>Safe retries only. No duplicate execution.</Text>
    </Card>
  );
}

export function ReceiptVerificationCard() {
  return (
    <Card title="ReceiptVerificationCard">
      <Text style={styles.body}>Receipt ID, trust hash, NovaTrust signature state, replay evidence.</Text>
      <Text style={styles.meta}>Receipt displays NovaTrust signature state.</Text>
    </Card>
  );
}

export function CommissionSummaryCard() {
  return (
    <Card title="CommissionSummaryCard">
      <Text style={styles.body}>Today, week, month, and quarter commission summaries.</Text>
      <Text style={styles.meta}>Commission is sourced from NovaPay Core.</Text>
    </Card>
  );
}

export function ComplianceAlertPanel() {
  return (
    <Card title="ComplianceAlertPanel">
      {complianceAlerts.map((alert) => (
        <Text key={alert} style={styles.alert}>{alert}</Text>
      ))}
      <Text style={styles.meta}>Alerts originate from NovaPower. UI cannot override holds.</Text>
    </Card>
  );
}

export function NovaAIInsightCard() {
  return (
    <Card title="NovaAIInsightCard">
      <Text style={styles.body}>Float recommendations, queue health, compliance reminders, operational guidance.</Text>
      <Text style={styles.meta}>NovaAI is advisory only and never executes transactions.</Text>
      <Text style={styles.bannerText}>Advisory Only</Text>
    </Card>
  );
}

export function AgentProfileScreen() {
  return (
    <Card title="AgentProfileScreen">
      <Text style={styles.body}>Agent name, branch, role, trust level, biometric status, device trust, pilot mode, version.</Text>
      <Text style={styles.meta}>NovaID identifies. NovaPower authorizes. NovaTrust verifies.</Text>
    </Card>
  );
}

export function AgentHomeDashboard({
  agentName,
  agentId,
  trustLevel,
  deviceTrust,
  syncStatus,
  pendingSync,
  floatBalance,
  walletBalance,
  commissionToday,
}: {
  agentName: string;
  agentId: string;
  trustLevel: "verified" | "review";
  deviceTrust: "trusted" | "review";
  syncStatus: "online" | "pending" | "offline";
  pendingSync: number;
  floatBalance: string;
  walletBalance: string;
  commissionToday: string;
}) {
  return (
    <View style={styles.stack}>
      <Card title="AgentHomeDashboard">
        <Text style={styles.title}>Good morning, {agentName}</Text>
        <Text style={styles.body}>{agentId} · Senior Agent · Verified</Text>
        <Text style={styles.meta}>Float balance: {floatBalance}</Text>
        <Text style={styles.meta}>Wallet balance: {walletBalance}</Text>
        <Text style={styles.meta}>Commission today: {commissionToday}</Text>
        <View style={styles.statusRow}>
          <TrustBadge status={trustLevel} />
          <DeviceTrustChip status={deviceTrust} />
          <SyncStatusChip status={syncStatus} pendingCount={pendingSync} />
        </View>
      </Card>
      <PrimaryActionGrid />
      <CustomerVerificationCard />
      <NovaAIInsightCard />
    </View>
  );
}

export function SendMoneyScreen() {
  const [recipient, setRecipient] = useState("0700000001");
  const [amount, setAmount] = useState("50000");
  const feeEstimate = useMemo(() => Number(amount || "0") * 0.01, [amount]);

  return (
    <Card title="SendMoneyScreen">
      <Text style={styles.body}>Recipient lookup, amount entry, fee estimate, limits, review screen.</Text>
      <Text style={styles.meta}>UI may not calculate settlement, execute ledger writes, approve transactions, or bypass policy checks.</Text>
      <TextInput style={styles.input} value={recipient} onChangeText={setRecipient} placeholder="Recipient" />
      <TextInput style={styles.input} value={amount} onChangeText={setAmount} placeholder="Amount" keyboardType="numeric" />
      <Text style={styles.body}>Fee estimate: {feeEstimate.toFixed(0)}</Text>
      <Text style={styles.meta}>Review screen before NovaPower authorization.</Text>
      <Text style={styles.meta}>NovaPay Core processes the transaction after governed approval.</Text>
    </Card>
  );
}

export function ReceiveMoneyScreen() {
  return (
    <Card title="ReceiveMoneyScreen">
      <Text style={styles.body}>Wallet ID, QR code, payment request, share request.</Text>
      <Text style={styles.meta}>Share via SMS, WhatsApp, email, QR, or link.</Text>
    </Card>
  );
}

export function CashInScreen() {
  return (
    <Card title="CashInScreen">
      <Text style={styles.body}>Customer verification, KYC check, amount, policy validation, confirmation, receipt.</Text>
      <Text style={styles.meta}>NovaID verification required before submission.</Text>
    </Card>
  );
}

export function CashOutScreen() {
  return (
    <Card title="CashOutScreen">
      <Text style={styles.body}>Wallet balance, requested amount, available float, remaining float, PIN, biometric.</Text>
      <Text style={styles.meta}>Check float availability. Request NovaID verification. NovaPower authorization required.</Text>
    </Card>
  );
}

export function QRScannerScreen() {
  return (
    <Card title="QRScannerScreen">
      <Text style={styles.body}>Full screen scanner, autofocus, flashlight, offline decode, scan history.</Text>
      <Text style={styles.meta}>Valid, invalid, trusted, suspicious.</Text>
    </Card>
  );
}

export function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>{title}</Text>
      {children}
    </View>
  );
}

function TabBar({ activeTab, onChange }: { activeTab: AgentTab; onChange: (tab: AgentTab) => void }) {
  const tabs: Array<{ key: AgentTab; label: string }> = [
    { key: "home", label: "Home" },
    { key: "transfers", label: "Transfers" },
    { key: "transactions", label: "Transactions" },
    { key: "float", label: "Float" },
    { key: "profile", label: "Profile" },
  ];

  return (
    <View style={styles.tabRow}>
      {tabs.map((tab) => (
        <Pressable key={tab.key} onPress={() => onChange(tab.key)} style={[styles.tab, activeTab === tab.key ? styles.tabActive : null]}>
          <Text style={styles.tabText}>{tab.label}</Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#10131a" },
  content: { padding: 18, gap: 14 },
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: 12 },
  kicker: { color: "#8bc4ff", fontSize: 12, letterSpacing: 0.8, textTransform: "uppercase" },
  title: { color: "#f7fbff", fontSize: 22, fontWeight: "700" },
  body: { color: "#edf2ff", fontSize: 14, lineHeight: 20 },
  meta: { color: "#a8b3c7", fontSize: 12, marginTop: 4 },
  chip: { color: "#e8f1ff", backgroundColor: "#1b2230", borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6, overflow: "hidden", marginRight: 6, marginBottom: 6 },
  badgeRow: { alignItems: "flex-end" },
  banner: { backgroundColor: "#17324b", borderRadius: 16, padding: 12 },
  bannerText: { color: "#d5e7ff", fontSize: 12, fontWeight: "700" },
  statusRow: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: 8 },
  tabRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  tab: { paddingHorizontal: 12, paddingVertical: 10, backgroundColor: "#1a2130", borderRadius: 14 },
  tabActive: { backgroundColor: "#2d4f77" },
  tabText: { color: "#f5f8ff", fontWeight: "700" },
  stack: { gap: 12 },
  card: { backgroundColor: "#171c27", borderRadius: 20, padding: 16, gap: 8 },
  cardTitle: { color: "#ffffff", fontSize: 18, fontWeight: "700" },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  actionCard: { width: "48%", backgroundColor: "#1c2435", borderRadius: 18, padding: 14, gap: 6 },
  actionTitle: { color: "#ffffff", fontSize: 15, fontWeight: "700" },
  actionDetail: { color: "#a7b5ca", fontSize: 12 },
  input: { backgroundColor: "#0e1320", color: "#ffffff", borderRadius: 14, paddingHorizontal: 12, paddingVertical: 10, borderWidth: 1, borderColor: "#273146" },
  alert: { color: "#ffd579", fontSize: 13, fontWeight: "600" },
});
