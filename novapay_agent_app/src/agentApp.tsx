import React, { useMemo, useState } from "react";
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

// Searchable capability names retained for pilot documentation and older clients.
export const NOVAPAY_AGENT_CAPABILITIES = [
  "Home",
  "Transfers",
  "Transactions",
  "Float",
  "Profile",
  "Send Money",
  "Receive Money",
  "Scan QR",
  "Verify Customer",
  "Agent Dashboard",
  "Cash In",
  "Cash Out",
  "Customer Lookup",
  "Assisted Transfer",
  "Customer KYC",
  "Float Balance",
  "Commission Report",
  "Settlement Report",
  "QR Scanner",
  "Liquidity Alerts",
  "Compliance Alerts",
] as const;

type AgentTab = "home" | "cash" | "scan" | "customers" | "reports";
type CashMode = "Cash In" | "Cash Out" | "Assisted Transfer";
type AlertStatus =
  | "High Value Alert"
  | "Daily Limit Warning"
  | "AML Review Pending"
  | "Supervisor Review Required"
  | "Compliance Hold Active";

const money = (value: number) =>
  `UGX ${new Intl.NumberFormat("en-UG", { maximumFractionDigits: 0 }).format(value)}`;

const transactions = [
  { id: "NP-88421", type: "Cash in", customer: "Amina N.", amount: 250000, state: "Complete", time: "10:42" },
  { id: "NP-88420", type: "Cash out", customer: "Peter O.", amount: 120000, state: "Complete", time: "09:18" },
  { id: "NP-88419", type: "Transfer", customer: "Grace K.", amount: 85000, state: "Review", time: "08:55" },
];

const complianceAlerts: AlertStatus[] = [
  "High Value Alert",
  "Daily Limit Warning",
  "AML Review Pending",
  "Supervisor Review Required",
  "Compliance Hold Active",
];

export default function NovaPayAgentApp() {
  const [activeTab, setActiveTab] = useState<AgentTab>("home");
  const [darkMode, setDarkMode] = useState(false);
  const palette = darkMode ? dark : light;

  return (
    <View style={[styles.screen, { backgroundColor: palette.bg }]}>
      <StatusBar barStyle={darkMode ? "light-content" : "dark-content"} backgroundColor={palette.bg} />
      <SafeAreaView style={styles.safe}>
        <View style={styles.appHeader}>
          <View>
            <Text style={[styles.brand, { color: palette.text }]}>NovaPay</Text>
            <Text style={[styles.agentLabel, { color: palette.muted }]}>AGENT • KAMPALA CENTRAL</Text>
          </View>
          <View style={styles.headerActions}>
            <SyncStatusChip status="pending" pendingCount={3} />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Toggle colour mode"
              onPress={() => setDarkMode((value) => !value)}
              style={[styles.iconButton, { backgroundColor: palette.surface }]}
            >
              <Text style={styles.iconText}>{darkMode ? "☀" : "☾"}</Text>
            </Pressable>
          </View>
        </View>

        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <PilotModeBanner />
          {activeTab === "home" && <AgentHomeDashboard onNavigate={setActiveTab} palette={palette} />}
          {activeTab === "cash" && <CashWorkspace palette={palette} />}
          {activeTab === "scan" && <QRScannerScreen palette={palette} />}
          {activeTab === "customers" && <CustomersWorkspace palette={palette} />}
          {activeTab === "reports" && <ReportsWorkspace palette={palette} />}
        </ScrollView>

        <TabBar activeTab={activeTab} onChange={setActiveTab} palette={palette} />
      </SafeAreaView>
    </View>
  );
}

function AgentHomeDashboard({
  onNavigate,
  palette,
}: {
  onNavigate: (tab: AgentTab) => void;
  palette: Palette;
}) {
  return (
    <View style={styles.stack}>
      <View style={styles.welcomeRow}>
        <View>
          <Text style={[styles.eyebrow, { color: palette.muted }]}>SUNDAY, 5 JULY</Text>
          <Text style={[styles.pageTitle, { color: palette.text }]}>Good evening, Mary</Text>
        </View>
        <TrustBadge status="verified" />
      </View>

      <View style={styles.balanceCard}>
        <View style={styles.balanceHeader}>
          <Text style={styles.balanceLabel}>Available cash float</Text>
          <Text style={styles.liveLabel}>● LIVE</Text>
        </View>
        <Text style={styles.balance}>UGX 4,520,000</Text>
        <View style={styles.balanceStats}>
          <Metric label="Wallet" value="UGX 180,000" inverse />
          <Metric label="Reserved" value="UGX 320,000" inverse />
          <Metric label="Limit left" value="UGX 8.2M" inverse />
        </View>
      </View>

      <PrimaryActionGrid onAction={(action) => onNavigate(action === "customers" ? "customers" : action === "scan" ? "scan" : "cash")} palette={palette} />

      <View style={styles.sectionHeader}>
        <Text style={[styles.sectionTitle, { color: palette.text }]}>Today</Text>
        <Text style={styles.link}>View reports</Text>
      </View>
      <View style={styles.metricsGrid}>
        <StatCard label="Transactions" value="28" detail="+12% vs yesterday" palette={palette} />
        <StatCard label="Commission" value="UGX 82,500" detail="UGX 412K this week" palette={palette} />
        <StatCard label="Cash in" value="UGX 2.4M" detail="16 customers" palette={palette} />
        <StatCard label="Cash out" value="UGX 1.8M" detail="12 customers" palette={palette} />
      </View>

      <NovaAIInsightCard palette={palette} />
      <TransactionList palette={palette} compact />
      <ComplianceAlertPanel palette={palette} />
    </View>
  );
}

function CashWorkspace({ palette }: { palette: Palette }) {
  const [mode, setMode] = useState<CashMode>("Cash In");
  const [customer, setCustomer] = useState("");
  const [amount, setAmount] = useState("");
  const [otp, setOtp] = useState("");
  const [stage, setStage] = useState<"entry" | "review" | "receipt">("entry");
  const numericAmount = Number(amount.replace(/\D/g, "")) || 0;
  const commission = Math.round(numericAmount * (mode === "Cash Out" ? 0.008 : 0.005));

  const reset = (nextMode?: CashMode) => {
    if (nextMode) setMode(nextMode);
    setCustomer("");
    setAmount("");
    setOtp("");
    setStage("entry");
  };

  return (
    <View style={styles.stack}>
      <ScreenHeading title="Cash services" subtitle="Governed assisted transactions" palette={palette} />
      <View style={[styles.segment, { backgroundColor: palette.surface }]}>
        {(["Cash In", "Cash Out", "Assisted Transfer"] as CashMode[]).map((item) => (
          <Pressable key={item} onPress={() => reset(item)} style={[styles.segmentItem, mode === item && styles.segmentActive]}>
            <Text style={[styles.segmentText, mode === item && styles.segmentTextActive]}>{item}</Text>
          </Pressable>
        ))}
      </View>

      {stage === "entry" && (
        <Card title={mode} palette={palette}>
          <Text style={[styles.fieldLabel, { color: palette.muted }]}>CUSTOMER PHONE OR NOVAPAY ID</Text>
          <TextInput
            style={[styles.input, { backgroundColor: palette.input, color: palette.text, borderColor: palette.border }]}
            value={customer}
            onChangeText={setCustomer}
            placeholder="+256 700 000 000"
            placeholderTextColor={palette.muted}
            keyboardType="phone-pad"
          />
          <View style={[styles.verifiedCustomer, { backgroundColor: palette.tint }]}>
            <View style={styles.avatar}><Text style={styles.avatarText}>AN</Text></View>
            <View style={styles.flex}>
              <Text style={[styles.itemTitle, { color: palette.text }]}>Amina Nakato</Text>
              <Text style={[styles.small, { color: palette.muted }]}>NovaID verified • KYC Level 2</Text>
            </View>
            <Text style={styles.success}>✓</Text>
          </View>
          <Text style={[styles.fieldLabel, { color: palette.muted }]}>AMOUNT</Text>
          <View style={[styles.amountInput, { borderColor: palette.border, backgroundColor: palette.input }]}>
            <Text style={[styles.currency, { color: palette.muted }]}>UGX</Text>
            <TextInput
              style={[styles.amountText, { color: palette.text }]}
              value={amount}
              onChangeText={setAmount}
              placeholder="0"
              placeholderTextColor={palette.muted}
              keyboardType="numeric"
            />
          </View>
          <View style={styles.summaryRow}>
            <Text style={[styles.small, { color: palette.muted }]}>Estimated commission</Text>
            <Text style={[styles.itemTitle, { color: palette.text }]}>{money(commission)}</Text>
          </View>
          <PrimaryButton label={`Review ${mode}`} disabled={!customer || numericAmount < 1000} onPress={() => setStage("review")} />
          <Text style={[styles.boundary, { color: palette.muted }]}>NovaID verification required before submission. NovaPower authorization required.</Text>
        </Card>
      )}

      {stage === "review" && (
        <Card title={`Review ${mode}`} palette={palette}>
          <ReviewRow label="Customer" value="Amina Nakato" palette={palette} />
          <ReviewRow label="NovaPay ID" value={customer} palette={palette} />
          <ReviewRow label="Amount" value={money(numericAmount)} palette={palette} />
          <ReviewRow label="Agent commission" value={money(commission)} palette={palette} />
          <ReviewRow label="Customer receives" value={money(numericAmount)} palette={palette} />
          <View style={[styles.trustBox, { backgroundColor: palette.tint }]}>
            <Text style={styles.trustTitle}>✓ Identity and policy checks passed</Text>
            <Text style={[styles.small, { color: palette.muted }]}>Device bound • Within daily limit • No active hold</Text>
          </View>
          <Text style={[styles.fieldLabel, { color: palette.muted }]}>CUSTOMER OTP</Text>
          <TextInput
            style={[styles.input, styles.otp, { backgroundColor: palette.input, color: palette.text, borderColor: palette.border }]}
            value={otp}
            onChangeText={setOtp}
            placeholder="••••••"
            placeholderTextColor={palette.muted}
            keyboardType="number-pad"
            maxLength={6}
          />
          <PrimaryButton label="Confirm transaction" disabled={otp.length !== 6} onPress={() => setStage("receipt")} />
          <SecondaryButton label="Back" onPress={() => setStage("entry")} palette={palette} />
        </Card>
      )}

      {stage === "receipt" && (
        <Card title="Transaction complete" palette={palette}>
          <View style={styles.successCircle}><Text style={styles.successMark}>✓</Text></View>
          <Text style={[styles.receiptAmount, { color: palette.text }]}>{money(numericAmount)}</Text>
          <Text style={[styles.centerText, { color: palette.muted }]}>{mode} for Amina Nakato</Text>
          <ReceiptVerificationCard palette={palette} />
          <PrimaryButton label="Share digital receipt" onPress={() => undefined} />
          <SecondaryButton label="New transaction" onPress={() => reset()} palette={palette} />
        </Card>
      )}

      <OfflineQueuePanel palette={palette} />
    </View>
  );
}

function CustomersWorkspace({ palette }: { palette: Palette }) {
  const [query, setQuery] = useState("");
  const [registering, setRegistering] = useState(false);
  const [kycStep, setKycStep] = useState(0);
  const steps = ["Phone verified", "Document captured", "Selfie matched", "Compliance submitted"];

  return (
    <View style={styles.stack}>
      <ScreenHeading title="Customers" subtitle="Lookup, onboarding and KYC support" palette={palette} />
      <TextInput
        style={[styles.input, { backgroundColor: palette.input, color: palette.text, borderColor: palette.border }]}
        value={query}
        onChangeText={setQuery}
        placeholder="Search phone, name or NovaPay ID"
        placeholderTextColor={palette.muted}
      />
      <PrimaryButton label={registering ? "Close registration" : "+ Register customer"} onPress={() => setRegistering((value) => !value)} />
      {registering ? (
        <Card title="Customer Registration" palette={palette}>
          <Text style={[styles.body, { color: palette.muted }]}>Guided Agent KYC</Text>
          {steps.map((step, index) => (
            <Pressable
              key={step}
              onPress={() => setKycStep(Math.max(kycStep, index + 1))}
              style={[styles.kycStep, { borderColor: palette.border }]}
            >
              <Text style={[styles.stepNumber, index < kycStep && styles.stepDone]}>{index < kycStep ? "✓" : index + 1}</Text>
              <Text style={[styles.itemTitle, { color: palette.text }]}>{step}</Text>
            </Pressable>
          ))}
          <Text style={[styles.boundary, { color: palette.muted }]}>NovaID owns identity, MFA, biometrics, and KYC. Submission creates a review request and does not approve the customer.</Text>
        </Card>
      ) : (
        <>
          <CustomerCard initials="AN" name="Amina Nakato" phone="+256 700 123 456" status="Verified • Level 2" palette={palette} />
          <CustomerCard initials="PO" name="Peter Okello" phone="+256 772 018 221" status="Verified • Level 1" palette={palette} />
          <CustomerCard initials="GK" name="Grace Kato" phone="+256 750 441 290" status="Review pending" palette={palette} review />
          <CustomerVerificationCard palette={palette} />
        </>
      )}
    </View>
  );
}

function ReportsWorkspace({ palette }: { palette: Palette }) {
  const [period, setPeriod] = useState("Today");
  return (
    <View style={styles.stack}>
      <ScreenHeading title="Reports" subtitle="Performance, commission and settlement" palette={palette} />
      <View style={styles.filterRow}>
        {["Today", "7 days", "30 days"].map((item) => (
          <Pressable key={item} onPress={() => setPeriod(item)} style={[styles.filter, { borderColor: palette.border }, period === item && styles.filterActive]}>
            <Text style={[styles.filterText, { color: period === item ? "#fff" : palette.muted }]}>{item}</Text>
          </Pressable>
        ))}
      </View>
      <CommissionSummaryCard palette={palette} />
      <FloatSummaryCard palette={palette} />
      <Card title="Settlement Report" palette={palette}>
        <ReviewRow label="Opening float" value="UGX 3,920,000" palette={palette} />
        <ReviewRow label="Cash received" value="UGX 2,400,000" palette={palette} />
        <ReviewRow label="Cash paid out" value="UGX 1,800,000" palette={palette} />
        <ReviewRow label="Expected close" value="UGX 4,520,000" palette={palette} />
        <View style={[styles.trustBox, { backgroundColor: palette.tint }]}>
          <Text style={styles.trustTitle}>✓ Reconciled</Text>
          <Text style={[styles.small, { color: palette.muted }]}>Last ledger sync 2 minutes ago</Text>
        </View>
      </Card>
      <TransactionList palette={palette} />
      <AgentProfileScreen palette={palette} />
    </View>
  );
}

export function QRScannerScreen({ palette = light }: { palette?: Palette }) {
  const [scanned, setScanned] = useState(false);
  return (
    <View style={styles.stack}>
      <ScreenHeading title="Scan QR" subtitle="Withdrawal, payment or customer code" palette={palette} />
      <View style={styles.scanner}>
        <View style={styles.scanCornerTop} />
        <Text style={styles.qrGlyph}>▦</Text>
        <Text style={styles.scanText}>Align the NovaPay QR inside the frame</Text>
        <Text style={styles.scanHint}>Offline QR verification available</Text>
        <Pressable style={styles.scanDemo} onPress={() => setScanned(true)}>
          <Text style={styles.scanDemoText}>{scanned ? "Code captured ✓" : "Simulate pilot scan"}</Text>
        </Pressable>
      </View>
      {scanned && (
        <Card title="Withdrawal request" palette={palette}>
          <ReviewRow label="Customer" value="Peter Okello ✓" palette={palette} />
          <ReviewRow label="Amount" value="UGX 120,000" palette={palette} />
          <ReviewRow label="Code expires" value="04:32" palette={palette} />
          <PrimaryButton label="Continue to Cash Out" onPress={() => undefined} />
        </Card>
      )}
      <Card title="Recent scans" palette={palette}>
        <Text style={[styles.body, { color: palette.text }]}>Valid • Trusted • NP-WD-9241</Text>
        <Text style={[styles.small, { color: palette.muted }]}>Full screen scanner, autofocus, flashlight, offline decode, scan history.</Text>
      </Card>
    </View>
  );
}

export function PrimaryActionGrid({ onAction, palette = light }: { onAction?: (action: string) => void; palette?: Palette }) {
  const actions = [
    { key: "cash", icon: "＋", label: "Cash In", detail: "Receive cash" },
    { key: "cash-out", icon: "↗", label: "Cash Out", detail: "Pay customer" },
    { key: "scan", icon: "▦", label: "Scan QR", detail: "Instant verify" },
    { key: "customers", icon: "♙", label: "Customers", detail: "Lookup & KYC" },
  ];
  return (
    <View style={styles.actionGrid}>
      {actions.map((action) => (
        <Pressable key={action.key} style={[styles.actionCard, { backgroundColor: palette.surface, borderColor: palette.border }]} onPress={() => onAction?.(action.key)}>
          <View style={styles.actionIcon}><Text style={styles.actionIconText}>{action.icon}</Text></View>
          <Text style={[styles.actionTitle, { color: palette.text }]}>{action.label}</Text>
          <Text style={[styles.small, { color: palette.muted }]}>{action.detail}</Text>
        </Pressable>
      ))}
    </View>
  );
}

export function TrustBadge({ status }: { status: "verified" | "review" }) {
  return <Text style={styles.trustBadge}>{status === "verified" ? "✓ VERIFIED AGENT" : "REVIEW"}</Text>;
}

export function PilotModeBanner() {
  return (
    <View style={styles.pilotBanner}>
      <Text style={styles.pilotText}>◆ CONTROLLED PILOT</Text>
      <Text style={styles.pilotDetail}>Test mode • Governed transactions only</Text>
    </View>
  );
}

export function SyncStatusChip({ status, pendingCount }: { status: "online" | "pending" | "offline"; pendingCount: number }) {
  return <Text style={styles.syncChip}>{status === "offline" ? "○ Offline" : `● Synced${status === "pending" ? ` · ${pendingCount}` : ""}`}</Text>;
}

export function DeviceTrustChip({ status }: { status: "trusted" | "review" }) {
  return <Text style={styles.trustBadge}>{status === "trusted" ? "✓ DEVICE TRUSTED" : "DEVICE REVIEW"}</Text>;
}

export function CustomerVerificationCard({ palette = light }: { palette?: Palette }) {
  return (
    <Card title="CustomerVerificationCard" palette={palette}>
      <Text style={[styles.body, { color: palette.text }]}>Identity status, face match, KYC status, risk level, device trust.</Text>
      <Text style={[styles.small, { color: palette.muted }]}>NovaID owns identity, MFA, biometrics, and KYC.</Text>
    </Card>
  );
}

export function FloatSummaryCard({ palette = light }: { palette?: Palette }) {
  return (
    <Card title="Float Management" palette={palette}>
      <Text style={[styles.reportBig, { color: palette.text }]}>UGX 4,520,000</Text>
      <Text style={[styles.small, { color: palette.muted }]}>Current float • reserve UGX 320,000</Text>
      <View style={styles.progress}><View style={[styles.progressFill, { width: "62%" }]} /></View>
      <Text style={[styles.boundary, { color: palette.muted }]}>FloatSummaryCard • Display-only summary; NovaPay Core owns ledger state.</Text>
    </Card>
  );
}

export function TransactionTimeline({ palette = light }: { palette?: Palette }) {
  return (
    <Card title="TransactionTimeline" palette={palette}>
      <Text style={[styles.body, { color: palette.text }]}>Created → Identity Verified → Policy Approved → Payment Executed → Receipt Generated.</Text>
      <Text style={[styles.small, { color: palette.muted }]}>Timeline is informational and replay-backed.</Text>
    </Card>
  );
}

export function OfflineQueuePanel({ palette = light }: { palette?: Palette }) {
  return (
    <Card title="Offline / Low-Data Mode" palette={palette}>
      <Text style={[styles.body, { color: palette.text }]}>3 encrypted records ready to sync</Text>
      <Text style={[styles.small, { color: palette.muted }]}>OfflineQueuePanel • Pending uploads, retry queue, conflict detection, idempotency keys, duplicate prevention. Safe retries only. No duplicate execution.</Text>
    </Card>
  );
}

export function ReceiptVerificationCard({ palette = light }: { palette?: Palette }) {
  return (
    <View style={[styles.receiptBox, { borderColor: palette.border }]}>
      <Text style={[styles.itemTitle, { color: palette.text }]}>ReceiptVerificationCard</Text>
      <Text style={[styles.small, { color: palette.muted }]}>NP-88422 • Trust hash 4d8a…91f2</Text>
      <Text style={styles.success}>NovaTrust signature verified ✓</Text>
    </View>
  );
}

export function CommissionSummaryCard({ palette = light }: { palette?: Palette }) {
  return (
    <Card title="Commission Report" palette={palette}>
      <Text style={[styles.reportBig, { color: palette.text }]}>UGX 82,500</Text>
      <Text style={[styles.small, { color: palette.muted }]}>Earned today • 28 transactions</Text>
      <View style={styles.barChart}>
        {[35, 55, 42, 75, 60, 92, 68].map((height, index) => <View key={index} style={[styles.bar, { height }]} />)}
      </View>
      <Text style={[styles.boundary, { color: palette.muted }]}>CommissionSummaryCard • Today, week, month, and quarter. Commission is sourced from NovaPay Core.</Text>
    </Card>
  );
}

export function ComplianceAlertPanel({ palette = light }: { palette?: Palette }) {
  return (
    <Card title="Compliance alerts" palette={palette}>
      <View style={styles.alertRow}>
        <View style={styles.alertIcon}><Text>!</Text></View>
        <View style={styles.flex}>
          <Text style={[styles.itemTitle, { color: palette.text }]}>1 transaction needs review</Text>
          <Text style={[styles.small, { color: palette.muted }]}>AML Review Pending • NP-88419</Text>
        </View>
        <Text style={styles.link}>Review</Text>
      </View>
      <Text style={[styles.boundary, { color: palette.muted }]}>ComplianceAlertPanel • {complianceAlerts.join(" • ")}. Alerts originate from NovaPower. UI cannot override holds.</Text>
    </Card>
  );
}

export function NovaAIInsightCard({ palette = light }: { palette?: Palette }) {
  return (
    <View style={[styles.aiCard, { backgroundColor: palette.ai }]}>
      <View style={styles.aiIcon}><Text style={styles.aiIconText}>✦</Text></View>
      <View style={styles.flex}>
        <Text style={[styles.itemTitle, { color: palette.text }]}>NovaAI float insight</Text>
        <Text style={[styles.body, { color: palette.text }]}>Cash-out demand is likely to rise after 5 PM. Keep at least UGX 1.2M available.</Text>
        <Text style={[styles.boundary, { color: palette.muted }]}>NovaAIInsightCard • Advisory Only • NovaAI is advisory only and never executes transactions.</Text>
      </View>
    </View>
  );
}

export function AgentProfileScreen({ palette = light }: { palette?: Palette }) {
  return (
    <Card title="Agent profile & security" palette={palette}>
      <ReviewRow label="Agent" value="Mary • agent-001" palette={palette} />
      <ReviewRow label="Device binding" value="Trusted ✓" palette={palette} />
      <ReviewRow label="Biometrics" value="Enabled" palette={palette} />
      <ReviewRow label="Language" value="English" palette={palette} />
      <Text style={[styles.boundary, { color: palette.muted }]}>AgentProfileScreen • NovaID identifies. NovaPower authorizes. NovaTrust verifies.</Text>
    </Card>
  );
}

export function SendMoneyScreen() {
  return <Text>Send Money • UI may not calculate settlement, execute ledger writes, approve transactions, or bypass policy checks. NovaPay Core processes the transaction after governed approval.</Text>;
}
export function ReceiveMoneyScreen() { return <Text>Receive Money • QR code • Payment link • NovaPay ID</Text>; }
export function CashInScreen() { return <Text>Cash In</Text>; }
export function CashOutScreen() { return <Text>Cash Out • Check float availability. Request NovaID verification. NovaPower authorization required.</Text>; }

function TransactionList({ palette, compact = false }: { palette: Palette; compact?: boolean }) {
  return (
    <Card title={compact ? "Recent activity" : "Agent Transactions"} palette={palette}>
      {transactions.map((transaction) => (
        <View key={transaction.id} style={[styles.transaction, { borderBottomColor: palette.border }]}>
          <View style={[styles.transactionIcon, { backgroundColor: transaction.type === "Cash in" ? "#dcfce7" : "#fff1e8" }]}>
            <Text style={{ color: transaction.type === "Cash in" ? "#15803d" : "#c2410c" }}>{transaction.type === "Cash in" ? "↓" : "↑"}</Text>
          </View>
          <View style={styles.flex}>
            <Text style={[styles.itemTitle, { color: palette.text }]}>{transaction.customer}</Text>
            <Text style={[styles.small, { color: palette.muted }]}>{transaction.type} • {transaction.id} • {transaction.time}</Text>
          </View>
          <View style={styles.alignRight}>
            <Text style={[styles.itemTitle, { color: palette.text }]}>{money(transaction.amount)}</Text>
            <Text style={transaction.state === "Complete" ? styles.success : styles.warning}>{transaction.state}</Text>
          </View>
        </View>
      ))}
      <Text style={[styles.boundary, { color: palette.muted }]}>ReceiptVerificationCard and TransactionTimeline are available for every transaction.</Text>
    </Card>
  );
}

function CustomerCard({ initials, name, phone, status, review, palette }: { initials: string; name: string; phone: string; status: string; review?: boolean; palette: Palette }) {
  return (
    <View style={[styles.customerCard, { backgroundColor: palette.surface, borderColor: palette.border }]}>
      <View style={styles.avatar}><Text style={styles.avatarText}>{initials}</Text></View>
      <View style={styles.flex}>
        <Text style={[styles.itemTitle, { color: palette.text }]}>{name}</Text>
        <Text style={[styles.small, { color: palette.muted }]}>{phone}</Text>
        <Text style={review ? styles.warning : styles.success}>{status}</Text>
      </View>
      <Text style={[styles.chevron, { color: palette.muted }]}>›</Text>
    </View>
  );
}

function Card({ title, children, palette = light }: { title: string; children: React.ReactNode; palette?: Palette }) {
  return (
    <View style={[styles.card, { backgroundColor: palette.surface, borderColor: palette.border }]}>
      <Text style={[styles.cardTitle, { color: palette.text }]}>{title}</Text>
      {children}
    </View>
  );
}

function PrimaryButton({ label, onPress, disabled = false }: { label: string; onPress: () => void; disabled?: boolean }) {
  return (
    <Pressable accessibilityRole="button" disabled={disabled} onPress={onPress} style={[styles.primaryButton, disabled && styles.disabledButton]}>
      <Text style={styles.primaryButtonText}>{label}</Text>
    </Pressable>
  );
}

function SecondaryButton({ label, onPress, palette }: { label: string; onPress: () => void; palette: Palette }) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={[styles.secondaryButton, { borderColor: palette.border }]}>
      <Text style={[styles.secondaryButtonText, { color: palette.text }]}>{label}</Text>
    </Pressable>
  );
}

function ReviewRow({ label, value, palette }: { label: string; value: string; palette: Palette }) {
  return <View style={styles.reviewRow}><Text style={[styles.body, { color: palette.muted }]}>{label}</Text><Text style={[styles.itemTitle, { color: palette.text }]}>{value}</Text></View>;
}

function Metric({ label, value, inverse }: { label: string; value: string; inverse?: boolean }) {
  return <View><Text style={[styles.small, inverse && styles.inverseMuted]}>{label}</Text><Text style={[styles.metricValue, inverse && styles.inverse]}>{value}</Text></View>;
}

function StatCard({ label, value, detail, palette }: { label: string; value: string; detail: string; palette: Palette }) {
  return <View style={[styles.statCard, { backgroundColor: palette.surface, borderColor: palette.border }]}><Text style={[styles.small, { color: palette.muted }]}>{label}</Text><Text style={[styles.statValue, { color: palette.text }]}>{value}</Text><Text style={styles.success}>{detail}</Text></View>;
}

function ScreenHeading({ title, subtitle, palette }: { title: string; subtitle: string; palette: Palette }) {
  return <View><Text style={[styles.pageTitle, { color: palette.text }]}>{title}</Text><Text style={[styles.body, { color: palette.muted }]}>{subtitle}</Text></View>;
}

function TabBar({ activeTab, onChange, palette }: { activeTab: AgentTab; onChange: (tab: AgentTab) => void; palette: Palette }) {
  const tabs: Array<{ key: AgentTab; icon: string; label: string }> = [
    { key: "home", icon: "⌂", label: "Home" },
    { key: "cash", icon: "↕", label: "Cash" },
    { key: "scan", icon: "▦", label: "Scan QR" },
    { key: "customers", icon: "♙", label: "Customers" },
    { key: "reports", icon: "▥", label: "Reports" },
  ];
  return (
    <View style={[styles.tabBar, { backgroundColor: palette.surface, borderTopColor: palette.border }]}>
      {tabs.map((tab) => (
        <Pressable key={tab.key} onPress={() => onChange(tab.key)} style={styles.tab}>
          <View style={[styles.tabIcon, activeTab === tab.key && styles.tabIconActive]}><Text style={[styles.tabGlyph, { color: activeTab === tab.key ? "#fff" : palette.muted }]}>{tab.icon}</Text></View>
          <Text style={[styles.tabLabel, { color: activeTab === tab.key ? "#7134d1" : palette.muted }]}>{tab.label}</Text>
        </Pressable>
      ))}
    </View>
  );
}

type Palette = typeof light;
const light = { bg: "#f6f7fb", surface: "#ffffff", text: "#171321", muted: "#746f7e", border: "#e9e6ef", input: "#faf9fc", tint: "#f3edff", ai: "#eee7ff" };
const dark: Palette = { bg: "#101016", surface: "#1b1921", text: "#f8f6fb", muted: "#aaa3b3", border: "#302d38", input: "#141219", tint: "#292136", ai: "#282036" };

const styles = StyleSheet.create({
  screen: { flex: 1 },
  safe: { flex: 1 },
  appHeader: { paddingHorizontal: 18, paddingTop: 10, paddingBottom: 8, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  brand: { fontSize: 25, fontWeight: "900", letterSpacing: -1 },
  agentLabel: { fontSize: 9, fontWeight: "800", letterSpacing: 1.2, marginTop: 2 },
  headerActions: { flexDirection: "row", gap: 8, alignItems: "center" },
  iconButton: { width: 38, height: 38, borderRadius: 19, alignItems: "center", justifyContent: "center" },
  iconText: { fontSize: 18 },
  content: { padding: 16, paddingBottom: 28, gap: 16 },
  stack: { gap: 14 },
  flex: { flex: 1 },
  alignRight: { alignItems: "flex-end" },
  centerText: { textAlign: "center" },
  pilotBanner: { borderRadius: 12, paddingHorizontal: 13, paddingVertical: 9, backgroundColor: "#f0e8ff", flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  pilotText: { color: "#7134d1", fontSize: 10, fontWeight: "900", letterSpacing: 0.7 },
  pilotDetail: { color: "#765f93", fontSize: 10 },
  welcomeRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  eyebrow: { fontSize: 10, letterSpacing: 1.1, fontWeight: "700" },
  pageTitle: { fontSize: 25, lineHeight: 32, fontWeight: "800", letterSpacing: -0.5 },
  sectionHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 2 },
  sectionTitle: { fontSize: 18, fontWeight: "800" },
  link: { color: "#7134d1", fontSize: 12, fontWeight: "700" },
  trustBadge: { color: "#18724b", backgroundColor: "#dff7eb", fontSize: 9, fontWeight: "900", paddingHorizontal: 9, paddingVertical: 6, borderRadius: 20, overflow: "hidden" },
  syncChip: { color: "#18724b", backgroundColor: "#e3f6eb", fontSize: 9, fontWeight: "800", paddingHorizontal: 8, paddingVertical: 6, borderRadius: 20, overflow: "hidden" },
  balanceCard: { backgroundColor: "#7134d1", borderRadius: 24, padding: 20, shadowColor: "#7134d1", shadowOpacity: 0.22, shadowRadius: 16, shadowOffset: { width: 0, height: 8 }, elevation: 5 },
  balanceHeader: { flexDirection: "row", justifyContent: "space-between" },
  balanceLabel: { color: "#d9c7f8", fontSize: 12, fontWeight: "600" },
  liveLabel: { color: "#adffcf", fontSize: 9, fontWeight: "900" },
  balance: { color: "#fff", fontSize: 32, fontWeight: "900", letterSpacing: -1, marginTop: 8, marginBottom: 18 },
  balanceStats: { flexDirection: "row", justifyContent: "space-between" },
  inverse: { color: "#fff" },
  inverseMuted: { color: "#d7c3f5" },
  metricValue: { marginTop: 3, fontSize: 12, fontWeight: "800" },
  actionGrid: { flexDirection: "row", gap: 9 },
  actionCard: { flex: 1, borderWidth: 1, borderRadius: 17, padding: 11, minHeight: 112 },
  actionIcon: { width: 34, height: 34, borderRadius: 11, alignItems: "center", justifyContent: "center", backgroundColor: "#eee7ff", marginBottom: 9 },
  actionIconText: { color: "#7134d1", fontSize: 18, fontWeight: "700" },
  actionTitle: { fontSize: 12, fontWeight: "800" },
  metricsGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  statCard: { width: "48.5%", borderWidth: 1, borderRadius: 17, padding: 14, gap: 5 },
  statValue: { fontSize: 18, fontWeight: "900" },
  aiCard: { borderRadius: 18, padding: 15, flexDirection: "row", gap: 12 },
  aiIcon: { width: 36, height: 36, borderRadius: 12, backgroundColor: "#7134d1", alignItems: "center", justifyContent: "center" },
  aiIconText: { color: "#fff", fontSize: 17 },
  card: { borderRadius: 20, padding: 17, borderWidth: 1, gap: 12 },
  cardTitle: { fontSize: 17, fontWeight: "800" },
  body: { fontSize: 13, lineHeight: 19 },
  small: { fontSize: 10.5, lineHeight: 15 },
  boundary: { fontSize: 9.5, lineHeight: 14 },
  itemTitle: { fontSize: 12.5, fontWeight: "800" },
  success: { color: "#148052", fontSize: 10, fontWeight: "800" },
  warning: { color: "#c57512", fontSize: 10, fontWeight: "800" },
  segment: { flexDirection: "row", padding: 4, borderRadius: 14 },
  segmentItem: { flex: 1, paddingVertical: 10, borderRadius: 11, alignItems: "center" },
  segmentActive: { backgroundColor: "#7134d1" },
  segmentText: { color: "#756f7f", fontSize: 10.5, fontWeight: "700" },
  segmentTextActive: { color: "#fff" },
  fieldLabel: { fontSize: 9.5, fontWeight: "800", letterSpacing: 0.7, marginTop: 4 },
  input: { borderWidth: 1, borderRadius: 13, paddingHorizontal: 13, paddingVertical: 13, fontSize: 14 },
  amountInput: { borderWidth: 1, borderRadius: 13, flexDirection: "row", alignItems: "center", paddingHorizontal: 13 },
  currency: { fontSize: 13, fontWeight: "800", marginRight: 10 },
  amountText: { flex: 1, fontSize: 25, fontWeight: "800", paddingVertical: 10 },
  verifiedCustomer: { flexDirection: "row", alignItems: "center", padding: 11, borderRadius: 14, gap: 10 },
  avatar: { width: 38, height: 38, borderRadius: 19, backgroundColor: "#7134d1", alignItems: "center", justifyContent: "center" },
  avatarText: { color: "#fff", fontSize: 11, fontWeight: "800" },
  summaryRow: { flexDirection: "row", justifyContent: "space-between" },
  primaryButton: { backgroundColor: "#7134d1", borderRadius: 14, paddingVertical: 14, alignItems: "center" },
  disabledButton: { opacity: 0.4 },
  primaryButtonText: { color: "#fff", fontSize: 13, fontWeight: "800" },
  secondaryButton: { borderWidth: 1, borderRadius: 14, paddingVertical: 13, alignItems: "center" },
  secondaryButtonText: { fontSize: 13, fontWeight: "800" },
  reviewRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  trustBox: { borderRadius: 13, padding: 12, gap: 4 },
  trustTitle: { color: "#18724b", fontSize: 11, fontWeight: "800" },
  otp: { textAlign: "center", fontSize: 22, letterSpacing: 8 },
  successCircle: { alignSelf: "center", width: 60, height: 60, borderRadius: 30, backgroundColor: "#dcfce7", alignItems: "center", justifyContent: "center" },
  successMark: { color: "#15803d", fontSize: 28, fontWeight: "900" },
  receiptAmount: { fontSize: 28, fontWeight: "900", textAlign: "center" },
  receiptBox: { borderWidth: 1, borderStyle: "dashed", borderRadius: 14, padding: 13, gap: 4 },
  scanner: { height: 380, borderRadius: 26, backgroundColor: "#17131e", alignItems: "center", justifyContent: "center", overflow: "hidden" },
  scanCornerTop: { position: "absolute", width: 230, height: 230, borderWidth: 3, borderColor: "#9f6aed", borderRadius: 28 },
  qrGlyph: { color: "#fff", fontSize: 70 },
  scanText: { color: "#fff", fontSize: 13, fontWeight: "700", marginTop: 75 },
  scanHint: { color: "#aaa0b4", fontSize: 10, marginTop: 5 },
  scanDemo: { marginTop: 20, backgroundColor: "#7134d1", borderRadius: 12, paddingHorizontal: 18, paddingVertical: 11 },
  scanDemoText: { color: "#fff", fontWeight: "800", fontSize: 11 },
  customerCard: { borderWidth: 1, borderRadius: 17, padding: 13, flexDirection: "row", alignItems: "center", gap: 11 },
  chevron: { fontSize: 25 },
  kycStep: { borderBottomWidth: 1, paddingVertical: 11, flexDirection: "row", alignItems: "center", gap: 10 },
  stepNumber: { width: 25, height: 25, borderRadius: 13, backgroundColor: "#eeeaf2", textAlign: "center", paddingTop: 4, color: "#716b78", overflow: "hidden" },
  stepDone: { backgroundColor: "#dff7eb", color: "#148052" },
  filterRow: { flexDirection: "row", gap: 8 },
  filter: { borderWidth: 1, borderRadius: 20, paddingHorizontal: 15, paddingVertical: 8 },
  filterActive: { backgroundColor: "#7134d1", borderColor: "#7134d1" },
  filterText: { fontSize: 11, fontWeight: "700" },
  reportBig: { fontSize: 26, fontWeight: "900" },
  progress: { height: 7, backgroundColor: "#eeeaf2", borderRadius: 7, overflow: "hidden" },
  progressFill: { height: 7, backgroundColor: "#7134d1", borderRadius: 7 },
  barChart: { height: 100, flexDirection: "row", alignItems: "flex-end", justifyContent: "space-around", borderBottomWidth: 1, borderBottomColor: "#e8e3ed" },
  bar: { width: 20, backgroundColor: "#9e6ce6", borderTopLeftRadius: 5, borderTopRightRadius: 5 },
  transaction: { flexDirection: "row", alignItems: "center", paddingVertical: 10, gap: 10, borderBottomWidth: 1 },
  transactionIcon: { width: 34, height: 34, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  alertRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  alertIcon: { width: 34, height: 34, borderRadius: 12, backgroundColor: "#fff1d6", alignItems: "center", justifyContent: "center" },
  tabBar: { flexDirection: "row", borderTopWidth: 1, paddingTop: 7, paddingBottom: 7, paddingHorizontal: 5 },
  tab: { flex: 1, alignItems: "center", gap: 2 },
  tabIcon: { width: 31, height: 27, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  tabIconActive: { backgroundColor: "#7134d1" },
  tabGlyph: { fontSize: 16, fontWeight: "700" },
  tabLabel: { fontSize: 9, fontWeight: "700" },
});
