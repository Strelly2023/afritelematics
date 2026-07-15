import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { audiences, fallbackProducts, fallbackServices } from "./data.js";
import { loadPublicGateway, searchPublic, submitContact } from "./api.js";
import "./styles.css";

const pages = {
  "/": "Home",
  "/platform": "Platform",
  "/products": "Products",
  "/apps": "Apps",
  "/solutions": "Solutions",
  "/industries": "Industries",
  "/developers": "Developers",
  "/trust": "Trust Center",
  "/resources": "Resources",
  "/about": "About",
  "/leadership": "Leadership",
  "/governance": "Governance",
  "/careers": "Careers",
  "/contact": "Contact",
  "/support": "Support",
  "/legal/privacy": "Privacy",
  "/legal/terms": "Terms",
  "/accessibility": "Accessibility",
  "/search": "Search",
  "/status": "Status",
  "/verify": "Verify",
  "/downloads": "Downloads",
};

function navigate(path) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function usePath() {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);
  return path;
}

function Badge({ children, tone = "neutral" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function uniqueNav(nav) {
  const seen = new Set();
  return nav.filter((item) => {
    if (seen.has(item.href)) {
      return false;
    }
    seen.add(item.href);
    return true;
  });
}

function Header({ site, path }) {
  const [open, setOpen] = useState(false);
  const nav = uniqueNav([...(site.navigation || []), { label: "Apps", href: "/apps" }, { label: "Status", href: "/status" }, { label: "Verify", href: "/verify" }, { label: "Downloads", href: "/downloads" }]);
  return (
    <header className="site-header">
      <div className="bar">
        <button className="brand" onClick={() => navigate("/")} aria-label="AfriTechnology home">
          <span className="brand-mark">AT</span>
          <span>AfriTechnology</span>
        </button>
        <button className="menu-button" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="nav">
          Menu
        </button>
        <nav id="nav" className={open ? "nav nav-open" : "nav"} aria-label="Primary">
          {nav.map((item) => (
            <button key={item.href} className={path === item.href ? "nav-link active" : "nav-link"} onClick={() => navigate(item.href)}>
              {item.label}
            </button>
          ))}
        </nav>
        <a className="signin" href={site.portal_destinations?.app || "https://app.afritechnology.com"} rel="noreferrer">
          Sign in
        </a>
      </div>
    </header>
  );
}

function Hero({ site, status }) {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="hero-copy">
        <Badge tone="trust">Public gateway</Badge>
        <h1 id="hero-title">Technology you can trust. Platforms built for real life.</h1>
        <p>{site.supporting_message}</p>
        <div className="actions">
          <button className="button primary" onClick={() => navigate("/products")}>Explore Products</button>
          <button className="button secondary" onClick={() => navigate("/contact")}>Start a Project</button>
        </div>
        <div className="trust-strip" aria-label="Live trust summary">
          <span>Status: {status.overall}</span>
          <span>Region: Australia and Africa</span>
          <span>No invented uptime</span>
        </div>
      </div>
      <EcosystemVisual />
    </section>
  );
}

function EcosystemVisual() {
  const nodes = ["Identity", "Trust", "Payments", "Mobility", "Commerce", "Data", "Intelligence"];
  return (
    <div className="ecosystem" aria-label="AfriTechnology ecosystem relationship">
      {nodes.map((node, index) => (
        <div className="eco-node" key={node} style={{ "--delay": `${index * 80}ms` }}>
          <span>{node}</span>
        </div>
      ))}
    </div>
  );
}

function ProductCard({ product }) {
  const tone = product.availability === "Available" ? "success" : product.availability === "Coming Soon" ? "warning" : "info";
  return (
    <article className="product-card">
      <div className="card-top">
        <h3>{product.name}</h3>
        <Badge tone={tone}>{product.availability}</Badge>
      </div>
      <p>{product.summary}</p>
      <dl>
        <div><dt>Family</dt><dd>{product.family}</dd></div>
        <div><dt>Regions</dt><dd>{(product.regions || []).join(", ")}</dd></div>
        <div><dt>Lifecycle</dt><dd>{product.lifecycle}</dd></div>
      </dl>
      <button className="text-action" onClick={() => navigate(`/products/${product.slug}`)}>View product</button>
    </article>
  );
}

function ProductGrid({ products }) {
  return (
    <section className="section" aria-labelledby="products-title">
      <div className="section-heading">
        <Badge>Governed catalog</Badge>
        <h2 id="products-title">Product ecosystem</h2>
        <p>Availability and maturity are explicit. Pilot products are not presented as generally available.</p>
      </div>
      <div className="grid products-grid">
        {products.map((product) => <ProductCard key={product.product_id} product={product} />)}
      </div>
    </section>
  );
}

function ServiceCard({ service }) {
  const tone = service.authentication_required ? "warning" : "trust";
  return (
    <article className="product-card">
      <div className="card-top">
        <h3>{service.name}</h3>
        <Badge tone={tone}>{service.status}</Badge>
      </div>
      <p>{service.domain}</p>
      <dl>
        <div><dt>Category</dt><dd>{service.category}</dd></div>
        <div><dt>Indexing</dt><dd>{service.indexing}</dd></div>
        <div><dt>Auth</dt><dd>{service.authentication_required ? "Required" : "Public"}</dd></div>
      </dl>
      <a className="text-action" href={service.url} rel="noreferrer">Open surface</a>
    </article>
  );
}

function PlatformSection() {
  const capabilities = [
    ["NovaID", "One identity across every experience."],
    ["NovaTrust", "Governance, evidence, assurance, and policy."],
    ["NovaAI", "Governed intelligence and agent automation."],
    ["NovaCloud", "Reliable regional infrastructure."],
    ["NovaData", "Trusted operational and analytical data."],
    ["NovaCodePro", "From requirements to governed execution."],
  ];
  return (
    <section className="band" aria-labelledby="platform-title">
      <div className="section-heading">
        <Badge tone="info">Shared foundation</Badge>
        <h2 id="platform-title">A platform beneath every product</h2>
      </div>
      <div className="grid capability-grid">
        {capabilities.map(([name, summary]) => (
          <article className="capability" key={name}>
            <h3>{name}</h3>
            <p>{summary}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function FabricSection({ services }) {
  const grouped = services.reduce((acc, service) => {
    const key = service.category || "Other";
    acc[key] = [...(acc[key] || []), service];
    return acc;
  }, {});
  return (
    <section className="band" aria-labelledby="fabric-title">
      <div className="section-heading">
        <Badge tone="info">Operational fabric</Badge>
        <h2 id="fabric-title">Product, portal, and platform surfaces</h2>
        <p>The public gateway exposes each surface with its actual exposure boundary instead of collapsing everything into one generic destination.</p>
      </div>
      {Object.entries(grouped).map(([category, records]) => (
        <div key={category} className="fabric-group">
          <div className="fabric-group-head">
            <h3>{category}</h3>
            <p>{records.length} surfaces</p>
          </div>
          <div className="grid services-grid">
            {records.map((service) => <ServiceCard key={service.slug} service={service} />)}
          </div>
        </div>
      ))}
    </section>
  );
}

function AudienceTabs() {
  const [selected, setSelected] = useState("Customers");
  const data = audiences[selected];
  return (
    <section className="section" aria-labelledby="audiences-title">
      <div className="section-heading">
        <Badge>Audience paths</Badge>
        <h2 id="audiences-title">Find the right starting point</h2>
      </div>
      <div className="tabs" role="tablist" aria-label="Audience">
        {Object.keys(audiences).map((audience) => (
          <button
            key={audience}
            role="tab"
            aria-selected={selected === audience}
            className={selected === audience ? "tab active" : "tab"}
            onClick={() => setSelected(audience)}
          >
            {audience}
          </button>
        ))}
      </div>
      <div className="audience-panel">
        <div>
          <h3>{selected}</h3>
          <ul>{data.benefits.map((benefit) => <li key={benefit}>{benefit}</li>)}</ul>
        </div>
        <div>
          <h4>Relevant products</h4>
          <p>{data.products.join(", ")}</p>
          <button className="button secondary" onClick={() => data.href.startsWith("/") ? navigate(data.href) : window.location.assign(data.href)}>
            {data.cta}
          </button>
        </div>
      </div>
    </section>
  );
}

function TrustLayer({ trust, status }) {
  return (
    <section className="band" aria-labelledby="trust-title">
      <div className="section-heading">
        <Badge tone="trust">Trust layer</Badge>
        <h2 id="trust-title">Evidence-backed public claims</h2>
        <p>{status.note || "Trust records show scope, owner, and evidence references."}</p>
      </div>
      <div className="grid trust-grid">
        {(trust.records || []).map((record) => (
          <article className="trust-record" key={record.id}>
            <Badge tone={record.status === "ENFORCED" ? "success" : "info"}>{record.status}</Badge>
            <h3>{record.title}</h3>
            <p>{record.scope}</p>
            <small>Owner: {record.owner}</small>
            <small>Evidence: {record.evidence_ref}</small>
          </article>
        ))}
      </div>
    </section>
  );
}

function AppsPage({ services }) {
  return (
    <section className="detail">
      <Badge tone="info">Application surfaces</Badge>
      <h1>Apps and portal gateways</h1>
      <p>Each surface is labeled with its exposure boundary, authentication posture, and indexing policy. Internal applications stay out of the public root.</p>
      <div className="grid services-grid">
        {services.map((service) => <ServiceCard key={service.slug} service={service} />)}
      </div>
      <div className="detail-grid">
        <article>
          <h2>Public experience</h2>
          <p>Corporate pages, product discovery, trust content, and status information are publicly indexable when appropriate.</p>
        </article>
        <article>
          <h2>Private workspaces</h2>
          <p>Customer, operator, and NovaCodePro experiences remain isolated behind authenticated subdomains and noindex rules.</p>
        </article>
      </div>
    </section>
  );
}

function Home({ data }) {
  return (
    <>
      {data.degraded && <div className="notice" role="status">Live content API is degraded. Showing approved fallback content.</div>}
      <Hero site={data.site} status={data.status} />
      <ProductGrid products={data.products} />
      <PlatformSection />
      <FabricSection services={data.services || fallbackServices} />
      <AudienceTabs />
      <TrustLayer trust={data.trust} status={data.status} />
      <Insights />
      <ContactCta />
    </>
  );
}

function ProductDetail({ products, slug }) {
  const product = products.find((item) => item.slug === slug) || fallbackProducts.find((item) => item.slug === slug);
  if (!product) return <GenericPage title="Product not found" description="The requested product is not published in the public catalog." />;
  return (
    <section className="detail">
      <Badge>{product.availability}</Badge>
      <h1>{product.name}</h1>
      <p>{product.summary}</p>
      <div className="detail-grid">
        <article><h2>Features</h2><ul>{(product.features || []).map((item) => <li key={item}>{item}</li>)}</ul></article>
        <article><h2>Audiences</h2><p>{(product.audiences || []).join(", ")}</p></article>
        <article><h2>Regions</h2><p>{(product.regions || []).join(", ")}</p></article>
        <article><h2>Lifecycle</h2><p>{product.lifecycle}</p></article>
      </div>
      <a className="button primary" href={product.portal_url}>Open product destination</a>
    </section>
  );
}

function GenericPage({ title, description, children }) {
  return (
    <section className="detail">
      <Badge>AfriTechnology</Badge>
      <h1>{title}</h1>
      <p>{description}</p>
      {children}
    </section>
  );
}

function SearchPage() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState({ status: "idle", results: [] });
  async function runSearch(event) {
    event.preventDefault();
    setState({ status: "loading", results: [] });
    try {
      const result = await searchPublic(query);
      setState({ status: "success", results: result.results || [] });
    } catch (error) {
      const q = query.toLowerCase();
      const productResults = fallbackProducts
        .filter((product) => `${product.name} ${product.summary} ${product.family}`.toLowerCase().includes(q))
        .map((product) => ({ title: product.name, summary: product.summary, href: `/products/${product.slug}`, availability: product.availability }));
      const serviceResults = fallbackServices
        .filter((service) => `${service.name} ${service.category} ${service.domain}`.toLowerCase().includes(q))
        .map((service) => ({ title: service.name, summary: `${service.domain} · ${service.indexing}`, href: service.url, availability: service.status }));
      setState({
        status: "degraded",
        results: [...productResults, ...serviceResults],
      });
    }
  }
  return (
    <section className="detail">
      <h1>Search AfriTechnology</h1>
      <form className="search-form" onSubmit={runSearch}>
        <label htmlFor="search">Search products, solutions, documentation, support, and downloads</label>
        <div className="field-row">
          <input id="search" value={query} onChange={(event) => setQuery(event.target.value)} required />
          <button className="button primary" type="submit">Search</button>
        </div>
      </form>
      <div className="results" aria-live="polite">
        {state.status === "loading" && <p>Searching...</p>}
        {state.results.map((result) => (
          <article key={`${result.href}-${result.title}`} className="result">
            <h2>{result.title}</h2>
            <p>{result.summary}</p>
            <button className="text-action" onClick={() => navigate(result.href)}>Open result</button>
          </article>
        ))}
      </div>
    </section>
  );
}

function ContactPage() {
  const [form, setForm] = useState({
    request_type: "START_PROJECT",
    name: "",
    email: "",
    organization: "",
    country: "AU",
    product_interests: ["NOVACODEPRO"],
    message: "",
    preferred_contact_method: "EMAIL",
    consent: { privacy_policy_version: "2026.1", marketing: false },
  });
  const [state, setState] = useState({ status: "idle" });
  const intentHelp = {
    START_PROJECT: "Tell us what you want to build and which platforms matter.",
    REQUEST_DEMO: "We will route the request to the relevant product owner.",
    CUSTOMER_SUPPORT: "Support requests are routed separately from sales.",
    SECURITY_DISCLOSURE: "Security issues are handled by the responsible disclosure workflow.",
  };
  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }
  async function submit(event) {
    event.preventDefault();
    setState({ status: "submitting" });
    try {
      const result = await submitContact(form);
      setState({ status: "submitted", result });
    } catch (error) {
      setState({ status: "recoverable", error: String(error.message || error) });
    }
  }
  return (
    <section className="detail">
      <h1>Contact AfriTechnology</h1>
      <p>A guided workflow routes enquiries to the right owner and returns a trackable reference.</p>
      <form className="contact-form" onSubmit={submit}>
        <label>Intent
          <select value={form.request_type} onChange={(event) => update("request_type", event.target.value)}>
            <option value="START_PROJECT">Start a project</option>
            <option value="REQUEST_DEMO">Request a product demo</option>
            <option value="BECOME_PARTNER">Become a partner</option>
            <option value="API_INTEGRATION">Integrate an API</option>
            <option value="CUSTOMER_SUPPORT">Get customer support</option>
            <option value="CAREERS">Apply for a job</option>
            <option value="COMPLIANCE">Speak with compliance</option>
            <option value="SECURITY_DISCLOSURE">Report a security issue</option>
            <option value="MEDIA">Media enquiry</option>
            <option value="GENERAL">General enquiry</option>
          </select>
        </label>
        <p className="form-hint">{intentHelp[form.request_type] || "We will triage your request."}</p>
        <div className="form-grid">
          <label>Name<input value={form.name} onChange={(event) => update("name", event.target.value)} required minLength="2" /></label>
          <label>Work email<input type="email" value={form.email} onChange={(event) => update("email", event.target.value)} required /></label>
          <label>Organization<input value={form.organization} onChange={(event) => update("organization", event.target.value)} /></label>
          <label>Country<input value={form.country} onChange={(event) => update("country", event.target.value)} required /></label>
        </div>
        <label>Product or service
          <select value={form.product_interests[0] || "NOVACODEPRO"} onChange={(event) => update("product_interests", [event.target.value])}>
            <option value="NOVACODEPRO">NovaCodePro</option>
            <option value="NOVAPAY">NovaPay</option>
            <option value="NOVARIDE">NovaRide</option>
            <option value="NOVAID">NovaID</option>
            <option value="NOVATRUST">NovaTrust</option>
          </select>
        </label>
        <label>Description<textarea value={form.message} onChange={(event) => update("message", event.target.value)} required minLength="20" /></label>
        <label className="checkbox"><input type="checkbox" required /> I agree to the privacy policy for this request.</label>
        <button className="button primary" type="submit" disabled={state.status === "submitting"}>{state.status === "submitting" ? "Submitting..." : "Submit request"}</button>
        <div aria-live="polite">
          {state.status === "submitted" && <p className="success">Received. Reference: {state.result.reference}. Expected response: {state.result.expected_response}.</p>}
          {state.status === "recoverable" && <p className="error">Submission failed. Your input has been preserved. Try again or email support.</p>}
        </div>
      </form>
    </section>
  );
}

function Insights() {
  return (
    <section className="section" aria-labelledby="insights-title">
      <div className="section-heading">
        <Badge>Resources</Badge>
        <h2 id="insights-title">Latest insights and announcements</h2>
      </div>
      <div className="grid">
        {["Operational verification is not approval", "Separating GA from real-payment activation", "Public routing isolation for trusted domains"].map((title) => (
          <article className="article-card" key={title}>
            <h3>{title}</h3>
            <p>Published only after review and linked to evidence in the Trust Center.</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function ContactCta() {
  return (
    <section className="cta">
      <h2>Start with a governed conversation</h2>
      <p>Tell us the audience, region, product, and urgency. The workflow returns a reference and routes ownership.</p>
      <button className="button primary" onClick={() => navigate("/contact")}>Contact AfriTechnology</button>
    </section>
  );
}

function VerifyPage() {
  return (
    <GenericPage title="Verify" description="Verification checks route receipts, release evidence, and public claims through governed evidence records.">
      <div className="detail-grid">
        <article>
          <h2>Receipt verification</h2>
          <p>Check signed receipts and tracked references against the evidence store.</p>
        </article>
        <article>
          <h2>Release verification</h2>
          <p>Confirm a release identifier, approved version, and associated readiness evidence.</p>
        </article>
      </div>
    </GenericPage>
  );
}

function DownloadsPage() {
  return (
    <GenericPage title="Downloads" description="Signed artifacts, release bundles, and evidence exports are published through governed download paths.">
      <div className="detail-grid">
        <article>
          <h2>Public mobile builds</h2>
          <p>Approved release artifacts are exposed only when verified for public distribution.</p>
        </article>
        <article>
          <h2>Evidence exports</h2>
          <p>Verification packages and signed evidence exports are published with explicit hashes.</p>
        </article>
      </div>
    </GenericPage>
  );
}

function StatusPage({ status }) {
  return (
    <GenericPage title="Public Status" description={status.note || "Measured status appears here after live operational verification."}>
      <div className="grid">
        {(status.components || []).map((component) => (
          <article className="capability" key={component.name}>
            <h2>{component.name}</h2>
            <p>{component.state}</p>
          </article>
        ))}
      </div>
    </GenericPage>
  );
}

function App() {
  const path = usePath();
  const [data, setData] = useState(null);
  useEffect(() => {
    loadPublicGateway().then(setData);
  }, []);
  useEffect(() => {
    const title = pages[path] ? `${pages[path]} | AfriTechnology` : path.startsWith("/products/") ? "Product | AfriTechnology" : "AfriTechnology | Trusted Digital Platforms";
    document.title = path === "/" ? "AfriTechnology | Trusted Digital Platforms" : title;
  }, [path]);
  const route = useMemo(() => path.replace(/\/$/, "") || "/", [path]);
  if (!data) return <main id="main" className="loading" aria-live="polite">Loading AfriTechnology...</main>;
  const page = route.startsWith("/products/") ? (
    <ProductDetail products={data.products} slug={route.split("/").pop()} />
  ) : route === "/" ? (
    <Home data={data} />
  ) : route === "/products" ? (
    <ProductGrid products={data.products} />
  ) : route === "/apps" ? (
    <AppsPage services={data.services || fallbackServices} />
  ) : route === "/platform" ? (
    <><PlatformSection /><AudienceTabs /></>
  ) : route === "/trust" ? (
    <TrustLayer trust={data.trust} status={data.status} />
  ) : route === "/verify" ? (
    <VerifyPage />
  ) : route === "/downloads" ? (
    <DownloadsPage />
  ) : route === "/contact" ? (
    <ContactPage />
  ) : route === "/search" ? (
    <SearchPage />
  ) : route === "/status" ? (
    <StatusPage status={data.status} />
  ) : route === "/developers" ? (
    <GenericPage title="Developer Platform" description="API catalog, sandbox, SDKs, webhooks, usage, changelog, and support are kept separate from internal portals." />
  ) : route === "/solutions" ? (
    <GenericPage title="Solutions" description="Audience-specific paths for customers, businesses, enterprises, developers, partners, and governments." />
  ) : route === "/industries" ? (
    <GenericPage title="Industries" description="Payments, mobility, identity, commerce, healthcare, logistics, government, and enterprise operations." />
  ) : route === "/support" ? (
    <GenericPage title="Support" description="Support requests are routed through the contact workflow and assigned an auditable reference." />
  ) : route === "/accessibility" ? (
    <GenericPage title="Accessibility" description="AfriTechnology targets WCAG 2.2 AA with automated checks and human review for major releases." />
  ) : route === "/legal/privacy" ? (
    <GenericPage title="Privacy" description="Privacy-conscious analytics, consent-aware routing, and data minimization are required for public workflows." />
  ) : route === "/legal/terms" ? (
    <GenericPage title="Terms" description="Public terms and product-specific terms are governed content records." />
  ) : (
    <GenericPage title={pages[route] || "AfriTechnology"} description="This page is part of the public AfriTechnology gateway and does not serve internal dashboards." />
  );
  return (
    <>
      <Header site={data.site} path={route} />
      <main id="main">{page}</main>
      <footer className="footer">
        <span>AfriTechnology</span>
        <button onClick={() => navigate("/trust")}>Trust Center</button>
        <button onClick={() => navigate("/legal/privacy")}>Privacy</button>
        <button onClick={() => navigate("/accessibility")}>Accessibility</button>
      </footer>
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
