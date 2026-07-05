import React, { useState } from "react";
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  type StyleProp,
  type ViewStyle,
  View,
} from "react-native";

type TabKey = "home" | "wallet" | "pay" | "activity" | "profile";
type AuthMode = "sign_in" | "phone" | "email";
type ActivityFilter = "Today" | "Week" | "Month" | "Custom";
type TransferStage = "Recipient" | "Amount" | "Review" | "Authentication" | "Confirmation" | "Receipt";
type Tone = "success" | "info" | "warning" | "danger";
type BalanceItem = { label: string; value: string; meta: string };
type QuickActionItem = { label: string; detail: string; tab: TabKey };
type ServiceItem = { label: string; detail: string };
type InsightCard = { label: string; value: string; detail: string };
type WalletAccount = { label: string; value: string; detail: string; status: string };
type FeedItem = { id: string; title: string; detail: string; amount: string; meta: string; tone: Tone };
type SecurityItem = { label: string; detail: string };
type SupportItem = { label: string; detail: string };
type ReceiptData = { reference: string; recipient: string; amount: string; status: string };

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: "home", label: "Home" },
  { key: "wallet", label: "Wallet" },
  { key: "pay", label: "Pay" },
  { key: "activity", label: "Activity" },
  { key: "profile", label: "Profile" },
];

const quickActions: QuickActionItem[] = [
  { label: "Send Money", detail: "NovaPay user, bank, mobile money", tab: "pay" as const },
  { label: "Receive Money", detail: "QR, link, NovaPay ID", tab: "pay" as const },
  { label: "Scan QR", detail: "Merchant and peer-to-peer", tab: "pay" as const },
  { label: "Pay Bills", detail: "Utility, school, subscriptions", tab: "pay" as const },
  { label: "Airtime", detail: "Top up instantly", tab: "wallet" as const },
  { label: "Top Up Wallet", detail: "Card, bank, mobile money", tab: "wallet" as const },
  { label: "Cash Out", detail: "Agent assisted withdrawal", tab: "wallet" as const },
  { label: "Request Money", detail: "Personal payment request", tab: "pay" as const },
];

const services: ServiceItem[] = [
  { label: "Bank Transfer", detail: "Local rails and beneficiary checks" },
  { label: "International", detail: "Live FX and delivery estimates" },
  { label: "Mobile Money", detail: "Interoperable mobile wallets" },
  { label: "Merchant Pay", detail: "QR-first checkout" },
  { label: "Savings", detail: "Goals and auto-save rules" },
  { label: "Cards", detail: "Virtual and physical controls" },
];

const balances: BalanceItem[] = [
  { label: "Local wallet", value: "UGX 3,482,000", meta: "Available now" },
  { label: "USD wallet", value: "USD 124.20", meta: "Multi-currency ready" },
  { label: "Pending", value: "UGX 48,000", meta: "Incoming transfers" },
];

const walletAccounts: WalletAccount[] = [
  {
    label: "UGX Wallet",
    value: "UGX 3,482,000",
    detail: "Primary spend balance",
    status: "Active",
  },
  {
    label: "USD Wallet",
    value: "USD 124.20",
    detail: "Travel and cross-border payments",
    status: "Ready",
  },
  {
    label: "Savings Vault",
    value: "UGX 620,000",
    detail: "Round-up rules and goals",
    status: "Growing",
  },
];

const transferStages: TransferStage[] = [
  "Recipient",
  "Amount",
  "Review",
  "Authentication",
  "Confirmation",
  "Receipt",
];

const recipientTypes = [
  "NovaPay user",
  "Phone number",
  "QR code",
  "Bank account",
  "Mobile money",
  "International",
];

const insightCards: InsightCard[] = [
  { label: "Monthly spend", value: "UGX 1.24M", detail: "12% below last month" },
  { label: "Budget health", value: "82%", detail: "Essential categories on track" },
  { label: "Savings goal", value: "UGX 2.8M", detail: "65% complete" },
];

const securityItems: SecurityItem[] = [
  { label: "Biometric authentication", detail: "Face ID, fingerprint, device binding" },
  { label: "Two-factor auth", detail: "OTP and trusted device checks" },
  { label: "Session management", detail: "Review active devices and sign out" },
  { label: "Fraud reporting", detail: "Raise a dispute and attach evidence" },
];

const supportItems: SupportItem[] = [
  { label: "Live chat", detail: "Talk to an agent or AI assistant" },
  { label: "FAQ", detail: "Help articles and guided answers" },
  { label: "Ticket tracking", detail: "Monitor disputes and support cases" },
  { label: "Call support", detail: "Escalate urgent account issues" },
];

const feedSeed: FeedItem[] = [
  {
    id: "txn-1",
    title: "Salary received",
    detail: "Acme Payroll",
    amount: "+ UGX 2,100,000",
    meta: "Today, 08:12",
    tone: "success" as const,
  },
  {
    id: "txn-2",
    title: "Merchant payment",
    detail: "NovaMart QR checkout",
    amount: "- UGX 74,500",
    meta: "Today, 10:24",
    tone: "info" as const,
  },
  {
    id: "txn-3",
    title: "Utility bill",
    detail: "City Power",
    amount: "- UGX 89,000",
    meta: "Yesterday, 18:40",
    tone: "warning" as const,
  },
];

export default function App() {
  return (
    <NovaPayErrorBoundary>
      <NovaPayConsumerApp />
    </NovaPayErrorBoundary>
  );
}

function NovaPayConsumerApp() {
  const [authenticated, setAuthenticated] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("sign_in");
  const [activeTab, setActiveTab] = useState<TabKey>("home");
  const [identifier, setIdentifier] = useState("consumer@novapay.test");
  const [secret, setSecret] = useState("1234");
  const [hiddenBalance, setHiddenBalance] = useState(false);
  const [activityFilter, setActivityFilter] = useState<ActivityFilter>("Today");
  const [recipient, setRecipient] = useState("Mama Grace");
  const [amount, setAmount] = useState("125.00");
  const [note, setNote] = useState("Rent support");
  const [selectedRecipientType, setSelectedRecipientType] = useState("NovaPay user");
  const [selectedDelivery, setSelectedDelivery] = useState("Instant wallet transfer");
  const [selectedCurrency, setSelectedCurrency] = useState("UGX");
  const [themeMode, setThemeMode] = useState("System");
  const [language, setLanguage] = useState("English");
  const [latestReceipt, setLatestReceipt] = useState<ReceiptData | null>(null);
  const [feed, setFeed] = useState<FeedItem[]>(feedSeed);

  const sendStages: Array<{ title: TransferStage; detail: string }> = [
    { title: "Recipient", detail: recipient || "Choose a verified recipient" },
    { title: "Amount", detail: `${selectedCurrency} ${amount || "0.00"}` },
    { title: "Review", detail: selectedDelivery },
    { title: "Authentication", detail: "PIN + biometric or OTP" },
    { title: "Confirmation", detail: "Ledger and receipt synced" },
    { title: "Receipt", detail: "Shareable proof of payment" },
  ];

  function handleSignIn() {
    setAuthenticated(true);
    setActiveTab("home");
  }

  function handleCreateAccount() {
    setAuthMode("email");
    setIdentifier("new.user@novapay.test");
  }

  function handleSendMoney() {
    const reference = `np-${Date.now().toString(36).toUpperCase()}`;
    const formattedAmount = `${selectedCurrency} ${amount}`;
    setLatestReceipt({
      reference,
      recipient,
      amount: formattedAmount,
      status: "Completed",
    });
    setFeed((current) => [
      {
        id: reference,
        title: "Money sent",
        detail: `${recipient} via ${selectedDelivery}`,
        amount: `- ${formattedAmount}`,
        meta: "Just now",
        tone: "success" as const,
      },
      ...current,
    ].slice(0, 6));
    setActiveTab("activity");
  }

  function handleQuickAction(tab: TabKey) {
    setActiveTab(tab);
  }

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.decorativeTop} />
      <View style={styles.decorativeOrbOne} />
      <View style={styles.decorativeOrbTwo} />

      {authenticated ? (
        <>
          <View style={styles.topBar}>
            <View>
              <Text style={styles.kicker}>NovaPay Consumer</Text>
              <Text style={styles.topTitle}>Modern money for everyday transfers</Text>
              <Text style={styles.topMeta}>
                {hiddenBalance ? "Balance hidden" : "Multi-currency wallet ready"} • KYC Level 2 • Trusted device
              </Text>
            </View>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={hiddenBalance ? "Show balance" : "Hide balance"}
              onPress={() => setHiddenBalance((value) => !value)}
              style={styles.modeBadge}
            >
              <Text style={styles.modeBadgeLabel}>{hiddenBalance ? "Show" : "Hide"}</Text>
            </Pressable>
          </View>

          <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
            {activeTab === "home" ? (
              <HomeTab
                balances={balances}
                hiddenBalance={hiddenBalance}
                onActionPress={handleQuickAction}
                quickActions={quickActions}
                services={services}
                insightCards={insightCards}
                recentFeed={feed}
              />
            ) : null}

            {activeTab === "wallet" ? (
              <WalletTab
                accounts={walletAccounts}
                selectedCurrency={selectedCurrency}
                onCurrencyChange={setSelectedCurrency}
              />
            ) : null}

            {activeTab === "pay" ? (
              <PayTab
                latestReceipt={latestReceipt}
                note={note}
                amount={amount}
                recipient={recipient}
                selectedDelivery={selectedDelivery}
                selectedRecipientType={selectedRecipientType}
                onAmountChange={setAmount}
                onNoteChange={setNote}
                onRecipientChange={setRecipient}
                onRecipientTypeChange={setSelectedRecipientType}
                onDeliveryChange={setSelectedDelivery}
                onSendMoney={handleSendMoney}
                stageRows={sendStages}
                recipientTypes={recipientTypes}
              />
            ) : null}

            {activeTab === "activity" ? (
              <ActivityTab
                activityFilter={activityFilter}
                onActivityFilterChange={setActivityFilter}
                feed={feed}
                latestReceipt={latestReceipt}
              />
            ) : null}

            {activeTab === "profile" ? (
              <ProfileTab
                language={language}
                onLanguageChange={setLanguage}
                themeMode={themeMode}
                onThemeModeChange={setThemeMode}
                securityItems={securityItems}
                supportItems={supportItems}
              />
            ) : null}
          </ScrollView>

          <View style={styles.bottomDock}>
            <View style={styles.bottomBar}>
              {tabs.map((tab) => {
                const active = tab.key === activeTab;
                return (
                  <Pressable
                    accessibilityRole="tab"
                    accessibilityState={{ selected: active }}
                    key={tab.key}
                    onPress={() => setActiveTab(tab.key)}
                    style={[styles.tab, active ? styles.tabActive : null]}
                  >
                    <Text style={[styles.tabLabel, active ? styles.tabLabelActive : null]}>{tab.label}</Text>
                  </Pressable>
                );
              })}
            </View>

            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Send Money"
              onPress={() => setActiveTab("pay")}
              style={styles.fab}
            >
              <Text style={styles.fabLabel}>Send Money</Text>
            </Pressable>
          </View>
        </>
      ) : (
        <ScrollView contentContainerStyle={styles.authContent} showsVerticalScrollIndicator={false}>
          <View style={styles.authHero}>
            <Text style={styles.kicker}>2026 consumer blueprint</Text>
            <Text style={styles.authTitle}>NovaPay</Text>
            <Text style={styles.authSubtitle}>
              A fast wallet for sending, receiving, saving, paying merchants, and tracking every transfer with a clear receipt trail.
            </Text>
            <View style={styles.heroPills}>
              <Pill label="Multi-currency" tone="info" />
              <Pill label="QR-first" tone="success" />
              <Pill label="Secure by design" tone="warning" />
            </View>
          </View>

          <View style={styles.authCard}>
            <View style={styles.authTabs}>
              <AuthTabButton label="Sign In" active={authMode === "sign_in"} onPress={() => setAuthMode("sign_in")} />
              <AuthTabButton label="Phone" active={authMode === "phone"} onPress={() => setAuthMode("phone")} />
              <AuthTabButton label="Email" active={authMode === "email"} onPress={() => setAuthMode("email")} />
            </View>

            <Text style={styles.fieldLabel}>{authMode === "phone" ? "Phone number" : authMode === "email" ? "Email" : "Phone or email"}</Text>
            <TextInput
              autoCapitalize="none"
              keyboardType={authMode === "phone" ? "phone-pad" : "email-address"}
              placeholder={authMode === "phone" ? "+256 7xx xxx xxx" : "consumer@novapay.test"}
              placeholderTextColor={colors.muted}
              value={identifier}
              onChangeText={setIdentifier}
              style={styles.input}
            />

            <Text style={styles.fieldLabel}>PIN / password</Text>
            <TextInput
              placeholder="Enter your PIN"
              placeholderTextColor={colors.muted}
              secureTextEntry
              value={secret}
              onChangeText={setSecret}
              style={styles.input}
            />

            <View style={styles.authActions}>
              <AppButton label="Sign In" onPress={handleSignIn} />
              <AppButton label="Create Account" onPress={handleCreateAccount} variant="secondary" />
            </View>

            <View style={styles.authFoot}>
              <Text style={styles.authFootText}>Continue with phone, email, PIN, or biometric unlock where supported.</Text>
            </View>
          </View>
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

function HomeTab({
  balances,
  hiddenBalance,
  onActionPress,
  quickActions,
  services,
  insightCards,
  recentFeed,
}: {
  balances: BalanceItem[];
  hiddenBalance: boolean;
  onActionPress: (tab: TabKey) => void;
  quickActions: QuickActionItem[];
  services: ServiceItem[];
  insightCards: InsightCard[];
  recentFeed: FeedItem[];
}) {
  return (
    <View style={styles.stack}>
      <SurfaceCard>
        <View style={styles.balanceHeader}>
          <View>
            <Text style={styles.sectionKicker}>Available balance</Text>
            <Text style={styles.balanceValue}>{hiddenBalance ? "••••••••" : "UGX 3,482,000"}</Text>
            <Text style={styles.balanceMeta}>Pending UGX 48,000 • USD 124.20 • Auto-save active</Text>
          </View>
          <View style={styles.balanceBadge}>
            <Text style={styles.balanceBadgeLabel}>Verified</Text>
          </View>
        </View>

        <View style={styles.balanceRows}>
          {balances.map((item) => (
            <BalanceRow key={item.label} label={item.label} value={hiddenBalance ? "Hidden" : item.value} meta={item.meta} />
          ))}
        </View>
      </SurfaceCard>

      <SurfaceCard>
        <SectionTitle title="Quick actions" subtitle="One tap to the main money tasks" />
        <View style={styles.actionGrid}>
          {quickActions.map((action) => (
            <Pressable
              accessibilityRole="button"
              key={action.label}
              onPress={() => onActionPress(action.tab)}
              style={styles.actionTile}
            >
              <Text style={styles.actionLabel}>{action.label}</Text>
              <Text style={styles.actionDetail}>{action.detail}</Text>
            </Pressable>
          ))}
        </View>
      </SurfaceCard>

      <SurfaceCard>
        <SectionTitle title="Services" subtitle="Everyday payments and savings" />
        <View style={styles.serviceGrid}>
          {services.map((service) => (
            <View key={service.label} style={styles.serviceTile}>
              <Text style={styles.serviceLabel}>{service.label}</Text>
              <Text style={styles.serviceDetail}>{service.detail}</Text>
            </View>
          ))}
        </View>
      </SurfaceCard>

      <View style={styles.insightRow}>
        {insightCards.map((insight) => (
          <SurfaceCard key={insight.label} style={styles.insightCard}>
            <Text style={styles.sectionKicker}>{insight.label}</Text>
            <Text style={styles.insightValue}>{insight.value}</Text>
            <Text style={styles.insightDetail}>{insight.detail}</Text>
          </SurfaceCard>
        ))}
      </View>

      <SurfaceCard>
        <SectionTitle title="AI assistant" subtitle="Natural language help and smart guidance" />
        <Text style={styles.aiPrompt}>“Send 100 dollars to Mama, split the fee, and show me the receipt.”</Text>
        <View style={styles.aiPills}>
          <Pill label="Fraud warnings" tone="warning" />
          <Pill label="Smart recipients" tone="info" />
          <Pill label="Spending insights" tone="success" />
        </View>
      </SurfaceCard>

      <SurfaceCard>
        <SectionTitle title="Recent activity" subtitle="Latest money movement and receipts" />
        <View style={styles.feedList}>
          {recentFeed.map((item) => (
            <ActivityRow key={item.id} {...item} />
          ))}
        </View>
      </SurfaceCard>
    </View>
  );
}

function WalletTab({
  accounts,
  selectedCurrency,
  onCurrencyChange,
}: {
  accounts: WalletAccount[];
  selectedCurrency: string;
  onCurrencyChange: (currency: string) => void;
}) {
  return (
    <View style={styles.stack}>
      <SurfaceCard>
        <SectionTitle title="Wallet" subtitle="Accounts, conversions, and statements" />
        <View style={styles.currencyRow}>
          {["UGX", "USD", "EUR", "GBP", "AUD"].map((currency) => (
            <FilterChip
              key={currency}
              label={currency}
              active={selectedCurrency === currency}
              onPress={() => onCurrencyChange(currency)}
            />
          ))}
        </View>
      </SurfaceCard>

      <SurfaceCard>
        <Text style={styles.sectionKicker}>Accounts</Text>
        <View style={styles.walletStack}>
          {accounts.map((account) => (
            <View key={account.label} style={styles.walletRow}>
              <View>
                <Text style={styles.walletLabel}>{account.label}</Text>
                <Text style={styles.walletDetail}>{account.detail}</Text>
              </View>
              <View style={styles.walletRight}>
                <Text style={styles.walletValue}>{account.value}</Text>
                <Text style={styles.walletStatus}>{account.status}</Text>
              </View>
            </View>
          ))}
        </View>
      </SurfaceCard>

      <View style={styles.walletActions}>
        <ActionCard label="Deposit" detail="Card, bank, or mobile money top-up" />
        <ActionCard label="Withdraw" detail="Cash out via agent or bank rails" />
        <ActionCard label="Convert" detail="Live FX and fee preview" />
        <ActionCard label="Statements" detail="Export PDF or CSV" />
      </View>
    </View>
  );
}

function PayTab({
  latestReceipt,
  note,
  amount,
  recipient,
  selectedDelivery,
  selectedRecipientType,
  onAmountChange,
  onNoteChange,
  onRecipientChange,
  onRecipientTypeChange,
  onDeliveryChange,
  onSendMoney,
  stageRows,
  recipientTypes,
}: {
  latestReceipt: { reference: string; recipient: string; amount: string; status: string } | null;
  note: string;
  amount: string;
  recipient: string;
  selectedDelivery: string;
  selectedRecipientType: string;
  onAmountChange: (value: string) => void;
  onNoteChange: (value: string) => void;
  onRecipientChange: (value: string) => void;
  onRecipientTypeChange: (value: string) => void;
  onDeliveryChange: (value: string) => void;
  onSendMoney: () => void;
  stageRows: Array<{ title: TransferStage; detail: string }>;
  recipientTypes: string[];
}) {
  return (
    <View style={styles.stack}>
      <SurfaceCard>
        <SectionTitle title="Send money" subtitle="Recipient, amount, review, authentication, receipt" />
        <View style={styles.stageRow}>
          {stageRows.map((stage, index) => (
            <View key={stage.title} style={styles.stageChip}>
              <Text style={styles.stageIndex}>{index + 1}</Text>
              <Text style={styles.stageLabel}>{stage.title}</Text>
              <Text style={styles.stageDetail}>{stage.detail}</Text>
            </View>
          ))}
        </View>
      </SurfaceCard>

      <SurfaceCard>
        <Text style={styles.sectionKicker}>Recipient type</Text>
        <View style={styles.chipWrap}>
          {recipientTypes.map((type) => (
            <FilterChip
              key={type}
              label={type}
              active={selectedRecipientType === type}
              onPress={() => onRecipientTypeChange(type)}
            />
          ))}
        </View>

        <Text style={styles.fieldLabel}>Recipient</Text>
        <TextInput
          placeholder="Mama Grace"
          placeholderTextColor={colors.muted}
          value={recipient}
          onChangeText={onRecipientChange}
          style={styles.input}
        />

        <Text style={styles.fieldLabel}>Amount</Text>
        <TextInput
          keyboardType="decimal-pad"
          placeholder="125.00"
          placeholderTextColor={colors.muted}
          value={amount}
          onChangeText={onAmountChange}
          style={styles.input}
        />

        <Text style={styles.fieldLabel}>Note</Text>
        <TextInput
          placeholder="What is it for?"
          placeholderTextColor={colors.muted}
          value={note}
          onChangeText={onNoteChange}
          style={styles.input}
        />

        <Text style={styles.fieldLabel}>Delivery method</Text>
        <View style={styles.chipWrap}>
          {["Instant wallet transfer", "Bank transfer", "Mobile money", "Cash pickup"].map((delivery) => (
            <FilterChip
              key={delivery}
              label={delivery}
              active={selectedDelivery === delivery}
              onPress={() => onDeliveryChange(delivery)}
            />
          ))}
        </View>

        <View style={styles.reviewBox}>
          <Text style={styles.reviewLabel}>Authentication</Text>
          <Text style={styles.reviewValue}>PIN, biometric, or OTP confirmation</Text>
          <Text style={styles.reviewLabel}>Trust layer</Text>
          <Text style={styles.reviewValue}>Verified recipient, proof-of-payment, and receipt replay</Text>
        </View>

        <AppButton label="Send Money" onPress={onSendMoney} />
      </SurfaceCard>

      <View style={styles.paySplit}>
        <SurfaceCard style={styles.splitCard}>
          <SectionTitle title="Receive money" subtitle="QR, link, NovaPay ID, or phone" />
          <View style={styles.chipWrap}>
            {["Personal QR", "Payment link", "NovaPay ID", "Phone number"].map((method) => (
              <Pill key={method} label={method} tone="info" />
            ))}
          </View>
          <Text style={styles.reviewValue}>NovaPay ID: NP-4839-2026</Text>
        </SurfaceCard>

        <SurfaceCard style={styles.splitCard}>
          <SectionTitle title="QR payments" subtitle="Merchant and peer-to-peer checkout" />
          <View style={styles.qrCard}>
            <Text style={styles.qrCode}>NP•QR•2026•88</Text>
            <Text style={styles.qrMeta}>Static and dynamic QR payment support</Text>
          </View>
        </SurfaceCard>
      </View>

      {latestReceipt ? (
        <SurfaceCard>
          <SectionTitle title="Latest receipt" subtitle="Portable proof of payment" />
          <ReceiptBanner receipt={latestReceipt} />
        </SurfaceCard>
      ) : null}
    </View>
  );
}

function ActivityTab({
  activityFilter,
  onActivityFilterChange,
  feed,
  latestReceipt,
}: {
  activityFilter: ActivityFilter;
  onActivityFilterChange: (value: ActivityFilter) => void;
  feed: FeedItem[];
  latestReceipt: ReceiptData | null;
}) {
  return (
    <View style={styles.stack}>
      <SurfaceCard>
        <SectionTitle title="Activity" subtitle="Transactions, receipts, disputes, and status" />
        <View style={styles.filterRow}>
          {(["Today", "Week", "Month", "Custom"] as const).map((filter) => (
            <FilterChip
              key={filter}
              label={filter}
              active={activityFilter === filter}
              onPress={() => onActivityFilterChange(filter)}
            />
          ))}
        </View>
      </SurfaceCard>

      {latestReceipt ? (
        <SurfaceCard>
          <SectionTitle title="Receipt details" subtitle="Latest transfer summary" />
          <ReceiptBanner receipt={latestReceipt} />
        </SurfaceCard>
      ) : null}

      <SurfaceCard>
        <SectionTitle title="Transactions" subtitle="Payments, transfers, bills, and deposits" />
        <View style={styles.feedList}>
          {feed.map((item) => (
            <ActivityRow key={item.id} {...item} />
          ))}
        </View>
      </SurfaceCard>
    </View>
  );
}

function ProfileTab({
  language,
  onLanguageChange,
  themeMode,
  onThemeModeChange,
  securityItems,
  supportItems,
}: {
  language: string;
  onLanguageChange: (value: string) => void;
  themeMode: string;
  onThemeModeChange: (value: string) => void;
  securityItems: SecurityItem[];
  supportItems: SupportItem[];
}) {
  return (
    <View style={styles.stack}>
      <SurfaceCard>
        <SectionTitle title="Security center" subtitle="Protection, device trust, and session control" />
        <View style={styles.infoPillRow}>
          <Pill label="Biometric enabled" tone="success" />
          <Pill label="Trusted device" tone="info" />
          <Pill label="KYC Level 2" tone="warning" />
        </View>
        <View style={styles.settingsList}>
          {securityItems.map((item) => (
            <SettingsRow key={item.label} label={item.label} detail={item.detail} />
          ))}
        </View>
      </SurfaceCard>

      <SurfaceCard>
        <SectionTitle title="Preferences" subtitle="Language, theme, and accessibility" />
        <View style={styles.settingsList}>
          <SettingsRow label="Language" detail={language} />
          <SettingsRow label="Theme" detail={themeMode} />
          <SettingsRow label="Accessibility" detail="Large text and high contrast ready" />
        </View>
        <View style={styles.chipWrap}>
          {["English", "Swahili", "French"].map((value) => (
            <FilterChip key={value} label={value} active={language === value} onPress={() => onLanguageChange(value)} />
          ))}
        </View>
        <View style={styles.chipWrap}>
          {["System", "Light", "Dark"].map((value) => (
            <FilterChip key={value} label={value} active={themeMode === value} onPress={() => onThemeModeChange(value)} />
          ))}
        </View>
      </SurfaceCard>

      <SurfaceCard>
        <SectionTitle title="Linked accounts" subtitle="Cards, bank accounts, beneficiaries" />
        <View style={styles.settingsList}>
          <SettingsRow label="Linked bank accounts" detail="2 verified banks" />
          <SettingsRow label="Linked cards" detail="1 virtual Visa, 1 debit card" />
          <SettingsRow label="Beneficiaries" detail="6 saved recipients" />
        </View>
      </SurfaceCard>

      <SurfaceCard>
        <SectionTitle title="Support" subtitle="Help, disputes, and escalation" />
        <View style={styles.settingsList}>
          {supportItems.map((item) => (
            <SettingsRow key={item.label} label={item.label} detail={item.detail} />
          ))}
        </View>
      </SurfaceCard>
    </View>
  );
}

function ReceiptBanner({
  receipt,
}: {
  receipt: ReceiptData;
}) {
  return (
    <View style={styles.receiptBanner}>
      <View style={styles.receiptHeader}>
        <Text style={styles.receiptTitle}>Transfer completed</Text>
        <Pill label={receipt.status} tone="success" />
      </View>
      <Text style={styles.receiptAmount}>{receipt.amount}</Text>
      <Text style={styles.receiptMeta}>To {receipt.recipient}</Text>
      <Text style={styles.receiptMeta}>Reference {receipt.reference}</Text>
      <Text style={styles.receiptHint}>Tamper-evident digital receipt ready to share or download.</Text>
    </View>
  );
}

function ActivityRow({
  title,
  detail,
  amount,
  meta,
  tone,
}: {
  title: string;
  detail: string;
  amount: string;
  meta: string;
  tone: Tone;
}) {
  return (
    <View style={styles.activityRow}>
      <View style={styles.activityDotWrap}>
        <View style={[styles.activityDot, tone === "success" ? styles.dotSuccess : tone === "warning" ? styles.dotWarning : tone === "danger" ? styles.dotDanger : styles.dotInfo]} />
      </View>
      <View style={styles.activityBody}>
        <Text style={styles.activityTitle}>{title}</Text>
        <Text style={styles.activityDetail}>{detail}</Text>
        <Text style={styles.activityMeta}>{meta}</Text>
      </View>
      <Text style={styles.activityAmount}>{amount}</Text>
    </View>
  );
}

function BalanceRow({ label, value, meta }: { label: string; value: string; meta: string }) {
  return (
    <View style={styles.balanceRow}>
      <View>
        <Text style={styles.balanceRowLabel}>{label}</Text>
        <Text style={styles.balanceRowMeta}>{meta}</Text>
      </View>
      <Text style={styles.balanceRowValue}>{value}</Text>
    </View>
  );
}

function SettingsRow({ label, detail }: { label: string; detail: string }) {
  return (
    <View style={styles.settingsRow}>
      <Text style={styles.settingsLabel}>{label}</Text>
      <Text style={styles.settingsDetail}>{detail}</Text>
    </View>
  );
}

function ActionCard({ label, detail }: { label: string; detail: string }) {
  return (
    <View style={styles.actionCard}>
      <Text style={styles.actionLabel}>{label}</Text>
      <Text style={styles.actionDetail}>{detail}</Text>
    </View>
  );
}

function SectionTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <View style={styles.sectionTitleWrap}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <Text style={styles.sectionSubtitle}>{subtitle}</Text>
    </View>
  );
}

function FilterChip({
  label,
  active,
  onPress,
}: {
  label: string;
  active?: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [
        styles.filterChip,
        active ? styles.filterChipActive : null,
        pressed ? styles.filterChipPressed : null,
      ]}
    >
      <Text style={[styles.filterChipLabel, active ? styles.filterChipLabelActive : null]}>{label}</Text>
    </Pressable>
  );
}

function Pill({ label, tone }: { label: string; tone: "success" | "info" | "warning" }) {
  return (
    <View
      style={[
        styles.pill,
        tone === "success" ? styles.pillSuccess : null,
        tone === "info" ? styles.pillInfo : null,
        tone === "warning" ? styles.pillWarning : null,
      ]}
    >
      <Text style={[styles.pillLabel, tone === "warning" ? styles.pillLabelDark : null]}>{label}</Text>
    </View>
  );
}

function AuthTabButton({
  label,
  active,
  onPress,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      onPress={onPress}
      style={[styles.authTab, active ? styles.authTabActive : null]}
    >
      <Text style={[styles.authTabLabel, active ? styles.authTabLabelActive : null]}>{label}</Text>
    </Pressable>
  );
}

function AppButton({
  label,
  onPress,
  variant = "primary",
}: {
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary";
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [
        styles.appButton,
        variant === "secondary" ? styles.appButtonSecondary : styles.appButtonPrimary,
        pressed ? styles.appButtonPressed : null,
      ]}
    >
      <Text style={[styles.appButtonLabel, variant === "secondary" ? styles.appButtonLabelSecondary : null]}>{label}</Text>
    </Pressable>
  );
}

function SurfaceCard({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return <View style={[styles.surfaceCard, style]}>{children}</View>;
}

class NovaPayErrorBoundary extends React.Component<React.PropsWithChildren, { hasError: boolean }> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <SafeAreaView style={styles.screen}>
          <View style={styles.errorShell}>
            <Text style={styles.authTitle}>NovaPay</Text>
            <Text style={styles.authSubtitle}>
              The app hit a startup issue. Reload the APK to continue.
            </Text>
          </View>
        </SafeAreaView>
      );
    }

    return this.props.children;
  }
}

const colors = {
  background: "#08111a",
  backgroundAlt: "#0c1724",
  border: "rgba(166, 190, 214, 0.18)",
  card: "#0e1d2d",
  cardAlt: "#10283c",
  chip: "#13283b",
  danger: "#f87171",
  foreground: "#f8fafc",
  info: "#7dd3fc",
  ink: "#e2e8f0",
  muted: "#92a7bd",
  primary: "#2dd4bf",
  secondary: "#8b5cf6",
  success: "#34d399",
  warning: "#fbbf24",
};

const styles = StyleSheet.create({
  actionCard: {
    backgroundColor: colors.cardAlt,
    borderColor: colors.border,
    borderRadius: 22,
    borderWidth: 1,
    flex: 1,
    gap: 8,
    minHeight: 108,
    padding: 16,
  },
  actionTile: {
    backgroundColor: colors.cardAlt,
    borderColor: colors.border,
    borderRadius: 22,
    borderWidth: 1,
    gap: 8,
    minHeight: 108,
    padding: 16,
    width: "48%",
  },
  actionDetail: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  actionGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  actionLabel: {
    color: colors.foreground,
    fontSize: 15,
    fontWeight: "900",
  },
  aiPrompt: {
    color: colors.ink,
    fontSize: 16,
    fontStyle: "italic",
    lineHeight: 24,
  },
  aiPills: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  appButton: {
    alignItems: "center",
    borderRadius: 18,
    borderWidth: 1,
    minHeight: 52,
    justifyContent: "center",
    paddingHorizontal: 18,
  },
  appButtonLabel: {
    color: colors.background,
    fontSize: 16,
    fontWeight: "900",
  },
  appButtonLabelSecondary: {
    color: colors.foreground,
  },
  appButtonPressed: {
    opacity: 0.86,
  },
  appButtonPrimary: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  appButtonSecondary: {
    backgroundColor: colors.chip,
    borderColor: colors.border,
  },
  authActions: {
    gap: 12,
  },
  authCard: {
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderRadius: 28,
    borderWidth: 1,
    gap: 16,
    padding: 20,
  },
  authContent: {
    gap: 20,
    padding: 18,
    paddingBottom: 32,
  },
  authFoot: {
    alignItems: "center",
    paddingTop: 4,
  },
  authFootText: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
    textAlign: "center",
  },
  authHero: {
    backgroundColor: "rgba(14, 29, 45, 0.9)",
    borderColor: colors.border,
    borderRadius: 30,
    borderWidth: 1,
    gap: 12,
    padding: 20,
  },
  authSubtitle: {
    color: colors.muted,
    fontSize: 15,
    lineHeight: 22,
  },
  authTab: {
    backgroundColor: colors.chip,
    borderColor: colors.border,
    borderRadius: 999,
    borderWidth: 1,
    flex: 1,
    minHeight: 46,
    justifyContent: "center",
  },
  authTabActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  authTabLabel: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "900",
    textAlign: "center",
  },
  authTabLabelActive: {
    color: colors.background,
  },
  authTabs: {
    flexDirection: "row",
    gap: 10,
  },
  authTitle: {
    color: colors.foreground,
    fontSize: 34,
    fontWeight: "900",
    letterSpacing: -0.4,
  },
  balanceBadge: {
    alignItems: "center",
    backgroundColor: "rgba(52, 211, 153, 0.14)",
    borderColor: "rgba(52, 211, 153, 0.4)",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  balanceBadgeLabel: {
    color: colors.success,
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  balanceHeader: {
    flexDirection: "row",
    gap: 12,
    justifyContent: "space-between",
  },
  balanceMeta: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
    marginTop: 6,
  },
  balanceRow: {
    alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.02)",
    borderColor: colors.border,
    borderRadius: 18,
    borderWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    padding: 14,
  },
  balanceRowLabel: {
    color: colors.foreground,
    fontSize: 15,
    fontWeight: "900",
  },
  balanceRowMeta: {
    color: colors.muted,
    fontSize: 12,
    marginTop: 4,
  },
  balanceRowValue: {
    color: colors.primary,
    fontSize: 14,
    fontWeight: "900",
  },
  balanceRows: {
    gap: 10,
  },
  balanceValue: {
    color: colors.foreground,
    fontSize: 28,
    fontWeight: "900",
    letterSpacing: -0.2,
    marginTop: 4,
  },
  bottomBar: {
    backgroundColor: "rgba(10, 20, 32, 0.94)",
    borderColor: colors.border,
    borderRadius: 24,
    borderWidth: 1,
    flexDirection: "row",
    gap: 8,
    padding: 8,
  },
  bottomDock: {
    bottom: 16,
    gap: 12,
    left: 16,
    position: "absolute",
    right: 16,
  },
  chipWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  content: {
    gap: 16,
    paddingBottom: 160,
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  currencyRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  decorativeOrbOne: {
    backgroundColor: "rgba(45, 212, 191, 0.24)",
    borderRadius: 260,
    height: 220,
    position: "absolute",
    right: -80,
    top: -60,
    width: 220,
  },
  decorativeOrbTwo: {
    backgroundColor: "rgba(139, 92, 246, 0.18)",
    borderRadius: 220,
    bottom: 140,
    height: 180,
    left: -60,
    position: "absolute",
    width: 180,
  },
  decorativeTop: {
    backgroundColor: colors.backgroundAlt,
    height: 220,
    left: 0,
    position: "absolute",
    right: 0,
    top: 0,
  },
  dotDanger: {
    backgroundColor: colors.danger,
  },
  dotInfo: {
    backgroundColor: colors.info,
  },
  dotSuccess: {
    backgroundColor: colors.success,
  },
  dotWarning: {
    backgroundColor: colors.warning,
  },
  errorShell: {
    flex: 1,
    gap: 12,
    justifyContent: "center",
    padding: 24,
  },
  fab: {
    alignItems: "center",
    alignSelf: "center",
    backgroundColor: colors.primary,
    borderRadius: 999,
    paddingHorizontal: 22,
    paddingVertical: 14,
  },
  fabLabel: {
    color: colors.background,
    fontSize: 15,
    fontWeight: "900",
  },
  feedList: {
    gap: 12,
  },
  fieldLabel: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "900",
    marginTop: 4,
  },
  filterChip: {
    backgroundColor: colors.chip,
    borderColor: colors.border,
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterChipLabel: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "900",
  },
  filterChipLabelActive: {
    color: colors.background,
  },
  filterChipPressed: {
    opacity: 0.88,
  },
  filterRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  heroPills: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  infoPillRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  insightCard: {
    flex: 1,
  },
  insightDetail: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  insightRow: {
    flexDirection: "row",
    gap: 10,
  },
  insightValue: {
    color: colors.foreground,
    fontSize: 20,
    fontWeight: "900",
    marginTop: 6,
  },
  input: {
    backgroundColor: colors.chip,
    borderColor: colors.border,
    borderRadius: 18,
    borderWidth: 1,
    color: colors.foreground,
    fontSize: 16,
    minHeight: 52,
    paddingHorizontal: 16,
  },
  kicker: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  modeBadge: {
    alignItems: "center",
    backgroundColor: "rgba(125, 211, 252, 0.14)",
    borderColor: "rgba(125, 211, 252, 0.36)",
    borderRadius: 999,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: 44,
    minWidth: 74,
    paddingHorizontal: 12,
  },
  modeBadgeLabel: {
    color: colors.info,
    fontSize: 13,
    fontWeight: "900",
  },
  paySplit: {
    gap: 16,
  },
  pill: {
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  pillInfo: {
    backgroundColor: "rgba(125, 211, 252, 0.12)",
    borderColor: "rgba(125, 211, 252, 0.3)",
  },
  pillLabel: {
    color: colors.ink,
    fontSize: 11,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  pillLabelDark: {
    color: colors.background,
  },
  pillSuccess: {
    backgroundColor: "rgba(52, 211, 153, 0.12)",
    borderColor: "rgba(52, 211, 153, 0.3)",
  },
  pillWarning: {
    backgroundColor: "rgba(251, 191, 36, 0.14)",
    borderColor: "rgba(251, 191, 36, 0.3)",
  },
  qrCard: {
    alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.03)",
    borderColor: colors.border,
    borderRadius: 22,
    borderWidth: 1,
    gap: 10,
    padding: 20,
  },
  qrCode: {
    color: colors.foreground,
    fontSize: 18,
    fontWeight: "900",
    letterSpacing: 2,
  },
  qrMeta: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
    textAlign: "center",
  },
  receiptAmount: {
    color: colors.foreground,
    fontSize: 24,
    fontWeight: "900",
  },
  receiptBanner: {
    backgroundColor: "rgba(52, 211, 153, 0.08)",
    borderColor: "rgba(52, 211, 153, 0.22)",
    borderRadius: 22,
    borderWidth: 1,
    gap: 8,
    padding: 16,
  },
  receiptHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  receiptHint: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
  },
  receiptMeta: {
    color: colors.ink,
    fontSize: 13,
  },
  receiptTitle: {
    color: colors.foreground,
    fontSize: 16,
    fontWeight: "900",
  },
  reviewBox: {
    backgroundColor: "rgba(255,255,255,0.03)",
    borderColor: colors.border,
    borderRadius: 20,
    borderWidth: 1,
    gap: 8,
    padding: 14,
  },
  reviewLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  reviewValue: {
    color: colors.foreground,
    fontSize: 14,
    lineHeight: 20,
  },
  surfaceCard: {
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderRadius: 28,
    borderWidth: 1,
    gap: 14,
    padding: 18,
  },
  screen: {
    backgroundColor: colors.background,
    flex: 1,
  },
  sectionKicker: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0.8,
    textTransform: "uppercase",
  },
  sectionSubtitle: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
  },
  sectionTitle: {
    color: colors.foreground,
    fontSize: 19,
    fontWeight: "900",
  },
  sectionTitleWrap: {
    gap: 4,
  },
  serviceDetail: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  serviceGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  serviceLabel: {
    color: colors.foreground,
    fontSize: 14,
    fontWeight: "900",
  },
  serviceTile: {
    backgroundColor: colors.chip,
    borderColor: colors.border,
    borderRadius: 18,
    borderWidth: 1,
    gap: 6,
    minHeight: 96,
    padding: 14,
    width: "48%",
  },
  settingsDetail: {
    color: colors.muted,
    fontSize: 13,
    textAlign: "right",
  },
  settingsLabel: {
    color: colors.foreground,
    fontSize: 14,
    fontWeight: "900",
  },
  settingsList: {
    gap: 10,
  },
  settingsRow: {
    alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.03)",
    borderColor: colors.border,
    borderRadius: 18,
    borderWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    padding: 14,
  },
  splitCard: {
    flex: 1,
  },
  stack: {
    gap: 16,
    paddingBottom: 8,
  },
  stageChip: {
    backgroundColor: colors.chip,
    borderColor: colors.border,
    borderRadius: 18,
    borderWidth: 1,
    flexGrow: 1,
    gap: 6,
    minHeight: 108,
    padding: 14,
    width: "48%",
  },
  stageDetail: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  stageIndex: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: "900",
  },
  stageLabel: {
    color: colors.foreground,
    fontSize: 15,
    fontWeight: "900",
  },
  stageRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  tab: {
    alignItems: "center",
    backgroundColor: "transparent",
    borderRadius: 18,
    flex: 1,
    justifyContent: "center",
    minHeight: 46,
  },
  tabActive: {
    backgroundColor: colors.primary,
  },
  tabLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "900",
  },
  tabLabelActive: {
    color: colors.background,
  },
  topBar: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingTop: 10,
  },
  topMeta: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
    marginTop: 4,
    maxWidth: 290,
  },
  topTitle: {
    color: colors.foreground,
    fontSize: 22,
    fontWeight: "900",
    letterSpacing: -0.2,
    marginTop: 6,
    maxWidth: 280,
  },
  walletActions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  walletDetail: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
  },
  walletLabel: {
    color: colors.foreground,
    fontSize: 15,
    fontWeight: "900",
  },
  walletRight: {
    alignItems: "flex-end",
    gap: 4,
  },
  walletRow: {
    alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.03)",
    borderColor: colors.border,
    borderRadius: 18,
    borderWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    padding: 14,
  },
  walletStack: {
    gap: 10,
  },
  walletStatus: {
    color: colors.success,
    fontSize: 12,
    fontWeight: "900",
  },
  walletValue: {
    color: colors.foreground,
    fontSize: 15,
    fontWeight: "900",
  },
  activityAmount: {
    color: colors.foreground,
    fontSize: 14,
    fontWeight: "900",
  },
  activityBody: {
    flex: 1,
    gap: 4,
  },
  activityDetail: {
    color: colors.muted,
    fontSize: 12,
  },
  activityDot: {
    borderRadius: 999,
    height: 12,
    width: 12,
  },
  activityDotWrap: {
    paddingTop: 4,
  },
  activityMeta: {
    color: colors.info,
    fontSize: 12,
    fontWeight: "700",
  },
  activityRow: {
    alignItems: "flex-start",
    backgroundColor: "rgba(255,255,255,0.03)",
    borderColor: colors.border,
    borderRadius: 18,
    borderWidth: 1,
    flexDirection: "row",
    gap: 10,
    padding: 14,
  },
  activityTitle: {
    color: colors.foreground,
    fontSize: 14,
    fontWeight: "900",
  },
  stackSpacer: {
    height: 8,
  },
  syntax: {
    color: colors.muted,
  },
});
