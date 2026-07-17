import React, { useMemo, useState } from "react";

const PAYMENT_LIFECYCLE = [
  "Discover",
  "Wallet setup",
  "Identity verification",
  "Funding",
  "Checkout",
  "Authorization",
  "Settlement",
  "Receipts",
  "Refunds",
  "Reconciliation",
  "Reporting",
  "Rewards",
];

const ROLE_APPS = [
  { title: "Consumer App", summary: "Wallet, cards, bank transfer, split payments, tips, refunds, loyalty, and subscription billing." },
  { title: "Merchant App", summary: "Checkout, invoice management, refunds, settlements, inventory integration, and reporting." },
  { title: "Business Portal", summary: "Corporate accounts, approvals, expense workflows, bulk payments, and invoicing." },
  { title: "Support Console", summary: "Customer support, disputes, risk review, and payment evidence lookup." },
  { title: "Operations Center", summary: "Settlement monitoring, exception handling, fraud detection, and compliance controls." },
  { title: "Developer Portal", summary: "Open APIs, webhooks, SDKs, sandboxing, and integration guidance." },
];

const CAPABILITIES = [
  { title: "Wallet", summary: "Customer and business wallets with stored value, balances, and programmable controls." },
  { title: "Cards and bank transfer", summary: "Checkout support for credit, debit, direct bank transfer, and digital wallets." },
  { title: "Escrow and settlement", summary: "Hold funds, release on completion, and reconcile with evidence-backed settlements." },
  { title: "Refunds and reversals", summary: "Policy-driven refunds, partial reversals, chargeback handling, and audit trails." },
  { title: "Tips and loyalty", summary: "Gratuities, rewards, gift cards, points, and subscription billing." },
  { title: "Multi-currency", summary: "Support for regional payments, settlement views, and financial reporting." },
];

const TRUST_AND_PLATFORM = [
  { title: "NovaID", summary: "Passkeys, MFA, KYC, business verification, and customer verification when required." },
  { title: "NovaTrust", summary: "Fraud detection, verified merchants, trust scores, immutable audit trails, and evidence." },
  { title: "NovaAI", summary: "Fraud scoring, cash-flow insights, merchant recommendations, and support copilots." },
  { title: "NovaData", summary: "Revenue, settlements, disputes, refunds, retention, and financial analytics." },
  { title: "NovaConnect", summary: "Banking, ERP, accounting, merchant systems, webhooks, and SDKs." },
  { title: "NovaCloud", summary: "Reliable, multi-region infrastructure for regulated financial workflows." },
];

const PAYMENT_TYPES = [
  "Wallet",
  "Cards",
  "Bank transfer",
  "Business account",
  "Split payment",
  "Tip",
  "Refund",
  "Gift card",
  "Loyalty reward",
  "Subscription",
];

const SAMPLE_TRANSACTIONS = [
  {
    id: "txn-1",
    title: "Restaurant checkout",
    counterparty: "Green Table Kitchen",
    type: "Card",
    status: "Settled",
    amount: "$34.20",
    note: "Contactless checkout with tip and receipt.",
  },
  {
    id: "txn-2",
    title: "Rent payment",
    counterparty: "Property manager",
    type: "Bank transfer",
    status: "Pending settlement",
    amount: "$2,400.00",
    note: "Scheduled recurring transfer with approval flow.",
  },
  {
    id: "txn-3",
    title: "Merchant payout",
    counterparty: "NovaPay Merchant",
    type: "Wallet",
    status: "Reconciled",
    amount: "$812.56",
    note: "Daily settlement and reconciliation complete.",
  },
  {
    id: "txn-4",
    title: "Split bill",
    counterparty: "Family account",
    type: "Split payment",
    status: "Authorised",
    amount: "$68.00",
    note: "Shared wallet with family contribution.",
  },
  {
    id: "txn-5",
    title: "Refund",
    counterparty: "Retail store",
    type: "Refund",
    status: "Processed",
    amount: "-$26.90",
    note: "Evidence-backed partial refund.",
  },
];

const AI_FEATURES = [
  { title: "Fraud detection", summary: "Score suspicious payment activity, behavioural anomalies, and merchant risk." },
  { title: "Merchant insights", summary: "Summarise sales, cash flow, seasonality, and payment conversion patterns." },
  { title: "Support copilot", summary: "Reduce case handling time with evidence lookup and guided resolution steps." },
  { title: "Cash-flow forecasting", summary: "Predict settlement timing, payout pressure, and account balance movement." },
  { title: "Smart routing", summary: "Choose payment rails based on region, cost, compliance, and reliability." },
  { title: "Risk recommendations", summary: "Suggest step-up verification, limits, or hold policies when risk increases." },
];

function Badge({ children, tone = "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-AU", { style: "currency", currency: "AUD", maximumFractionDigits: 2 }).format(value);
}

function matchesTransaction(transaction, filters) {
  const text = `${transaction.title} ${transaction.counterparty} ${transaction.type} ${transaction.status} ${transaction.note}`.toLowerCase();
  if (filters.query && !text.includes(filters.query.toLowerCase())) return false;
  if (filters.type !== "All" && transaction.type !== filters.type) return false;
  if (filters.status !== "All" && transaction.status !== filters.status) return false;
  if (filters.settledOnly && transaction.status !== "Settled" && transaction.status !== "Reconciled") return false;
  return true;
}

function ProductCard({ title, summary }) {
  return (
    <article className="capability">
      <h3>{title}</h3>
      <p>{summary}</p>
    </article>
  );
}

function TransactionCard({ transaction, navigate }) {
  const parsedAmount = Number(String(transaction.amount).replace(/[^0-9.-]/g, "")) || 0;
  return (
    <article className="product-card delivery-card">
      <div className="card-top">
        <div>
          <Badge tone="trust">{transaction.type}</Badge>
          <h3>{transaction.title}</h3>
          <p>{transaction.counterparty}</p>
        </div>
        <Badge tone={transaction.status === "Settled" || transaction.status === "Reconciled" ? "trust" : "warning"}>{transaction.status}</Badge>
      </div>
      <dl>
        <div><dt>Amount</dt><dd>{transaction.amount.startsWith("-") ? transaction.amount : formatMoney(parsedAmount)}</dd></div>
        <div><dt>Evidence</dt><dd>Linked</dd></div>
      </dl>
      <p>{transaction.note}</p>
      <div className="actions housing-actions">
        <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start integration</button>
        <button className="button secondary" type="button" onClick={() => navigate("/trust")}>Open trust center</button>
      </div>
    </article>
  );
}

function FilterChip({ label, active, onClick }) {
  return (
    <button className={active ? "chip chip-active" : "chip"} type="button" onClick={onClick}>
      {label}
    </button>
  );
}

export function NovaPayDetail({ navigate }) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState("All");
  const [status, setStatus] = useState("All");
  const [settledOnly, setSettledOnly] = useState(false);

  const filteredTransactions = useMemo(
    () => SAMPLE_TRANSACTIONS.filter((transaction) => matchesTransaction(transaction, { query, type, status, settledOnly })),
    [query, type, status, settledOnly],
  );

  return (
    <section className="detail housing-detail">
      <div className="housing-hero">
        <div className="housing-hero-copy">
          <Badge tone="trust">NovaTech payments and financial operations</Badge>
          <h1>NovaPay</h1>
          <p>
            Wallet, cards, bank transfer, business accounts, escrow, loyalty, settlements, and payments intelligence in one platform.
          </p>
          <div className="actions">
            <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start a payments project</button>
            <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open APIs and SDKs</button>
          </div>
          <div className="trust-strip">
            <span>Consumer, merchant, and business flows</span>
            <span>NovaID · NovaTrust · NovaAI</span>
            <span>Private preview</span>
            <span>Multi-currency ready</span>
          </div>
        </div>
        <div className="housing-hero-panel">
          <h2>Payments scope</h2>
          <div className="metric-grid">
            <article>
              <strong>12</strong>
              <span>payment capabilities</span>
            </article>
            <article>
              <strong>6</strong>
              <span>role-specific apps</span>
            </article>
            <article>
              <strong>5</strong>
              <span>live transaction samples</span>
            </article>
            <article>
              <strong>1</strong>
              <span>financial control plane</span>
            </article>
          </div>
          <div className="mini-stack">
            {PAYMENT_LIFECYCLE.slice(0, 4).map((item) => (
              <div key={item} className="mini-stack-item">{item}</div>
            ))}
          </div>
        </div>
      </div>

      <section className="band">
        <div className="section-heading">
          <Badge>Lifecycle</Badge>
          <h2>Payments lifecycle from funding to reconciliation</h2>
          <p>NovaPay is more than checkout. It covers authorisation, settlement, refunds, receipts, rewards, and reporting.</p>
        </div>
        <div className="grid app-grid">
          {PAYMENT_LIFECYCLE.map((step) => <ProductCard key={step} title={step} summary="Governed step in the financial lifecycle." />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="info">Applications</Badge>
          <h2>Role-specific applications on a shared financial core</h2>
        </div>
        <div className="grid app-grid">
          {ROLE_APPS.map((app) => <ProductCard key={app.title} {...app} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="trust">Capabilities</Badge>
          <h2>Financial building blocks that can power every NovaTech product</h2>
        </div>
        <div className="grid segment-grid">
          {CAPABILITIES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Transactions</Badge>
          <h2>Search a governed payment ledger view</h2>
          <p>Operators can filter by type, status, and settlement state while preserving the evidence trail.</p>
        </div>
        <div className="housing-search">
          <div className="facet-row">
            <label>
              Search
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search payments, merchants, or statuses" />
            </label>
            <label>
              Type
              <select value={type} onChange={(event) => setType(event.target.value)}>
                {["All", ...PAYMENT_TYPES].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                {["All", "Settled", "Pending settlement", "Reconciled", "Authorised", "Processed"].map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>
            <div>
              <span className="shell-label">Settled only</span>
              <div style={{ marginTop: "8px" }}>
                <FilterChip label={settledOnly ? "Settled only: yes" : "Settled only"} active={settledOnly} onClick={() => setSettledOnly(!settledOnly)} />
              </div>
            </div>
          </div>
        </div>
        <div className="grid listing-grid">
          {filteredTransactions.map((transaction) => <TransactionCard key={transaction.id} transaction={transaction} navigate={navigate} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">AI and risk</Badge>
          <h2>AI-assisted finance operations with controlled risk</h2>
        </div>
        <div className="grid integration-grid">
          {AI_FEATURES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Trust and platform</Badge>
          <h2>Identity, fraud control, and integrations for regulated money movement</h2>
        </div>
        <div className="grid integration-grid">
          {TRUST_AND_PLATFORM.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>
    </section>
  );
}

