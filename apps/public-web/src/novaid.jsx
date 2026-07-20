import React, { useMemo, useState } from "react";

const IDENTITY_LIFECYCLE = [
  "Discover",
  "Register",
  "Verify",
  "Authenticate",
  "Authorise",
  "Consent",
  "Monitor",
  "Recover",
  "Audit",
];

const ROLE_APPS = [
  { title: "Consumer App", summary: "Profile, passkeys, MFA, device trust, and account recovery." },
  { title: "Business App", summary: "Business verification, employees, roles, policies, and access control." },
  { title: "Partner Portal", summary: "Federated access, integration approvals, and certification workflows." },
  { title: "Employee App", summary: "Internal identity, session monitoring, privileged access, and approvals." },
  { title: "Inspector App", summary: "Identity checks, certificate validation, and evidence capture." },
  { title: "Operations Center", summary: "Risk scoring, suspicious activity, recovery workflows, and audit review." },
];

const CAPABILITIES = [
  { title: "Passkeys", summary: "Phishing-resistant sign-in for users and devices." },
  { title: "MFA", summary: "Second-factor controls for high-risk and regulated actions." },
  { title: "KYC and verification", summary: "Identity verification for customers, couriers, businesses, and partners." },
  { title: "Business verification", summary: "Legal entity validation, role assignment, and delegated administration." },
  { title: "Device trust", summary: "Risk-aware device posture, session trust, and behavioural signals." },
  { title: "Consent management", summary: "User consent records, scopes, revocation, and evidence trails." },
];

const TRUST_AND_PLATFORM = [
  { title: "NovaTrust", summary: "Trust scores, verified status, fraud detection, and immutable audit evidence." },
  { title: "NovaPay", summary: "Verification for regulated money movement and identity-bound settlement workflows." },
  { title: "NovaAI", summary: "Risk scoring, recovery guidance, identity support copilots, and anomaly detection." },
  { title: "NovaData", summary: "Identity events, access analytics, verification metrics, and audit reporting." },
  { title: "NovaConnect", summary: "Open APIs, webhooks, SCIM, SSO, and identity federation integrations." },
  { title: "NovaCloud", summary: "Secure multi-region identity services with controlled data residency." },
];

const IDENTITY_TYPES = [
  "Consumer",
  "Business",
  "Employee",
  "Partner",
  "Courier",
  "Inspector",
  "Agent",
  "Device",
];

const SAMPLE_IDENTITIES = [
  {
    id: "consumer-1",
    name: "Mia Carter",
    type: "Consumer",
    status: "Verified",
    trust: "High",
    lastSeen: "2 min ago",
    note: "Passkey enrolled, MFA enabled, and trusted device active.",
  },
  {
    id: "business-1",
    name: "Green Table Kitchen Pty Ltd",
    type: "Business",
    status: "Verified",
    trust: "High",
    lastSeen: "14 min ago",
    note: "ABN checked, directors verified, and delegated admins approved.",
  },
  {
    id: "partner-1",
    name: "CityCare Pharmacy Partner",
    type: "Partner",
    status: "Pending review",
    trust: "Medium",
    lastSeen: "Today",
    note: "Federated SSO requested, business documents awaiting review.",
  },
  {
    id: "courier-1",
    name: "Driver 2048",
    type: "Courier",
    status: "Verified",
    trust: "High",
    lastSeen: "1 min ago",
    note: "Identity re-check completed before shift start.",
  },
  {
    id: "device-1",
    name: "Rider iPhone 15",
    type: "Device",
    status: "Trusted",
    trust: "High",
    lastSeen: "Now",
    note: "Device trust and location signals are within policy.",
  },
];

const AI_FEATURES = [
  { title: "Risk scoring", summary: "Detect account takeover, fraud signals, and policy drift." },
  { title: "Support copilot", summary: "Guide users through recovery, verification, and secure access flows." },
  { title: "Identity matching", summary: "Connect duplicate records, households, business entities, and device links." },
  { title: "Step-up checks", summary: "Recommend stronger verification for sensitive or high-risk actions." },
  { title: "Compliance automation", summary: "Support jurisdiction-specific checks, evidence, and retention rules." },
  { title: "Session insights", summary: "Monitor active sessions, geolocation, trust posture, and anomalies." },
];

function Badge({ children, tone = "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function matchesIdentity(identity, filters) {
  const text = `${identity.name} ${identity.type} ${identity.status} ${identity.trust} ${identity.note}`.toLowerCase();
  if (filters.query && !text.includes(filters.query.toLowerCase())) return false;
  if (filters.type !== "All" && identity.type !== filters.type) return false;
  if (filters.status !== "All" && identity.status !== filters.status) return false;
  if (filters.highTrust && identity.trust !== "High") return false;
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

function IdentityCard({ identity, navigate }) {
  return (
    <article className="product-card delivery-card">
      <div className="card-top">
        <div>
          <Badge tone="trust">{identity.type}</Badge>
          <h3>{identity.name}</h3>
          <p>{identity.note}</p>
        </div>
        <Badge tone={identity.trust === "High" ? "trust" : "warning"}>{identity.status}</Badge>
      </div>
      <dl>
        <div><dt>Trust</dt><dd>{identity.trust}</dd></div>
        <div><dt>Last seen</dt><dd>{identity.lastSeen}</dd></div>
      </dl>
      <div className="actions housing-actions">
        <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start verification</button>
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

export function NovaIDDetail({ navigate }) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState("All");
  const [status, setStatus] = useState("All");
  const [highTrust, setHighTrust] = useState(false);

  const filteredIdentities = useMemo(
    () => SAMPLE_IDENTITIES.filter((identity) => matchesIdentity(identity, { query, type, status, highTrust })),
    [query, type, status, highTrust],
  );

  return (
    <section className="detail housing-detail">
      <div className="housing-hero">
        <div className="housing-hero-copy">
          <Badge tone="trust">NovaTech identity and access platform</Badge>
          <h1>NovaID</h1>
          <p>
            Unified identity, access, verification, consent, and device trust for every NovaTech product and partner.
          </p>
          <div className="actions">
            <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start an identity project</button>
            <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open identity APIs</button>
          </div>
          <div className="trust-strip">
            <span>Passkeys and MFA</span>
            <span>Consumer, business, partner, and device identity</span>
            <span>NovaTrust · NovaPay · NovaAI</span>
            <span>Partner access and private preview</span>
          </div>
        </div>
        <div className="housing-hero-panel">
          <img className="product-hero-logo" src="/brand/NOVAID.webp" alt="NovaID logo" />
          <h2>Identity scope</h2>
          <div className="metric-grid">
            <article>
              <strong>9</strong>
              <span>identity lifecycle stages</span>
            </article>
            <article>
              <strong>6</strong>
              <span>role-specific apps</span>
            </article>
            <article>
              <strong>8</strong>
              <span>identity types</span>
            </article>
            <article>
              <strong>1</strong>
              <span>trusted identity fabric</span>
            </article>
          </div>
          <div className="mini-stack">
            {IDENTITY_LIFECYCLE.slice(0, 4).map((item) => (
              <div key={item} className="mini-stack-item">{item}</div>
            ))}
          </div>
        </div>
      </div>

      <section className="band">
        <div className="section-heading">
          <Badge>Lifecycle</Badge>
          <h2>Identity lifecycle from registration to audit</h2>
          <p>NovaID is the entry point for sign-in, verification, consent, and trusted access across the NovaTech ecosystem.</p>
        </div>
        <div className="grid app-grid">
          {IDENTITY_LIFECYCLE.map((step) => <ProductCard key={step} title={step} summary="Managed identity lifecycle stage." />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="info">Applications</Badge>
          <h2>Identity applications for every participant type</h2>
        </div>
        <div className="grid app-grid">
          {ROLE_APPS.map((app) => <ProductCard key={app.title} {...app} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="trust">Capabilities</Badge>
          <h2>Foundational identity capabilities</h2>
        </div>
        <div className="grid segment-grid">
          {CAPABILITIES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Identities</Badge>
          <h2>Search a governed identity inventory</h2>
          <p>Operational users can inspect verified identities, trust state, and recent activity before taking privileged action.</p>
        </div>
        <div className="housing-search">
          <div className="facet-row">
            <label>
              Search
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search names, types, or statuses" />
            </label>
            <label>
              Type
              <select value={type} onChange={(event) => setType(event.target.value)}>
                {["All", ...IDENTITY_TYPES].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                {["All", "Verified", "Pending review", "Trusted"].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <div>
              <span className="shell-label">High trust only</span>
              <div style={{ marginTop: "8px" }}>
                <FilterChip label={highTrust ? "High trust: yes" : "High trust"} active={highTrust} onClick={() => setHighTrust(!highTrust)} />
              </div>
            </div>
          </div>
        </div>
        <div className="grid listing-grid">
          {filteredIdentities.map((identity) => <IdentityCard key={identity.id} identity={identity} navigate={navigate} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">AI and compliance</Badge>
          <h2>AI assistance for identity risk and recovery</h2>
        </div>
        <div className="grid integration-grid">
          {AI_FEATURES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Trust and platform</Badge>
          <h2>Identity depends on NovaTrust, NovaPay, and NovaConnect</h2>
        </div>
        <div className="grid integration-grid">
          {TRUST_AND_PLATFORM.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>
    </section>
  );
}
