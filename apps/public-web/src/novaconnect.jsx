import React, { useMemo, useState } from "react";

const CONNECT_LIFECYCLE = [
  "Discover",
  "Register",
  "Authenticate",
  "Configure",
  "Publish",
  "Test",
  "Monitor",
  "Retry",
  "Certify",
  "Operate",
];

const ROLE_APPS = [
  { title: "Developer Portal", summary: "API discovery, SDKs, documentation, and sandbox tooling." },
  { title: "Partner Portal", summary: "Integration onboarding, approvals, certification, and access management." },
  { title: "Integration Ops", summary: "Webhook health, retry policies, traffic, and incident visibility." },
  { title: "API Product Team", summary: "Versioning, policies, documentation, and release governance." },
  { title: "Security Review", summary: "Scopes, tokens, secrets, abuse signals, and security posture." },
  { title: "Customer Success", summary: "Implementation guidance and partner enablement." },
];

const CAPABILITIES = [
  { title: "API gateway", summary: "Route, throttle, authorize, and observe API traffic." },
  { title: "Webhooks", summary: "Publish event contracts and manage delivery, retries, and signatures." },
  { title: "Partner routing", summary: "Segregate partner access and contract-bound integrations." },
  { title: "SDKs and tooling", summary: "Support documented, versioned integration kits for developers." },
  { title: "Policy enforcement", summary: "Require scopes, approvals, rate limits, and trust checks." },
  { title: "Monitoring", summary: "Measure latency, errors, retries, and integration health." },
];

const TRUST_AND_PLATFORM = [
  { title: "NovaID", summary: "Authenticate developers, partners, and machine-to-machine access." },
  { title: "NovaTrust", summary: "Policy binding, partner verification, audit evidence, and trust scores." },
  { title: "NovaCloud", summary: "Managed runtime for API endpoints, webhooks, and integrations." },
  { title: "NovaData", summary: "Integration metrics, adoption, latency, failures, and reporting." },
  { title: "NovaAI", summary: "Integration guidance, error analysis, and workflow assistance." },
  { title: "NovaFlow", summary: "Automate onboarding, approvals, and lifecycle workflows." },
];

const INTEGRATION_TYPES = [
  "Payments",
  "Commerce",
  "Property",
  "Logistics",
  "Identity",
  "Government",
  "Healthcare",
  "Data",
];

const SAMPLE_INTEGRATIONS = [
  {
    id: "integration-pos",
    title: "POS bridge",
    type: "Commerce",
    partner: "Retail ERP",
    status: "Certified",
    note: "Catalog, inventory, and orders synchronised with the merchant platform.",
  },
  {
    id: "integration-payments",
    title: "Payments webhook",
    type: "Payments",
    partner: "NovaPay",
    status: "Certified",
    note: "Settlement, refund, and chargeback events delivered with signatures.",
  },
  {
    id: "integration-property",
    title: "Property registry sync",
    type: "Property",
    partner: "NovaHouseReach",
    status: "Review",
    note: "Listing, inspection, and ownership events mapped to trust records.",
  },
  {
    id: "integration-logistics",
    title: "Courier tracking bridge",
    type: "Logistics",
    partner: "NovaDashDoor",
    status: "Certified",
    note: "Delivery tracking and proof events delivered in real time.",
  },
  {
    id: "integration-government",
    title: "Permit service link",
    type: "Government",
    partner: "NovaGov",
    status: "Pilot",
    note: "Approval and status events synchronised with citizen workflows.",
  },
];

const API_SURFACES = [
  "REST APIs",
  "GraphQL APIs",
  "Webhooks",
  "SDKs",
  "OpenAPI specs",
  "Partner sandbox",
  "Token management",
  "Scopes and policies",
  "Usage analytics",
];

const AI_FEATURES = [
  { title: "Integration copilot", summary: "Help partners configure endpoints, scopes, and events." },
  { title: "Error analysis", summary: "Explain failures, retries, and webhook delivery issues." },
  { title: "Contract guidance", summary: "Suggest versioning, payload shapes, and backward-compatibility steps." },
  { title: "Traffic insights", summary: "Summarise usage, spikes, and adoption by partner or API." },
  { title: "Certification assistant", summary: "Track readiness, outstanding checks, and integration evidence." },
  { title: "Automation", summary: "Trigger workflows for onboarding, approvals, and release steps." },
];

function Badge({ children, tone = "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function matchesIntegration(integration, filters) {
  const text = `${integration.title} ${integration.type} ${integration.partner} ${integration.status} ${integration.note}`.toLowerCase();
  if (filters.query && !text.includes(filters.query.toLowerCase())) return false;
  if (filters.type !== "All" && integration.type !== filters.type) return false;
  if (filters.status !== "All" && integration.status !== filters.status) return false;
  if (filters.certifiedOnly && integration.status !== "Certified") return false;
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

function IntegrationCard({ integration, navigate }) {
  return (
    <article className="product-card delivery-card">
      <div className="card-top">
        <div>
          <Badge tone="trust">{integration.type}</Badge>
          <h3>{integration.title}</h3>
          <p>{integration.partner}</p>
        </div>
        <Badge tone={integration.status === "Certified" ? "trust" : "warning"}>{integration.status}</Badge>
      </div>
      <p>{integration.note}</p>
      <div className="actions housing-actions">
        <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start integration</button>
        <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open docs</button>
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

export function NovaConnectDetail({ navigate }) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState("All");
  const [status, setStatus] = useState("All");
  const [certifiedOnly, setCertifiedOnly] = useState(false);

  const filteredIntegrations = useMemo(
    () => SAMPLE_INTEGRATIONS.filter((integration) => matchesIntegration(integration, { query, type, status, certifiedOnly })),
    [query, type, status, certifiedOnly],
  );

  return (
    <section className="detail housing-detail">
      <div className="housing-hero">
        <div className="housing-hero-copy">
          <Badge tone="trust">NovaTech integration platform</Badge>
          <h1>NovaConnect</h1>
          <p>
            API gateway, partner integrations, webhooks, SDKs, and policy-controlled contracts for the NovaTech ecosystem.
          </p>
          <div className="actions">
            <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start an integration project</button>
            <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open developer portal</button>
          </div>
          <div className="trust-strip">
            <span>Open APIs and webhooks</span>
            <span>Partner routing and certification</span>
            <span>NovaID · NovaTrust · NovaCloud</span>
            <span>Available</span>
          </div>
        </div>
        <div className="housing-hero-panel">
          <h2>Integration scope</h2>
          <div className="metric-grid">
            <article>
              <strong>10</strong>
              <span>integration lifecycle stages</span>
            </article>
            <article>
              <strong>6</strong>
              <span>role-specific apps</span>
            </article>
            <article>
              <strong>5</strong>
              <span>sample integrations</span>
            </article>
            <article>
              <strong>9</strong>
              <span>API surface families</span>
            </article>
          </div>
          <div className="mini-stack">
            {CONNECT_LIFECYCLE.slice(0, 4).map((item) => (
              <div key={item} className="mini-stack-item">{item}</div>
            ))}
          </div>
        </div>
      </div>

      <section className="band">
        <div className="section-heading">
          <Badge>Lifecycle</Badge>
          <h2>Integration lifecycle from registration to operation</h2>
          <p>NovaConnect is the governed edge for APIs, partners, and event-driven systems.</p>
        </div>
        <div className="grid app-grid">
          {CONNECT_LIFECYCLE.map((step) => <ProductCard key={step} title={step} summary="Managed integration lifecycle stage." />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="info">Applications</Badge>
          <h2>Integration experiences for developers, partners, and operations</h2>
        </div>
        <div className="grid app-grid">
          {ROLE_APPS.map((app) => <ProductCard key={app.title} {...app} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="trust">Capabilities</Badge>
          <h2>Core integration capabilities</h2>
        </div>
        <div className="grid segment-grid">
          {CAPABILITIES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Integrations</Badge>
          <h2>Browse sample integration flows</h2>
          <p>Filter by integration type, certification state, and search terms to inspect the partner graph.</p>
        </div>
        <div className="housing-search">
          <div className="facet-row">
            <label>
              Search
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search integrations, partners, or notes" />
            </label>
            <label>
              Type
              <select value={type} onChange={(event) => setType(event.target.value)}>
                {["All", ...INTEGRATION_TYPES].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                {["All", "Certified", "Review", "Pilot"].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <div>
              <span className="shell-label">Certified only</span>
              <div style={{ marginTop: "8px" }}>
                <FilterChip label={certifiedOnly ? "Certified only: yes" : "Certified only"} active={certifiedOnly} onClick={() => setCertifiedOnly(!certifiedOnly)} />
              </div>
            </div>
          </div>
        </div>
        <div className="grid listing-grid">
          {filteredIntegrations.map((integration) => <IntegrationCard key={integration.id} integration={integration} navigate={navigate} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">API surfaces</Badge>
          <h2>Developer and partner platform capabilities</h2>
        </div>
        <div className="grid integration-grid">
          {API_SURFACES.map((surface) => <ProductCard key={surface} title={surface} summary="Available through governed integration tooling." />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="info">AI and workflow</Badge>
          <h2>AI assistance for integration teams</h2>
        </div>
        <div className="grid integration-grid">
          {AI_FEATURES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="trust">Platform</Badge>
          <h2>NovaConnect works with identity, trust, cloud, and automation</h2>
        </div>
        <div className="grid integration-grid">
          {TRUST_AND_PLATFORM.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>
    </section>
  );
}

