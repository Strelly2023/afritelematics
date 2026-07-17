import React, { useMemo, useState } from "react";

const TRUST_LIFECYCLE = [
  "Discover",
  "Verify",
  "Attest",
  "Policy bind",
  "Monitor",
  "Evidence capture",
  "Audit",
  "Dispute handling",
  "Review",
];

const ROLE_APPS = [
  { title: "Compliance App", summary: "Policy management, evidence review, approvals, and audit readiness." },
  { title: "Security App", summary: "Threat signals, fraud checks, trust scoring, and incident review." },
  { title: "Executive App", summary: "Readiness scorecards, risk posture, and governance metrics." },
  { title: "Partner Portal", summary: "Verification, certification, onboarding, and evidence exchange." },
  { title: "Operations Console", summary: "Release controls, runtime evidence, and cross-product trust monitoring." },
  { title: "Developer Portal", summary: "APIs, webhooks, attestations, and integration policies." },
];

const CAPABILITIES = [
  { title: "Evidence verification", summary: "Validate receipts, releases, attestations, and other governed claims." },
  { title: "Trust scores", summary: "Score merchants, drivers, products, partners, and events based on policy and evidence." },
  { title: "Policy controls", summary: "Encode governance rules, approval thresholds, and operational boundaries." },
  { title: "Audit history", summary: "Maintain immutable audit trails for critical actions and trust decisions." },
  { title: "Fraud detection", summary: "Use signals, anomalies, and cross-product evidence to flag suspicious activity." },
  { title: "Dispute support", summary: "Surface the evidence bundle required to resolve claims or escalations." },
];

const TRUST_PRODUCTS = [
  { title: "NovaID", summary: "Verified identities, passkeys, MFA, partner access, and device trust." },
  { title: "NovaPay", summary: "Money movement, settlements, refunds, and financial risk controls." },
  { title: "NovaDashDoor", summary: "Verified merchants, courier trust, and delivery evidence." },
  { title: "NovaLogistics X", summary: "Chain of custody, shipment integrity, and carrier verification." },
  { title: "NovaHouseReach", summary: "Property ownership, inspections, and document-backed trust records." },
  { title: "NovaCodePro", summary: "Release governance, manifest verification, and engineering evidence." },
];

const EVIDENCE_TYPES = [
  "Receipt",
  "Release certificate",
  "Verification report",
  "Audit trail",
  "Policy approval",
  "Chain of custody",
  "Identity attestation",
  "Fraud signal",
];

const SAMPLE_RECORDS = [
  {
    id: "trust-1",
    title: "Release certificate for NovaPay",
    subject: "NovaPay 2026.1.3",
    type: "Release certificate",
    status: "Verified",
    owner: "Platform Operations",
    score: 98,
    note: "Signed artifact checksum matches the approved release manifest.",
  },
  {
    id: "trust-2",
    title: "Verified merchant status",
    subject: "Green Table Kitchen",
    type: "Identity attestation",
    status: "Verified",
    owner: "Risk and Compliance",
    score: 94,
    note: "Business verification complete with delegated admin and policy binding.",
  },
  {
    id: "trust-3",
    title: "Delivery evidence bundle",
    subject: "NovaDashDoor courier route",
    type: "Chain of custody",
    status: "Verified",
    owner: "Operations",
    score: 91,
    note: "Pickup photo, geolocation, and proof of delivery attached.",
  },
  {
    id: "trust-4",
    title: "Identity risk alert",
    subject: "Partner login anomaly",
    type: "Fraud signal",
    status: "Review required",
    owner: "Security",
    score: 61,
    note: "Device posture and location change triggered step-up verification.",
  },
  {
    id: "trust-5",
    title: "Property ownership verification",
    subject: "NovaHouseReach listing",
    type: "Verification report",
    status: "Verified",
    owner: "Property Compliance",
    score: 96,
    note: "Title, inspection, and document evidence aligned with the listing record.",
  },
];

const AI_FEATURES = [
  { title: "Trust assistant", summary: "Summarise evidence, explain verification gaps, and guide next actions." },
  { title: "Risk scoring", summary: "Blend policy, behaviour, and evidence into a trust score." },
  { title: "Anomaly detection", summary: "Spot unusual patterns across products, identities, and transactions." },
  { title: "Approval routing", summary: "Route high-risk cases to the correct reviewer based on policy." },
  { title: "Evidence synthesis", summary: "Bundle related records into a clear review or dispute packet." },
  { title: "Compliance insights", summary: "Surface outstanding obligations, recertifications, and controls." },
];

function Badge({ children, tone = "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function matchesRecord(record, filters) {
  const text = `${record.title} ${record.subject} ${record.type} ${record.status} ${record.owner} ${record.note}`.toLowerCase();
  if (filters.query && !text.includes(filters.query.toLowerCase())) return false;
  if (filters.type !== "All" && record.type !== filters.type) return false;
  if (filters.status !== "All" && record.status !== filters.status) return false;
  if (filters.highScore && record.score < 90) return false;
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

function TrustRecordCard({ record, navigate }) {
  return (
    <article className="product-card delivery-card">
      <div className="card-top">
        <div>
          <Badge tone="trust">{record.type}</Badge>
          <h3>{record.title}</h3>
          <p>{record.subject}</p>
        </div>
        <Badge tone={record.status === "Verified" ? "trust" : "warning"}>{record.status}</Badge>
      </div>
      <dl>
        <div><dt>Owner</dt><dd>{record.owner}</dd></div>
        <div><dt>Score</dt><dd>{record.score}</dd></div>
      </dl>
      <p>{record.note}</p>
      <div className="actions housing-actions">
        <button className="button primary" type="button" onClick={() => navigate("/contact")}>Request review</button>
        <button className="button secondary" type="button" onClick={() => navigate("/downloads")}>Open evidence center</button>
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

export function NovaTrustDetail({ navigate }) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState("All");
  const [status, setStatus] = useState("All");
  const [highScore, setHighScore] = useState(false);

  const filteredRecords = useMemo(
    () => SAMPLE_RECORDS.filter((record) => matchesRecord(record, { query, type, status, highScore })),
    [query, type, status, highScore],
  );

  return (
    <section className="detail housing-detail">
      <div className="housing-hero">
        <div className="housing-hero-copy">
          <Badge tone="trust">NovaTech trust and assurance platform</Badge>
          <h1>NovaTrust</h1>
          <p>
            Evidence, assurance, policy, verification, and audit controls across the NovaTech ecosystem.
          </p>
          <div className="actions">
            <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start a trust project</button>
            <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open trust APIs</button>
          </div>
          <div className="trust-strip">
            <span>Evidence-backed claims</span>
            <span>Audit trails and policy controls</span>
            <span>NovaID · NovaPay · NovaDashDoor</span>
            <span>Available</span>
          </div>
        </div>
        <div className="housing-hero-panel">
          <h2>Trust scope</h2>
          <div className="metric-grid">
            <article>
              <strong>9</strong>
              <span>trust lifecycle stages</span>
            </article>
            <article>
              <strong>6</strong>
              <span>role-specific apps</span>
            </article>
            <article>
              <strong>8</strong>
              <span>evidence types</span>
            </article>
            <article>
              <strong>1</strong>
              <span>assurance fabric</span>
            </article>
          </div>
          <div className="mini-stack">
            {TRUST_LIFECYCLE.slice(0, 4).map((item) => (
              <div key={item} className="mini-stack-item">{item}</div>
            ))}
          </div>
        </div>
      </div>

      <section className="band">
        <div className="section-heading">
          <Badge>Lifecycle</Badge>
          <h2>Trust lifecycle from evidence discovery to dispute resolution</h2>
          <p>NovaTrust keeps claims, approvals, policies, and audit evidence together so the platform can prove what it says.</p>
        </div>
        <div className="grid app-grid">
          {TRUST_LIFECYCLE.map((step) => <ProductCard key={step} title={step} summary="Managed trust lifecycle stage." />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="info">Applications</Badge>
          <h2>Trust applications for compliance, security, and operations</h2>
        </div>
        <div className="grid app-grid">
          {ROLE_APPS.map((app) => <ProductCard key={app.title} {...app} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="trust">Capabilities</Badge>
          <h2>Assurance controls that apply across the product suite</h2>
        </div>
        <div className="grid segment-grid">
          {CAPABILITIES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Evidence</Badge>
          <h2>Search a governed evidence inventory</h2>
          <p>Teams can filter records by evidence type, status, and score before reviewing or escalating a claim.</p>
        </div>
        <div className="housing-search">
          <div className="facet-row">
            <label>
              Search
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search evidence, subjects, or owners" />
            </label>
            <label>
              Evidence type
              <select value={type} onChange={(event) => setType(event.target.value)}>
                {["All", ...EVIDENCE_TYPES].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                {["All", "Verified", "Review required"].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <div>
              <span className="shell-label">High score only</span>
              <div style={{ marginTop: "8px" }}>
                <FilterChip label={highScore ? "High score: yes" : "High score"} active={highScore} onClick={() => setHighScore(!highScore)} />
              </div>
            </div>
          </div>
        </div>
        <div className="grid listing-grid">
          {filteredRecords.map((record) => <TrustRecordCard key={record.id} record={record} navigate={navigate} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">AI and review</Badge>
          <h2>AI support for assurance, review, and escalation</h2>
        </div>
        <div className="grid integration-grid">
          {AI_FEATURES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Platform coverage</Badge>
          <h2>Trust spans the full NovaTech ecosystem</h2>
        </div>
        <div className="grid integration-grid">
          {TRUST_PRODUCTS.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>
    </section>
  );
}

