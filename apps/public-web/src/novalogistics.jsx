import React, { useMemo, useState } from "react";

const LOGISTICS_LIFECYCLE = [
  "Request",
  "Quote",
  "Book",
  "Pickup",
  "Sort",
  "Warehouse",
  "Transport",
  "Border clearance",
  "Distribution",
  "Last mile",
  "Delivery",
  "Proof",
  "Returns",
  "Settlement",
  "Analytics",
];

const ROLE_APPS = [
  { title: "Customer App", summary: "Ship parcels, get quotes, schedule pickups, track in real time, and manage returns." },
  { title: "Courier App", summary: "Accept jobs, scan packages, capture proof, manage routes, and track earnings." },
  { title: "Driver App", summary: "Vehicles, compliance, safety, fuel or charging, incident reporting, and communication." },
  { title: "Fleet Manager App", summary: "Fleet overview, GPS, fuel, maintenance, performance, and predictive operations." },
  { title: "Warehouse App", summary: "Receiving, put-away, picking, packing, dispatch staging, and inventory control." },
  { title: "Business Portal", summary: "Shipment creation, bulk shipping, multi-warehouse support, billing, and integrations." },
  { title: "Enterprise Control Center", summary: "Global maps, SLA monitoring, customs, incidents, carbon, and executive KPIs." },
];

const CAPABILITIES = [
  { title: "AI planning", summary: "Demand forecasting, capacity planning, vehicle assignment, inventory optimisation, and workforce planning." },
  { title: "Dynamic routing", summary: "Routing considers distance, traffic, weather, energy, hours, priority, customs, carbon, and restrictions." },
  { title: "Warehouse management", summary: "Inventory, slotting, replenishment, pick-path optimisation, cycle counting, and robotics integration." },
  { title: "Transport management", summary: "Shipment planning, carrier selection, dispatch, load planning, costing, and electronic proof of delivery." },
  { title: "Cross-border flows", summary: "Customs docs, duties, trade compliance, labels, international billing, and border tracking." },
  { title: "Supply chain visibility", summary: "Shipments, packages, containers, vehicles, warehouses, and proof in one audit trail." },
];

const TRUST_AND_PLATFORM = [
  { title: "NovaID", summary: "Verify customers, drivers, fleet operators, warehouse staff, merchants, customs brokers, and agencies." },
  { title: "NovaPay", summary: "Shipping payments, freight invoicing, escrow, settlements, insurance, customs fees, and reconciliation." },
  { title: "NovaTrust", summary: "Verified carriers, chain-of-custody, fraud detection, trust scores, and immutable audit trails." },
  { title: "NovaAI", summary: "Forecasting, route optimisation, disruption alerts, and workflow automation." },
  { title: "NovaData", summary: "Tracking, performance, carbon emissions, profitability, and regional comparisons." },
  { title: "NovaConnect", summary: "REST, GraphQL, webhooks, SDKs, IoT device APIs, ERP, and marketplace integrations." },
];

const FULFILLMENT_STEPS = [
  "Receiving",
  "Put-away",
  "Inventory counts",
  "Picking",
  "Packing",
  "Label printing",
  "Dispatch staging",
  "Returns",
  "Reverse logistics",
  "Cross-docking",
];

const TRANSPORT_MODES = [
  "Cars",
  "Vans",
  "Trucks",
  "Motorcycles",
  "Bicycles",
  "Electric vehicles",
  "Drones",
  "Autonomous robots",
];

const SAMPLE_SHIPMENTS = [
  {
    id: "parcel-1",
    title: "Same-day parcel",
    origin: "CBD Melbourne",
    destination: "Richmond",
    mode: "Courier",
    eta: "36 min",
    status: "In transit",
    priority: "High",
  },
  {
    id: "parcel-2",
    title: "Healthcare sample",
    origin: "Hospital precinct",
    destination: "Laboratory",
    mode: "Cold chain",
    eta: "18 min",
    status: "Scheduled",
    priority: "Critical",
  },
  {
    id: "parcel-3",
    title: "Retail replenishment",
    origin: "Regional warehouse",
    destination: "Merchant store",
    mode: "Van",
    eta: "2h 15m",
    status: "Warehouse staging",
    priority: "Normal",
  },
  {
    id: "parcel-4",
    title: "Cross-border document",
    origin: "Business district",
    destination: "Customs broker",
    mode: "Motorcycle",
    eta: "24 min",
    status: "Proof pending",
    priority: "Priority",
  },
];

function Badge({ children, tone = "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function matchesShipment(shipment, filters) {
  const text = `${shipment.title} ${shipment.origin} ${shipment.destination} ${shipment.mode} ${shipment.status} ${shipment.priority}`.toLowerCase();
  if (filters.query && !text.includes(filters.query.toLowerCase())) return false;
  if (filters.mode !== "All" && shipment.mode !== filters.mode) return false;
  if (filters.status !== "All" && shipment.status !== filters.status) return false;
  if (filters.criticalOnly && shipment.priority !== "Critical") return false;
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

function ShipmentCard({ shipment, navigate }) {
  return (
    <article className="product-card delivery-card">
      <div className="card-top">
        <div>
          <Badge tone="trust">{shipment.mode}</Badge>
          <h3>{shipment.title}</h3>
          <p>{shipment.origin} to {shipment.destination}</p>
        </div>
        <Badge tone={shipment.priority === "Critical" ? "warning" : "info"}>{shipment.status}</Badge>
      </div>
      <dl>
        <div><dt>ETA</dt><dd>{shipment.eta}</dd></div>
        <div><dt>Priority</dt><dd>{shipment.priority}</dd></div>
      </dl>
      <div className="actions housing-actions">
        <button className="button primary" type="button" onClick={() => navigate("/contact")}>Request integration</button>
        <button className="button secondary" type="button" onClick={() => navigate("/trust")}>View trust evidence</button>
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

export function NovaLogisticsDetail({ navigate }) {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("All");
  const [status, setStatus] = useState("All");
  const [criticalOnly, setCriticalOnly] = useState(false);

  const filtered = useMemo(
    () => SAMPLE_SHIPMENTS.filter((shipment) => matchesShipment(shipment, { query, mode, status, criticalOnly })),
    [query, mode, status, criticalOnly],
  );

  return (
    <section className="detail housing-detail">
      <div className="housing-hero">
        <div className="housing-hero-copy">
          <Badge tone="trust">NovaTech logistics operating system</Badge>
          <h1>NovaLogistics X</h1>
          <p>
            AI-powered logistics for parcels, freight, warehouses, fleets, cross-border workflows, and last-mile delivery.
          </p>
          <div className="actions">
            <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start a logistics project</button>
            <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open APIs and SDKs</button>
          </div>
          <div className="trust-strip">
            <span>Transport, warehouse, fleet, and control center apps</span>
            <span>AI routing and planning</span>
            <span>NovaID · NovaPay · NovaTrust</span>
            <span>Private preview</span>
          </div>
        </div>
        <div className="housing-hero-panel">
          <img className="product-hero-logo" src="/brand/NOVALOGISTICS.webp" alt="NovaLogistics logo" />
          <h2>Platform scope</h2>
          <div className="metric-grid">
            <article>
              <strong>15</strong>
              <span>lifecycle stages</span>
            </article>
            <article>
              <strong>7</strong>
              <span>role-specific apps</span>
            </article>
            <article>
              <strong>8</strong>
              <span>transport modes</span>
            </article>
            <article>
              <strong>1</strong>
              <span>digital chain of custody</span>
            </article>
          </div>
          <div className="mini-stack">
            {LOGISTICS_LIFECYCLE.slice(0, 4).map((item) => (
              <div key={item} className="mini-stack-item">{item}</div>
            ))}
          </div>
        </div>
      </div>

      <section className="band">
        <div className="section-heading">
          <Badge>Lifecycle</Badge>
          <h2>Complete logistics lifecycle coverage</h2>
          <p>NovaLogistics is designed to connect request, booking, pickup, warehousing, delivery, proof, settlement, and analytics.</p>
        </div>
        <div className="grid app-grid">
          {LOGISTICS_LIFECYCLE.map((item) => <ProductCard key={item} title={item} summary="Part of the governed logistics lifecycle." />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="info">Applications</Badge>
          <h2>Role-specific apps on the same operational core</h2>
        </div>
        <div className="grid app-grid">
          {ROLE_APPS.map((app) => <ProductCard key={app.title} {...app} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="trust">Capabilities</Badge>
          <h2>Intelligent planning, routing, warehousing, and visibility</h2>
        </div>
        <div className="grid segment-grid">
          {CAPABILITIES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Shipments</Badge>
          <h2>Search a live logistics control view</h2>
          <p>Operators can filter by mode, status, and criticality while keeping the chain of custody visible.</p>
        </div>
        <div className="housing-search">
          <div className="facet-row">
            <label>
              Search
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search shipments, destinations, or priorities" />
            </label>
            <label>
              Mode
              <select value={mode} onChange={(event) => setMode(event.target.value)}>
                {["All", ...TRANSPORT_MODES].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                {["All", "Scheduled", "Warehouse staging", "In transit", "Proof pending"].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <div>
              <span className="shell-label">Critical only</span>
              <div style={{ marginTop: "8px" }}>
                <FilterChip label={criticalOnly ? "Critical only: yes" : "Critical only"} active={criticalOnly} onClick={() => setCriticalOnly(!criticalOnly)} />
              </div>
            </div>
          </div>
        </div>
        <div className="grid listing-grid">
          {filtered.map((shipment) => <ShipmentCard key={shipment.id} shipment={shipment} navigate={navigate} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">AI and routing</Badge>
          <h2>Routing scores that reflect the real logistics problem</h2>
        </div>
        <div className="detail-grid">
          <article>
            <h3>Route score factors</h3>
            <ul>
              <li>Distance</li>
              <li>Traffic</li>
              <li>Weather</li>
              <li>Fuel or energy</li>
              <li>Driver hours</li>
              <li>Cargo priority</li>
              <li>Customer SLA</li>
              <li>Customs delays</li>
              <li>Carbon emissions</li>
              <li>Road restrictions</li>
              <li>Vehicle capacity</li>
            </ul>
          </article>
          <article>
            <h3>AI use cases</h3>
            <ul>
              {[
                "Demand forecasting",
                "Delay prediction",
                "Vehicle failure prediction",
                "Warehouse slotting",
                "Workforce planning",
                "Incident detection",
                "Capacity planning",
                "Disruption alerts",
              ].map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Warehousing and trust</Badge>
          <h2>Operational depth across warehouse, transport, identity, and evidence</h2>
        </div>
        <div className="grid integration-grid">
          {TRUST_AND_PLATFORM.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
        <div className="detail-grid">
          <article>
            <h3>Fulfillment steps</h3>
            <ul>
              {FULFILLMENT_STEPS.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>
          <article>
            <h3>Transport modes</h3>
            <ul>
              {TRANSPORT_MODES.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>
        </div>
      </section>
    </section>
  );
}
