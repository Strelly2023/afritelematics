import React, { useMemo, useState } from "react";

const COMMERCE_LIFECYCLE = [
  "Discover",
  "Catalog",
  "Inventory sync",
  "Cart",
  "Checkout",
  "Payment",
  "Preparation",
  "Pickup",
  "Delivery",
  "Settlement",
  "Analytics",
  "Retention",
];

const ROLE_APPS = [
  { title: "Merchant App", summary: "Business profile, catalog, inventory, pricing, promotions, and order handling." },
  { title: "Customer App", summary: "Search, browse, cart, checkout, saved items, reorder, and delivery visibility." },
  { title: "Business Portal", summary: "Corporate ordering, approvals, invoices, expense workflows, and bulk purchasing." },
  { title: "Operations Console", summary: "Support, fraud, SLA, incidents, and cross-merchant monitoring." },
  { title: "Retail Admin", summary: "Multi-store management, workforce, product performance, and peak-hour planning." },
  { title: "Developer Portal", summary: "APIs, webhooks, SDKs, POS integration, and commerce automation." },
];

const CAPABILITIES = [
  { title: "Digital storefronts", summary: "Managed commerce pages for restaurants, retailers, and specialty merchants." },
  { title: "Menu and catalog management", summary: "Products, variants, bundles, customisation, pricing, and availability." },
  { title: "Inventory and fulfilment", summary: "Sync stock, route orders, and connect to kitchen, store, and warehouse workflows." },
  { title: "Promotions and loyalty", summary: "Coupons, discounts, rewards, gift cards, and subscription offers." },
  { title: "Checkout and payments", summary: "NovaPay-backed cards, wallet, split payments, refunds, and settlement." },
  { title: "Support and evidence", summary: "Issue handling, receipts, order status, and trust-backed proof records." },
];

const TRUST_AND_PLATFORM = [
  { title: "NovaID", summary: "Verified customers, merchants, employees, and delegated business accounts." },
  { title: "NovaPay", summary: "Wallet, cards, settlement, refunds, loyalty, and subscription billing." },
  { title: "NovaTrust", summary: "Verified merchants, fraud detection, evidence trails, and trust scoring." },
  { title: "NovaAI", summary: "Personalised recommendations, dynamic pricing support, demand forecasting, and support copilot." },
  { title: "NovaData", summary: "Revenue, conversion, retention, basket size, fulfilment, and profitability analytics." },
  { title: "NovaConnect", summary: "POS, ERP, inventory, accounting, webhooks, and commerce automation integrations." },
];

const COMMERCE_TYPES = [
  "Food",
  "Grocery",
  "Pharmacy",
  "Retail",
  "Courier",
  "Specialty",
];

const SAMPLE_MERCHANTS = [
  {
    id: "green-table",
    title: "Green Table Kitchen",
    category: "Food",
    location: "Richmond",
    status: "Open",
    rating: 4.8,
    note: "Fast-moving menu with AI recommendations and scheduled group orders.",
  },
  {
    id: "novafresh",
    title: "NovaFresh Market",
    category: "Grocery",
    location: "Brunswick",
    status: "Open",
    rating: 4.7,
    note: "Inventory sync and same-day basket fulfilment.",
  },
  {
    id: "citycare",
    title: "CityCare Pharmacy",
    category: "Pharmacy",
    location: "CBD",
    status: "Open",
    rating: 4.9,
    note: "Prescription handling, compliant pickup, and identity checks.",
  },
  {
    id: "metro-bites",
    title: "Metro Bites Catering",
    category: "Food",
    location: "Docklands",
    status: "Scheduled",
    rating: 4.6,
    note: "Business catering, bulk ordering, and invoice workflows.",
  },
  {
    id: "prime-electronics",
    title: "Prime Electronics",
    category: "Retail",
    location: "South Melbourne",
    status: "Open",
    rating: 4.5,
    note: "Retail fulfilment with delivery and pick-up options.",
  },
];

const AI_FEATURES = [
  { title: "Natural language ordering", summary: "Turn prompts into search, cart, and checkout flows." },
  { title: "Recommendations", summary: "Suggest products, bundles, upsells, and substitutions based on context." },
  { title: "Demand forecasting", summary: "Predict peak order windows, inventory pressure, and staffing needs." },
  { title: "Dynamic pricing support", summary: "Guide promotions, discounts, and bundle optimisation." },
  { title: "Merchant insights", summary: "Explain repeat customers, conversion, basket size, and peak demand." },
  { title: "Support copilot", summary: "Reduce ticket handling time with order, refund, and evidence lookup." },
];

const ORDER_TYPES = [
  "Standard",
  "Scheduled",
  "Group order",
  "Corporate",
  "Pickup",
  "Delivery",
  "Subscription",
];

const SAMPLE_ORDERS = [
  {
    id: "order-1",
    title: "Family dinner bundle",
    merchant: "Green Table Kitchen",
    type: "Food",
    orderType: "Group order",
    value: "$54.20",
    status: "Ready",
    note: "Custom notes and grouped items included.",
  },
  {
    id: "order-2",
    title: "Weekly grocery basket",
    merchant: "NovaFresh Market",
    type: "Grocery",
    orderType: "Delivery",
    value: "$126.40",
    status: "Processing",
    note: "Inventory synced and substitutions available.",
  },
  {
    id: "order-3",
    title: "Prescription pickup",
    merchant: "CityCare Pharmacy",
    type: "Pharmacy",
    orderType: "Pickup",
    value: "$19.95",
    status: "Verified",
    note: "Identity verified for controlled item collection.",
  },
  {
    id: "order-4",
    title: "Corporate lunch",
    merchant: "Metro Bites Catering",
    type: "Food",
    orderType: "Corporate",
    value: "$245.00",
    status: "Approved",
    note: "Invoice enabled with approval workflow.",
  },
  {
    id: "order-5",
    title: "Accessory bundle",
    merchant: "Prime Electronics",
    type: "Retail",
    orderType: "Standard",
    value: "$89.00",
    status: "Shipped",
    note: "Delivery tracking active.",
  },
];

function Badge({ children, tone = "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function matchesMerchant(merchant, filters) {
  const text = `${merchant.title} ${merchant.category} ${merchant.location} ${merchant.status} ${merchant.note}`.toLowerCase();
  if (filters.query && !text.includes(filters.query.toLowerCase())) return false;
  if (filters.category !== "All" && merchant.category !== filters.category) return false;
  if (filters.status !== "All" && merchant.status !== filters.status) return false;
  if (filters.highRating && merchant.rating < 4.7) return false;
  return true;
}

function matchesOrder(order, filters) {
  const text = `${order.title} ${order.merchant} ${order.type} ${order.orderType} ${order.status} ${order.note}`.toLowerCase();
  if (filters.query && !text.includes(filters.query.toLowerCase())) return false;
  if (filters.type !== "All" && order.type !== filters.type) return false;
  if (filters.orderType !== "All" && order.orderType !== filters.orderType) return false;
  if (filters.fastOnly && order.status !== "Ready" && order.status !== "Shipped") return false;
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

function MerchantCard({ merchant, navigate }) {
  return (
    <article className="product-card delivery-card">
      <div className="card-top">
        <div>
          <Badge tone="trust">{merchant.category}</Badge>
          <h3>{merchant.title}</h3>
          <p>{merchant.location}</p>
        </div>
        <Badge tone={merchant.status === "Open" ? "trust" : "warning"}>{merchant.status}</Badge>
      </div>
      <dl>
        <div><dt>Rating</dt><dd>{merchant.rating}</dd></div>
        <div><dt>Trust</dt><dd>Verified</dd></div>
      </dl>
      <p>{merchant.note}</p>
      <div className="actions housing-actions">
        <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start merchant onboarding</button>
        <button className="button secondary" type="button" onClick={() => navigate("/trust")}>View trust evidence</button>
      </div>
    </article>
  );
}

function OrderCard({ order, navigate }) {
  return (
    <article className="product-card delivery-card">
      <div className="card-top">
        <div>
          <Badge tone="trust">{order.type}</Badge>
          <h3>{order.title}</h3>
          <p>{order.merchant}</p>
        </div>
        <Badge tone={order.status === "Ready" || order.status === "Approved" || order.status === "Shipped" ? "trust" : "warning"}>
          {order.status}
        </Badge>
      </div>
      <dl>
        <div><dt>Order type</dt><dd>{order.orderType}</dd></div>
        <div><dt>Value</dt><dd>{order.value}</dd></div>
      </dl>
      <p>{order.note}</p>
      <div className="actions housing-actions">
        <button className="button primary" type="button" onClick={() => navigate("/contact")}>Open demo flow</button>
        <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open APIs</button>
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

export function NovaCommerceDetail({ navigate }) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [status, setStatus] = useState("All");
  const [highRating, setHighRating] = useState(false);
  const [orderType, setOrderType] = useState("All");
  const [fastOnly, setFastOnly] = useState(false);

  const filteredMerchants = useMemo(
    () => SAMPLE_MERCHANTS.filter((merchant) => matchesMerchant(merchant, { query, category, status, highRating })),
    [query, category, status, highRating],
  );
  const filteredOrders = useMemo(
    () => SAMPLE_ORDERS.filter((order) => matchesOrder(order, { query, type: category, orderType, fastOnly })),
    [query, category, orderType, fastOnly],
  );

  return (
    <section className="detail housing-detail">
      <div className="housing-hero">
        <div className="housing-hero-copy">
          <Badge tone="trust">NovaTech commerce operating system</Badge>
          <h1>NovaCommerce</h1>
          <p>
            Unified local commerce for merchants, customers, and enterprise buyers with catalog, inventory, checkout, and trust.
          </p>
          <div className="actions">
            <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start a commerce project</button>
            <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open commerce APIs</button>
          </div>
          <div className="trust-strip">
            <span>Merchant, customer, and operations apps</span>
            <span>NovaID · NovaPay · NovaTrust</span>
            <span>Private preview</span>
            <span>Commerce, retail, pharmacy, and enterprise-ready</span>
          </div>
        </div>
        <div className="housing-hero-panel">
          <h2>Commerce scope</h2>
          <div className="metric-grid">
            <article>
              <strong>12</strong>
              <span>lifecycle stages</span>
            </article>
            <article>
              <strong>6</strong>
              <span>role-specific apps</span>
            </article>
            <article>
              <strong>5</strong>
              <span>merchant samples</span>
            </article>
            <article>
              <strong>1</strong>
              <span>commerce control plane</span>
            </article>
          </div>
          <div className="mini-stack">
            {COMMERCE_LIFECYCLE.slice(0, 4).map((item) => (
              <div key={item} className="mini-stack-item">{item}</div>
            ))}
          </div>
        </div>
      </div>

      <section className="band">
        <div className="section-heading">
          <Badge>Lifecycle</Badge>
          <h2>Commerce lifecycle from discovery to retention</h2>
          <p>NovaCommerce connects catalog, inventory, checkout, fulfilment, settlement, and repeat purchase flows.</p>
        </div>
        <div className="grid app-grid">
          {COMMERCE_LIFECYCLE.map((step) => <ProductCard key={step} title={step} summary="Managed commerce lifecycle stage." />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="info">Applications</Badge>
          <h2>Role-specific apps for merchants, buyers, and operations</h2>
        </div>
        <div className="grid app-grid">
          {ROLE_APPS.map((app) => <ProductCard key={app.title} {...app} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="trust">Capabilities</Badge>
          <h2>Full-stack commerce building blocks</h2>
        </div>
        <div className="grid segment-grid">
          {CAPABILITIES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Merchants</Badge>
          <h2>Browse merchant examples</h2>
          <p>Filters reflect the real operational needs of commerce: category, status, and quality threshold.</p>
        </div>
        <div className="housing-search">
          <div className="facet-row">
            <label>
              Search
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search merchants, categories, or notes" />
            </label>
            <label>
              Category
              <select value={category} onChange={(event) => setCategory(event.target.value)}>
                {["All", ...COMMERCE_TYPES].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                {["All", "Open", "Scheduled"].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <div>
              <span className="shell-label">High rating only</span>
              <div style={{ marginTop: "8px" }}>
                <FilterChip label={highRating ? "High rating: yes" : "High rating"} active={highRating} onClick={() => setHighRating(!highRating)} />
              </div>
            </div>
          </div>
        </div>
        <div className="grid listing-grid">
          {filteredMerchants.map((merchant) => <MerchantCard key={merchant.id} merchant={merchant} navigate={navigate} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">Orders</Badge>
          <h2>Commerce order flow examples</h2>
        </div>
        <div className="housing-search">
          <div className="facet-row">
            <label>
              Order search
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search orders or merchants" />
            </label>
            <label>
              Order type
              <select value={orderType} onChange={(event) => setOrderType(event.target.value)}>
                {["All", ...ORDER_TYPES].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <div>
              <span className="shell-label">Fast only</span>
              <div style={{ marginTop: "8px" }}>
                <FilterChip label={fastOnly ? "Fast only: yes" : "Fast only"} active={fastOnly} onClick={() => setFastOnly(!fastOnly)} />
              </div>
            </div>
          </div>
        </div>
        <div className="grid listing-grid">
          {filteredOrders.map((order) => <OrderCard key={order.id} order={order} navigate={navigate} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">AI and analytics</Badge>
          <h2>AI assists both merchants and shoppers</h2>
        </div>
        <div className="grid integration-grid">
          {AI_FEATURES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Platform</Badge>
          <h2>Commerce depends on identity, trust, payments, and integrations</h2>
        </div>
        <div className="grid integration-grid">
          {TRUST_AND_PLATFORM.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>
    </section>
  );
}

