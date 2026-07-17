import React, { useMemo, useState } from "react";

const PLATFORM_SECTIONS = [
  { title: "Food delivery", summary: "Restaurants, cafés, bakeries, fast food, and scheduled meal delivery." },
  { title: "Grocery delivery", summary: "Supermarkets, fresh produce, pantry items, and same-day replenishment." },
  { title: "Pharmacy delivery", summary: "Prescription pickup, OTC medicines, health products, and baby care." },
  { title: "Retail delivery", summary: "Electronics, clothing, home goods, pet supplies, and gifts." },
  { title: "Courier services", summary: "Documents, parcels, business delivery, same-day and scheduled courier." },
  { title: "Business logistics", summary: "Multi-location ordering, invoicing, approvals, catering, and distribution." },
];

const ROLE_APPS = [
  { title: "Customer App", summary: "Discovery, ordering, checkout, wallet, tips, family accounts, and live tracking." },
  { title: "Courier App", summary: "Online/offline status, batching, navigation, proof of pickup, and proof of delivery." },
  { title: "Merchant App", summary: "Store profile, menus, inventory, prep status, promotions, and analytics." },
  { title: "Fleet Manager App", summary: "Driver management, vehicle tracking, maintenance, route planning, and EV analytics." },
  { title: "Business Portal", summary: "Bulk ordering, approvals, catering, invoicing, and expense workflows." },
  { title: "Operations Center", summary: "Live order monitoring, dispatch, fraud, SLA, support, and incident management." },
  { title: "Executive View", summary: "KPI dashboards, profitability, forecast, and carbon reporting." },
];

const AI_FEATURES = [
  { title: "Natural language ordering", summary: "Turn prompts like 'find a vegan dinner under $30' into curated local options." },
  { title: "Smart cart suggestions", summary: "Recommend add-ons, substitutions, and bundle savings before checkout." },
  { title: "Intelligent dispatch", summary: "Route by traffic, prep time, vehicle type, reliability, and SLA constraints." },
  { title: "Predictive ETAs", summary: "Update delivery expectations with traffic, queue, and multi-stop route context." },
  { title: "Demand forecasting", summary: "Anticipate merchant load, courier supply, and peak windows for operations." },
  { title: "Merchant insights", summary: "Surface menu performance, repeat customers, profitability, and peak demand." },
];

const MARKET_CATEGORIES = [
  { title: "Food", summary: "Restaurants, cafés, fast food, fine dining, bakeries, and dessert stores." },
  { title: "Grocery", summary: "Supermarkets, fresh produce, meat, seafood, dairy, pantry, and frozen foods." },
  { title: "Pharmacy", summary: "Prescription pickup, over-the-counter medicines, personal care, and health products." },
  { title: "Retail", summary: "Electronics, clothing, home goods, pet supplies, office supplies, and gifts." },
  { title: "Courier", summary: "Documents, parcels, same-day jobs, business deliveries, and scheduled courier." },
  { title: "Specialty", summary: "Flowers, alcohol where permitted, convenience, and business logistics." },
];

const TRUST_AND_PAYMENTS = [
  { title: "NovaID", summary: "Passkeys, MFA, KYC for couriers, verified merchants, and business verification." },
  { title: "NovaPay", summary: "Wallet, cards, bank transfer, split payments, tips, refunds, loyalty, and payouts." },
  { title: "NovaTrust", summary: "Verified merchants, verified drivers, delivery evidence, fraud detection, and trust scores." },
  { title: "NovaAI", summary: "Ordering copilots, merchant recommendations, and optimisation models." },
  { title: "NovaData", summary: "Orders, revenue, driver performance, heat maps, retention, and emissions analytics." },
  { title: "NovaConnect", summary: "POS, ERP, inventory, accounting, restaurant systems, APIs, webhooks, and SDKs." },
];

const DISPATCH_SCORE = [
  "Distance",
  "Traffic",
  "Preparation time",
  "Courier reliability",
  "Vehicle suitability",
  "Battery or fuel",
  "Weather",
  "Customer priority",
  "SLA commitments",
  "Regulatory constraints",
  "Carbon impact",
  "Multi-order optimisation",
];

const DELIVERY_JOURNEY = [
  "Discover",
  "Cart",
  "Checkout",
  "Dispatch",
  "Pickup",
  "In transit",
  "Proof of delivery",
  "Settlement",
];

const SAMPLE_ORDERS = [
  {
    id: "vegan-dinner",
    title: "Vegan dinner under $30",
    merchant: "Green Table Kitchen",
    category: "Food",
    eta: "28 min",
    total: "$27.80",
    status: "Dispatch ready",
    tags: ["Plant-based", "Low carbon", "Wallet eligible"],
  },
  {
    id: "weekly-groceries",
    title: "Weekly groceries",
    merchant: "NovaFresh Market",
    category: "Grocery",
    eta: "42 min",
    total: "$94.15",
    status: "Batch route",
    tags: ["Family cart", "Same-day", "Saved list"],
  },
  {
    id: "pharmacy-pickup",
    title: "Prescription pickup",
    merchant: "CityCare Pharmacy",
    category: "Pharmacy",
    eta: "18 min",
    total: "$12.00",
    status: "Verified pickup",
    tags: ["ID check", "Contactless", "Trust trail"],
  },
  {
    id: "business-catering",
    title: "Business catering order",
    merchant: "Metro Bites",
    category: "Business",
    eta: "Scheduled",
    total: "$312.50",
    status: "Approval pending",
    tags: ["Invoice", "Scheduled", "Corporate"],
  },
  {
    id: "parcel-drop",
    title: "Same-day parcel",
    merchant: "NovaCourier",
    category: "Courier",
    eta: "51 min",
    total: "$18.90",
    status: "Courier assigned",
    tags: ["Document", "Proof of delivery", "Priority"],
  },
];

function Badge({ children, tone = "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-AU", { style: "currency", currency: "AUD", maximumFractionDigits: 0 }).format(value);
}

function matchesOrder(order, filters) {
  const text = `${order.title} ${order.merchant} ${order.category} ${order.tags.join(" ")}`.toLowerCase();
  if (filters.query && !text.includes(filters.query.toLowerCase())) return false;
  if (filters.category !== "All" && order.category !== filters.category) return false;
  if (filters.status !== "All" && order.status !== filters.status) return false;
  if (filters.fastOnly && !String(order.eta).toLowerCase().includes("min")) return false;
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

function FilterChip({ label, active, onClick }) {
  return (
    <button className={active ? "chip chip-active" : "chip"} type="button" onClick={onClick}>
      {label}
    </button>
  );
}

function OrderCard({ order, navigate }) {
  const total = order.total.startsWith("$") ? order.total : formatMoney(Number(order.total) || 0);
  return (
    <article className="product-card delivery-card">
      <div className="card-top">
        <div>
          <Badge tone="trust">{order.category}</Badge>
          <h3>{order.title}</h3>
          <p>{order.merchant}</p>
        </div>
        <Badge tone={order.status.toLowerCase().includes("ready") || order.status.toLowerCase().includes("assigned") ? "trust" : "warning"}>
          {order.status}
        </Badge>
      </div>
      <dl>
        <div><dt>ETA</dt><dd>{order.eta}</dd></div>
        <div><dt>Total</dt><dd>{total}</dd></div>
      </dl>
      <div className="chip-row">
        {order.tags.map((tag) => <span className="chip" key={tag}>{tag}</span>)}
      </div>
      <div className="actions housing-actions">
        <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start partnership</button>
        <button className="button secondary" type="button" onClick={() => navigate("/trust")}>View trust center</button>
      </div>
    </article>
  );
}

export function NovaDashDoorDetail({ navigate }) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [status, setStatus] = useState("All");
  const [fastOnly, setFastOnly] = useState(false);

  const filteredOrders = useMemo(
    () => SAMPLE_ORDERS.filter((order) => matchesOrder(order, { query, category, status, fastOnly })),
    [query, category, status, fastOnly],
  );

  return (
    <section className="detail housing-detail">
      <div className="housing-hero">
        <div className="housing-hero-copy">
          <Badge tone="trust">NovaTech commerce and logistics OS</Badge>
          <h1>NovaDashDoor</h1>
          <p>
            AI-powered local commerce and last-mile delivery across food, grocery, pharmacy, retail, courier, and business logistics.
          </p>
          <div className="actions">
            <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start a delivery partnership</button>
            <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open APIs and SDKs</button>
          </div>
          <div className="trust-strip">
            <span>Customer, courier, merchant, fleet, and operations apps</span>
            <span>AI dispatch and predictive ETAs</span>
            <span>NovaID · NovaPay · NovaTrust</span>
            <span>Private preview</span>
          </div>
        </div>
        <div className="housing-hero-panel">
          <h2>Platform scope</h2>
          <div className="metric-grid">
            <article>
              <strong>6</strong>
              <span>consumer commerce domains</span>
            </article>
            <article>
              <strong>7</strong>
              <span>role-specific apps</span>
            </article>
            <article>
              <strong>12</strong>
              <span>dispatch factors</span>
            </article>
            <article>
              <strong>1</strong>
              <span>logistics operating core</span>
            </article>
          </div>
          <div className="mini-stack">
            {DELIVERY_JOURNEY.slice(0, 4).map((item) => (
              <div key={item} className="mini-stack-item">{item}</div>
            ))}
          </div>
        </div>
      </div>

      <section className="band">
        <div className="section-heading">
          <Badge>Architecture</Badge>
          <h2>Multi-vertical commerce and last-mile platform</h2>
          <p>One consumer-facing core, one merchant surface, one courier execution layer, and one operations control tower.</p>
        </div>
        <div className="grid app-grid">
          {PLATFORM_SECTIONS.map((section) => <ProductCard key={section.title} {...section} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="info">Applications</Badge>
          <h2>Role-specific apps on the same backend</h2>
        </div>
        <div className="grid app-grid">
          {ROLE_APPS.map((app) => <ProductCard key={app.title} {...app} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="trust">Marketplace</Badge>
          <h2>Categories beyond restaurant delivery</h2>
        </div>
        <div className="grid segment-grid">
          {MARKET_CATEGORIES.map((categoryItem) => <ProductCard key={categoryItem.title} {...categoryItem} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Ordering</Badge>
          <h2>Search and order experience built for local commerce</h2>
          <p>Customers can browse, filter, and reorder across fast-moving commerce categories with trusted checkout and delivery visibility.</p>
        </div>
        <div className="housing-search">
          <div className="facet-row">
            <label>
              Search
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search meals, groceries, parcels, or retailers" />
            </label>
            <label>
              Category
              <select value={category} onChange={(event) => setCategory(event.target.value)}>
                {["All", "Food", "Grocery", "Pharmacy", "Courier", "Business"].map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                {["All", "Dispatch ready", "Batch route", "Verified pickup", "Approval pending", "Courier assigned"].map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>
            <div>
              <span className="shell-label">Fast delivery only</span>
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
          <Badge tone="info">AI and dispatch</Badge>
          <h2>Dispatch scoring that reflects real delivery constraints</h2>
        </div>
        <div className="detail-grid">
          <article>
            <h3>Dispatch factors</h3>
            <ul>
              {DISPATCH_SCORE.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>
          <article>
            <h3>AI capabilities</h3>
            <ul>
              {AI_FEATURES.map((item) => <li key={item.title}><strong>{item.title}:</strong> {item.summary}</li>)}
            </ul>
          </article>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Payments and trust</Badge>
          <h2>Checkout, payouts, and evidence are first-class concerns</h2>
        </div>
        <div className="grid integration-grid">
          {TRUST_AND_PAYMENTS.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">Open platform</Badge>
          <h2>Enterprise integrations and logistics depth</h2>
        </div>
        <div className="detail-grid">
          <article>
            <h3>Integration surfaces</h3>
            <p>POS systems, ERP systems, inventory platforms, accounting software, restaurant systems, APIs, webhooks, and SDKs.</p>
          </article>
          <article>
            <h3>Operational view</h3>
            <p>Live order monitoring, dispatch management, heat maps, driver availability, support, incidents, fraud, SLA, and dashboards.</p>
          </article>
        </div>
      </section>
    </section>
  );
}

