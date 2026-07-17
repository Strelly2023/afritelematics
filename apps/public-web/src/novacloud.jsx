import React, { useMemo, useState } from "react";

const CLOUD_LIFECYCLE = [
  "Provision",
  "Configure",
  "Deploy",
  "Govern",
  "Observe",
  "Scale",
  "Recover",
  "Optimise",
];

const ROLE_APPS = [
  { title: "Platform Engineering", summary: "Environments, deployment gates, service catalogs, and automation." },
  { title: "SRE Console", summary: "Observability, incidents, incident response, and reliability posture." },
  { title: "Security Ops", summary: "Policy, access, posture, threat signals, and compliance controls." },
  { title: "Data Platform", summary: "Workloads, clusters, pipelines, lineage, and managed analytics." },
  { title: "Product Teams", summary: "App environments, previews, releases, and rollback rehearsals." },
  { title: "Partner Tenants", summary: "Isolated tenant access with region and policy controls." },
];

const CAPABILITIES = [
  { title: "Multi-region environments", summary: "Controlled deployment across Australia, Africa, and regional failover zones." },
  { title: "Deployment gates", summary: "Policy-backed release gates, approvals, checks, and rollback safety." },
  { title: "Observability", summary: "Metrics, logs, traces, dashboards, alerting, and health views." },
  { title: "Regional controls", summary: "Data residency, tenancy isolation, and workload placement." },
  { title: "Resilience", summary: "Backups, disaster recovery, and controlled restoration procedures." },
  { title: "Cost controls", summary: "Resource visibility, budgets, and optimisation signals for cloud spend." },
];

const TRUST_AND_PLATFORM = [
  { title: "NovaCodePro", summary: "Governed delivery, testing, approvals, and operational evidence." },
  { title: "NovaID", summary: "Identity, access control, and tenant-bound sessions." },
  { title: "NovaTrust", summary: "Audit trails, policy governance, and verification evidence." },
  { title: "NovaData", summary: "Analytics, operational metrics, and platform intelligence." },
  { title: "NovaConnect", summary: "Platform APIs, partner access, and integration workflows." },
  { title: "NovaMonitor", summary: "Incident monitoring, alerting, and operational visibility." },
];

const ENVIRONMENT_TYPES = ["Production", "Staging", "Preview", "Development", "Recovery"];

const SAMPLE_ENVIRONMENTS = [
  {
    id: "cloud-prod-au",
    title: "Production AU",
    type: "Production",
    region: "Australia",
    status: "Healthy",
    workloads: "Core customer and business products",
    note: "Deployment gates and trust checks enforced.",
  },
  {
    id: "cloud-staging-af",
    title: "Staging Africa",
    type: "Staging",
    region: "Africa",
    status: "Healthy",
    workloads: "Pre-release validation and partner pilots",
    note: "Used for canary release rehearsal and validation.",
  },
  {
    id: "cloud-preview",
    title: "Partner Preview",
    type: "Preview",
    region: "Australia",
    status: "Controlled",
    workloads: "Private preview products and demos",
    note: "Tenant isolated with explicit approvals.",
  },
  {
    id: "cloud-dev",
    title: "Development",
    type: "Development",
    region: "Global",
    status: "Available",
    workloads: "Developer sandboxes and CI workloads",
    note: "Rapid iteration with policy-aware guardrails.",
  },
  {
    id: "cloud-dr",
    title: "Disaster Recovery",
    type: "Recovery",
    region: "Australia",
    status: "Ready",
    workloads: "Failover, backups, and restore testing",
    note: "Restoration procedures are rehearsed and documented.",
  },
];

const AI_FEATURES = [
  { title: "Capacity planning", summary: "Forecast compute, storage, and workload demand." },
  { title: "Reliability insights", summary: "Detect noisy services, saturation, and incident precursors." },
  { title: "Cost optimisation", summary: "Recommend instance shapes, scaling policies, and budget controls." },
  { title: "Auto remediation", summary: "Propose recovery steps for known cloud failure modes." },
  { title: "Change impact", summary: "Explain how releases affect services, regions, and policy boundaries." },
  { title: "Operational copilots", summary: "Guide SRE and platform teams through incidents and maintenance." },
];

function Badge({ children, tone = "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function matchesEnvironment(environment, filters) {
  const text = `${environment.title} ${environment.type} ${environment.region} ${environment.status} ${environment.workloads} ${environment.note}`.toLowerCase();
  if (filters.query && !text.includes(filters.query.toLowerCase())) return false;
  if (filters.type !== "All" && environment.type !== filters.type) return false;
  if (filters.region !== "All" && environment.region !== filters.region) return false;
  if (filters.healthyOnly && !["Healthy", "Ready", "Available"].includes(environment.status)) return false;
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

function EnvironmentCard({ environment, navigate }) {
  return (
    <article className="product-card delivery-card">
      <div className="card-top">
        <div>
          <Badge tone="trust">{environment.type}</Badge>
          <h3>{environment.title}</h3>
          <p>{environment.region}</p>
        </div>
        <Badge tone={environment.status === "Healthy" || environment.status === "Ready" ? "trust" : "warning"}>{environment.status}</Badge>
      </div>
      <dl>
        <div><dt>Workloads</dt><dd>{environment.workloads}</dd></div>
        <div><dt>Evidence</dt><dd>Linked</dd></div>
      </dl>
      <p>{environment.note}</p>
      <div className="actions housing-actions">
        <button className="button primary" type="button" onClick={() => navigate("/contact")}>Request platform access</button>
        <button className="button secondary" type="button" onClick={() => navigate("/trust")}>View platform trust</button>
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

export function NovaCloudDetail({ navigate }) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState("All");
  const [region, setRegion] = useState("All");
  const [healthyOnly, setHealthyOnly] = useState(false);

  const regions = useMemo(() => ["All", ...new Set(SAMPLE_ENVIRONMENTS.map((environment) => environment.region))], []);
  const filteredEnvironments = useMemo(
    () => SAMPLE_ENVIRONMENTS.filter((environment) => matchesEnvironment(environment, { query, type, region, healthyOnly })),
    [query, type, region, healthyOnly],
  );

  return (
    <section className="detail housing-detail">
      <div className="housing-hero">
        <div className="housing-hero-copy">
          <Badge tone="trust">NovaTech cloud infrastructure platform</Badge>
          <h1>NovaCloud</h1>
          <p>
            Multi-region infrastructure, deployment gates, observability, resilience, and tenant controls for the NovaTech ecosystem.
          </p>
          <div className="actions">
            <button className="button primary" type="button" onClick={() => navigate("/contact")}>Start a cloud project</button>
            <button className="button secondary" type="button" onClick={() => navigate("/developers")}>Open developer portal</button>
          </div>
          <div className="trust-strip">
            <span>Regional workloads</span>
            <span>Deployment governance</span>
            <span>NovaCodePro · NovaID · NovaTrust</span>
            <span>Private access</span>
          </div>
        </div>
        <div className="housing-hero-panel">
          <h2>Cloud scope</h2>
          <div className="metric-grid">
            <article>
              <strong>8</strong>
              <span>cloud lifecycle stages</span>
            </article>
            <article>
              <strong>6</strong>
              <span>platform roles</span>
            </article>
            <article>
              <strong>5</strong>
              <span>environment samples</span>
            </article>
            <article>
              <strong>2</strong>
              <span>primary regions</span>
            </article>
          </div>
          <div className="mini-stack">
            {CLOUD_LIFECYCLE.slice(0, 4).map((item) => (
              <div key={item} className="mini-stack-item">{item}</div>
            ))}
          </div>
        </div>
      </div>

      <section className="band">
        <div className="section-heading">
          <Badge>Lifecycle</Badge>
          <h2>Infrastructure lifecycle from provisioning to optimisation</h2>
          <p>NovaCloud provides the managed substrate used by the rest of the NovaTech product suite.</p>
        </div>
        <div className="grid app-grid">
          {CLOUD_LIFECYCLE.map((step) => <ProductCard key={step} title={step} summary="Managed cloud lifecycle stage." />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="info">Applications</Badge>
          <h2>Cloud experiences for platform and operations teams</h2>
        </div>
        <div className="grid app-grid">
          {ROLE_APPS.map((app) => <ProductCard key={app.title} {...app} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="trust">Capabilities</Badge>
          <h2>Infrastructure capabilities that other products consume</h2>
        </div>
        <div className="grid segment-grid">
          {CAPABILITIES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Environments</Badge>
          <h2>Browse managed cloud environments</h2>
          <p>Filter by environment type, region, and health to inspect the managed platform footprint.</p>
        </div>
        <div className="housing-search">
          <div className="facet-row">
            <label>
              Search
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search environments, workloads, or notes" />
            </label>
            <label>
              Type
              <select value={type} onChange={(event) => setType(event.target.value)}>
                {["All", ...ENVIRONMENT_TYPES].map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <label>
              Region
              <select value={region} onChange={(event) => setRegion(event.target.value)}>
                {regions.map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
            <div>
              <span className="shell-label">Healthy only</span>
              <div style={{ marginTop: "8px" }}>
                <FilterChip label={healthyOnly ? "Healthy only: yes" : "Healthy only"} active={healthyOnly} onClick={() => setHealthyOnly(!healthyOnly)} />
              </div>
            </div>
          </div>
        </div>
        <div className="grid listing-grid">
          {filteredEnvironments.map((environment) => <EnvironmentCard key={environment.id} environment={environment} navigate={navigate} />)}
        </div>
      </section>

      <section className="band">
        <div className="section-heading">
          <Badge tone="info">AI and resilience</Badge>
          <h2>AI support for platform engineering and SRE teams</h2>
        </div>
        <div className="grid integration-grid">
          {AI_FEATURES.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <Badge tone="trust">Platform</Badge>
          <h2>NovaCloud is the managed base for the NovaTech ecosystem</h2>
        </div>
        <div className="grid integration-grid">
          {TRUST_AND_PLATFORM.map((item) => <ProductCard key={item.title} {...item} />)}
        </div>
      </section>
    </section>
  );
}

