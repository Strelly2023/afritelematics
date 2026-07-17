import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { audiences, fallbackProducts, fallbackServices, fallbackSite } from "./data.js";
import { loadPublicGateway, searchPublic, submitContact } from "./api.js";
import "./styles.css";
import { NovaHouseReachDetail } from "./novahousereach.jsx";
import { NovaDashDoorDetail } from "./novadashdoor.jsx";
import { NovaLogisticsDetail } from "./novalogistics.jsx";
import { NovaPayDetail } from "./novapay.jsx";
import { NovaIDDetail } from "./novaid.jsx";
import { NovaTrustDetail } from "./novatrust.jsx";
import { NovaCommerceDetail } from "./novacommerce.jsx";
import { NovaCloudDetail } from "./novacloud.jsx";
import { NovaConnectDetail } from "./novaconnect.jsx";

const pages = {
  "/": "Home",
  "/platform": "Platform",
  "/products": "Products",
  "/products/novahousereach": "NovaHouseReach",
  "/products/novadashdoor": "NovaDashDoor",
  "/products/novalogistics": "NovaLogistics X",
  "/products/novapay": "NovaPay",
  "/products/novaid": "NovaID",
  "/products/novatrust": "NovaTrust",
  "/products/novacommerce": "NovaCommerce",
  "/products/novacloud": "NovaCloud",
  "/products/novaconnect": "NovaConnect",
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
  "/dashboard": "Dashboard",
  "/knowledge": "Knowledge",
  "/partners": "Partners",
  "/architecture": "Architecture",
  "/legal/privacy": "Privacy",
  "/legal/terms": "Terms",
  "/accessibility": "Accessibility",
  "/search": "Search",
  "/status": "Status",
  "/verify": "Verify",
  "/downloads": "Downloads",
  "/docs": "Developer Portal",
};

const PRODUCT_LANDING_ROUTES = [
  "/products/novacodepro",
  "/products/novaride",
  "/products/novapay",
  "/products/novaid",
  "/products/novatrust",
  "/products/novacommerce",
  "/products/novacloud",
  "/products/novagateway",
  "/products/novadata",
  "/products/novaconnect",
  "/products/novagov",
];

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

function useStoredState(key, fallback) {
  const [value, setValue] = useState(() => {
    if (typeof window === "undefined") {
      return fallback;
    }
    return window.localStorage.getItem(key) || fallback;
  });
  useEffect(() => {
    window.localStorage.setItem(key, value);
  }, [key, value]);
  return [value, setValue];
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

const LOCALES = {
  en: {
    navExplore: "Explore",
    navProducts: "Products",
    navApps: "Apps",
    navSolutions: "Solutions",
    navIndustries: "Industries",
    navDevelopers: "Developers",
    navPartners: "Partners",
    navSupport: "Support",
    navTrust: "Trust",
    navCompany: "Company",
    search: "Search",
    aiAssistant: "NovaAI",
    workspace: "Workspace",
    signIn: "Sign in",
    guest: "Guest",
    dashboard: "Dashboard",
    quickActions: "Quick actions",
  },
  fr: {
    navExplore: "Explorer",
    navProducts: "Produits",
    navApps: "Applications",
    navSolutions: "Solutions",
    navIndustries: "Secteurs",
    navDevelopers: "Développeurs",
    navPartners: "Partenaires",
    navSupport: "Assistance",
    navTrust: "Confiance",
    navCompany: "Entreprise",
    search: "Rechercher",
    aiAssistant: "NovaAI",
    workspace: "Espace",
    signIn: "Connexion",
    guest: "Invité",
    dashboard: "Tableau",
    quickActions: "Actions rapides",
  },
  sw: {
    navExplore: "Gundua",
    navProducts: "Bidhaa",
    navApps: "Programu",
    navSolutions: "Suluhisho",
    navIndustries: "Viwanda",
    navDevelopers: "Wasanidi",
    navPartners: "Washirika",
    navSupport: "Msaada",
    navTrust: "Uaminifu",
    navCompany: "Kampuni",
    search: "Tafuta",
    aiAssistant: "NovaAI",
    workspace: "Eneo",
    signIn: "Ingia",
    guest: "Mgeni",
    dashboard: "Dashibodi",
    quickActions: "Vitendo vya haraka",
  },
};

function localeCopy(language) {
  return LOCALES[language] || LOCALES.en;
}

const LABEL_TRANSLATIONS = {
  fr: {
    Explore: "Explorer",
    Products: "Produits",
    Apps: "Applications",
    Solutions: "Solutions",
    Industries: "Secteurs",
    Developers: "Développeurs",
    Partners: "Partenaires",
    Support: "Assistance",
    Trust: "Confiance",
    Company: "Entreprise",
    "Start a project": "Démarrer un projet",
    "Open dashboard": "Ouvrir le tableau",
    "Search knowledge": "Rechercher le savoir",
    "Verify evidence": "Vérifier la preuve",
    "View downloads": "Voir les téléchargements",
    "Command Palette": "Palette de commandes",
    Notifications: "Notifications",
    Workspace: "Espace",
    "AI assistant": "Assistant IA",
    "NovaAI": "NovaAI",
  },
  sw: {
    Explore: "Gundua",
    Products: "Bidhaa",
    Apps: "Programu",
    Solutions: "Suluhisho",
    Industries: "Viwanda",
    Developers: "Wasanidi",
    Partners: "Washirika",
    Support: "Msaada",
    Trust: "Uaminifu",
    Company: "Kampuni",
    "Start a project": "Anza mradi",
    "Open dashboard": "Fungua dashibodi",
    "Search knowledge": "Tafuta maarifa",
    "Verify evidence": "Thibitisha ushahidi",
    "View downloads": "Tazama vipakuliwa",
    "Command Palette": "Menyu ya amri",
    Notifications: "Arifa",
    Workspace: "Eneo",
    "AI assistant": "Msaidizi wa AI",
    "NovaAI": "NovaAI",
  },
};

function translateLabel(label, language) {
  return LABEL_TRANSLATIONS[language]?.[label] || label;
}

function buildSearchIndex(site, products, services, downloads, verifications) {
  const navEntries = uniqueNav([...(site.navigation || []), ...(site.shell?.navigation || [])]).map((item) => ({
    type: "navigation",
    title: item.label,
    summary: `Open ${item.label}`,
    href: item.href,
    availability: "Public",
  }));
  const quickActions = (site.shell?.quick_actions || []).map((item) => ({
    type: "action",
    title: item.label,
    summary: "Quick action",
    href: item.href,
    availability: "Public",
  }));
  const docs = [
    { type: "doc", title: "Public Gateway", summary: "Canonical public website and application gateway.", href: "/trust", availability: "Public" },
    { type: "doc", title: "Developer Docs", summary: "API explorer, sandbox, SDKs, examples, status.", href: "/developers", availability: "Public" },
    { type: "doc", title: "Knowledge Portal", summary: "Runbooks, playbooks, FAQs, architecture, and guides.", href: "/knowledge", availability: "Public" },
    { type: "doc", title: "Release Verification", summary: "Receipt and release evidence verification.", href: "/verify", availability: "Public" },
  ];
  const launcherEntries = (site.launcher || []).map((item) => ({
    type: "app",
    title: item.name,
    summary: `${item.audience} · ${item.availability} · ${item.release_channel}`,
    href: item.url,
    availability: item.availability,
  }));
  const productResults = products.map((product) => ({
    type: "product",
    title: product.name,
    summary: product.summary,
    href: `/products/${product.slug}`,
    availability: product.availability,
  }));
  const serviceResults = services.map((service) => ({
    type: "app",
    title: service.name,
    summary: `${service.domain} · ${service.status} · ${service.indexing}`,
    href: service.url,
    availability: service.status,
  }));
  const downloadResults = (downloads || []).map((item) => ({
    type: "download",
    title: item.name,
    summary: `${item.category} · ${item.version} · ${item.supported_platforms?.[0] || "Public verification"}`,
    href: item.href,
    availability: item.version,
  }));
  const verificationResults = (verifications || []).map((item) => ({
    type: "verification",
    title: item.name,
    summary: `${item.category} · ${item.evidence}`,
    href: item.lookup,
    availability: "Public",
  }));
  return [...navEntries, ...quickActions, ...docs, ...launcherEntries, ...productResults, ...serviceResults, ...downloadResults, ...verificationResults];
}

function assistantReply(prompt, workspace) {
  const text = prompt.trim().toLowerCase();
  if (!text) {
    return "Ask NovaAI about products, APIs, trust, or your workspace.";
  }
  if (text.includes("payment")) {
    return "NovaPay, NovaCodePro, and NovaTrust are the best match for governed payment and release workflows.";
  }
  if (text.includes("ride") || text.includes("mobility")) {
    return "NovaRide, dispatch, fleet, support, and evidence surfaces are the strongest mobility path.";
  }
  if (text.includes("api") || text.includes("sdk")) {
    return "Open the Developer Portal for API Explorer, SDKs, sandbox, authentication, and rate limits.";
  }
  if (text.includes("trust") || text.includes("verify")) {
    return "Use the Trust Center, Verify page, and Downloads page for evidence-backed claims.";
  }
  if (workspace !== "guest") {
    return "Your workspace dashboard will surface projects, approvals, tasks, evidence, and recommendations.";
  }
  return "I can route you to products, apps, trust, support, knowledge, or a project start workflow.";
}

function toneForAvailability(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("available") || normalized.includes("healthy") || normalized.includes("enforced")) return "trust";
  if (normalized.includes("pilot") || normalized.includes("planned") || normalized.includes("coming")) return "warning";
  return "info";
}

function joinText(items, separator = ", ") {
  return (items || []).filter(Boolean).join(separator);
}

function openHref(href) {
  if (!href) return;
  if (href.startsWith("/")) {
    navigate(href);
    return;
  }
  window.location.assign(href);
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

function NovaShellChrome({
  site,
  path,
  language,
  setLanguage,
  workspace,
  setWorkspace,
  signedIn,
  setSignedIn,
  theme,
  setTheme,
  commandOpen,
  setCommandOpen,
  assistantOpen,
  setAssistantOpen,
  notificationsOpen,
  setNotificationsOpen,
  searchTerm,
  setSearchTerm,
  searchIndex,
}) {
  const copy = localeCopy(language);
  const quickActions = (site.shell?.quick_actions || []).map((item) => ({ ...item, label: translateLabel(item.label, language) }));
  const nav = uniqueNav(site.shell?.navigation || site.navigation || []).map((item) => ({ ...item, label: translateLabel(item.label, language) }));
  const workspaceOptions = site.shell?.workspace_options || [];
  const languageOptions = site.shell?.language_options || [];
  const suggestions = (site.shell?.assistant_prompts || []).slice(0, 4);
  const commandResults = searchIndex.filter((item) => {
    const haystack = `${item.title} ${item.summary} ${item.availability} ${item.href}`.toLowerCase();
    return searchTerm.trim() ? haystack.includes(searchTerm.trim().toLowerCase()) : true;
  }).slice(0, 8);
  const notifications = [
    { title: "NovaTrust evidence updated", summary: "New signed release evidence is available.", tone: "trust" },
    { title: "Workspace ready", summary: `${workspace === "guest" ? "Guest" : workspaceOptions.find((item) => item.key === workspace)?.label || workspace} shell loaded.`, tone: "info" },
    { title: "Contact SLA running", summary: "New enquiries are routed with references and owners.", tone: "warning" },
  ];
  return (
    <section className="shell" aria-label="NovaShell">
      <header className="shell-header">
        <div className="shell-topline">
          <button className="brand" onClick={() => navigate("/")} aria-label="AfriTechnology home">
            <span className="brand-mark">AT</span>
            <span>AfriTechnology</span>
          </button>
          <div className="shell-search">
            <label className="sr-only" htmlFor="global-search">{copy.search}</label>
            <input id="global-search" value={searchTerm} onChange={(event) => { setSearchTerm(event.target.value); setCommandOpen(true); }} placeholder={`${copy.search} products, apps, docs, APIs, support...`} onFocus={() => setCommandOpen(true)} />
            <button className="button secondary compact" onClick={() => setCommandOpen(!commandOpen)} type="button">⌘K</button>
          </div>
          <div className="shell-actions">
            <button className="button secondary compact" type="button" onClick={() => setAssistantOpen(!assistantOpen)}>{translateLabel(copy.aiAssistant, language)}</button>
            <button className="button secondary compact" type="button" onClick={() => setNotificationsOpen(!notificationsOpen)} aria-label="Notifications">●</button>
            <select className="compact-select" value={workspace} onChange={(event) => setWorkspace(event.target.value)}>
              {workspaceOptions.map((option) => (
                <option key={option.key} value={option.key}>{option.label}</option>
              ))}
            </select>
            <select className="compact-select" value={language} onChange={(event) => setLanguage(event.target.value)}>
              {languageOptions.map((option) => (
                <option key={option.code} value={option.code}>{option.label}</option>
              ))}
            </select>
            <button className="button secondary compact" type="button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>{theme === "dark" ? "Light" : "Dark"}</button>
            <button className="button primary compact" type="button" onClick={() => setSignedIn(!signedIn)}>{signedIn ? "Signed in" : copy.signIn}</button>
          </div>
        </div>
        <nav className="shell-nav" aria-label="Primary shell">
          {nav.map((item) => (
            <button key={item.href} className={path === item.href ? "nav-link active" : "nav-link"} onClick={() => navigate(item.href)}>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="shell-quick-actions">
          <span className="shell-label">{translateLabel(copy.quickActions, language)}</span>
          {quickActions.map((action) => (
            <button key={action.href} className="quick-action" type="button" onClick={() => navigate(action.href)}>
              {action.label}
            </button>
          ))}
        </div>
      </header>

      {commandOpen && (
        <section className="shell-panel shell-command" aria-label="Command palette">
          <div className="panel-head">
              <h2>{translateLabel("Command Palette", language)}</h2>
            <button className="text-action" onClick={() => setCommandOpen(false)}>Close</button>
          </div>
          <p>Search products, apps, documentation, APIs, trust records, and public actions.</p>
          <input className="command-input" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Type to search..." />
          <div className="results command-results">
            {commandResults.map((item) => (
              <article className="result" key={`${item.type}:${item.href}:${item.title}`}>
                <Badge tone={item.type === "product" ? "trust" : item.type === "app" ? "warning" : "info"}>{item.type}</Badge>
                <h3>{item.title}</h3>
                <p>{item.summary}</p>
                <button className="text-action" onClick={() => openHref(item.href)} type="button">Open result</button>
              </article>
            ))}
          </div>
        </section>
      )}

      <div className="shell-grid">
        {assistantOpen && (
          <section className="shell-panel shell-assistant" aria-label="NovaAI assistant">
            <div className="panel-head">
            <h2>{translateLabel("NovaAI", language)}</h2>
              <button className="text-action" onClick={() => setAssistantOpen(false)}>Close</button>
            </div>
            <p>Conversational product discovery, architecture guidance, and trusted support routing.</p>
            <div className="assistant-chips">
              {suggestions.map((prompt) => (
                <button key={prompt} className="chip" type="button" onClick={() => setSearchTerm(prompt)}>{prompt}</button>
              ))}
            </div>
            <p className="assistant-answer">{assistantReply(searchTerm, workspace)}</p>
          </section>
        )}
        {notificationsOpen && (
          <section className="shell-panel shell-notifications" aria-label="Notifications">
            <div className="panel-head">
              <h2>Notifications</h2>
              <button className="text-action" onClick={() => setNotificationsOpen(false)}>Close</button>
            </div>
            <div className="results">
              {notifications.map((item) => (
                <article className="result" key={item.title}>
                  <Badge tone={item.tone}>{item.tone}</Badge>
                  <h3>{item.title}</h3>
                  <p>{item.summary}</p>
                </article>
              ))}
            </div>
          </section>
        )}
      </div>
    </section>
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
  const tone = toneForAvailability(product.availability);
  return (
    <article className="product-card">
      <div className="card-top">
        <div>
          <span className="brand-mark mini" aria-hidden="true">{(product.icon || product.name).slice(0, 2)}</span>
          <Badge tone="info">{product.release_channel || product.family}</Badge>
          <h3>{product.name}</h3>
        </div>
        <Badge tone={tone}>{product.availability}</Badge>
      </div>
      <p>{product.summary}</p>
      <dl>
        <div><dt>Family</dt><dd>{product.family}</dd></div>
        <div><dt>Version</dt><dd>{product.release_version || product.version || "Published"}</dd></div>
        <div><dt>Regions</dt><dd>{(product.regions || []).join(", ")}</dd></div>
        <div><dt>Lifecycle</dt><dd>{product.lifecycle}</dd></div>
        <div><dt>Trust</dt><dd>{product.trust_status || "Verified"}</dd></div>
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

function ProductsPage({ products }) {
  const [query, setQuery] = useState("");
  const [availability, setAvailability] = useState("All");
  const [family, setFamily] = useState("All");
  const [region, setRegion] = useState("All");
  const families = useMemo(() => ["All", ...new Set(products.map((product) => product.family))], [products]);
  const regions = useMemo(() => ["All", ...new Set(products.flatMap((product) => product.regions || []))], [products]);
  const filtered = products.filter((product) => {
    const text = `${product.name} ${product.summary} ${product.family} ${(product.audiences || []).join(" ")} ${(product.features || []).join(" ")}`.toLowerCase();
    const matchesQuery = !query || text.includes(query.toLowerCase());
    const matchesAvailability = availability === "All" || product.availability === availability;
    const matchesFamily = family === "All" || product.family === family;
    const matchesRegion = region === "All" || (product.regions || []).includes(region);
    return matchesQuery && matchesAvailability && matchesFamily && matchesRegion;
  });
  return (
    <section className="detail">
      <Badge tone="info">Products</Badge>
      <h1>Product catalog</h1>
      <p>Browse governed products with explicit availability, region coverage, and trust posture. Pilot products remain labeled as such.</p>
      <div className="search-form">
        <div className="form-grid">
          <label>Search<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search products, audiences, or capabilities" /></label>
          <label>Availability
            <select value={availability} onChange={(event) => setAvailability(event.target.value)}>
              {["All", "Available", "Controlled Pilot", "Partner Access", "Coming Soon"].map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </label>
          <label>Family
            <select value={family} onChange={(event) => setFamily(event.target.value)}>
              {families.map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </label>
          <label>Region
            <select value={region} onChange={(event) => setRegion(event.target.value)}>
              {regions.map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </label>
        </div>
      </div>
      <div className="grid products-grid">
        {filtered.map((product) => <ProductCard key={product.product_id} product={product} />)}
      </div>
      <div className="detail-grid">
        <article>
          <h2>Featured routes</h2>
          <p>{filtered.slice(0, 4).map((product) => product.name).join(", ")}</p>
        </article>
        <article>
          <h2>Commercial note</h2>
          <p>Pricing and procurement terms are handled through the guided contact workflow and release approvals.</p>
        </article>
      </div>
    </section>
  );
}

function ServiceCard({ service }) {
  const tone = service.authentication_required ? "warning" : "trust";
  return (
    <article className="product-card">
      <div className="card-top">
        <div>
          <span className="brand-mark mini" aria-hidden="true">{(service.icon || service.name).slice(0, 2)}</span>
          <Badge tone="info">{service.audience || service.category}</Badge>
          <h3>{service.name}</h3>
        </div>
        <Badge tone={tone}>{service.status}</Badge>
      </div>
      <p>{service.domain}</p>
      <dl>
        <div><dt>Category</dt><dd>{service.category}</dd></div>
        <div><dt>Version</dt><dd>{service.version || "Published"}</dd></div>
        <div><dt>Region</dt><dd>{service.region || "Global"}</dd></div>
        <div><dt>Health</dt><dd>{service.health || "Healthy"}</dd></div>
        <div><dt>Indexing</dt><dd>{service.indexing}</dd></div>
        <div><dt>Auth</dt><dd>{service.authentication_required ? "Required" : "Public"}</dd></div>
      </dl>
      <a className="text-action" href={service.url} rel="noreferrer">Open surface</a>
    </article>
  );
}

function LauncherCard({ item }) {
  const tone = toneForAvailability(item.availability);
  return (
    <article className="product-card">
      <div className="card-top">
        <div>
          <span className="brand-mark mini" aria-hidden="true">{item.icon || item.name.slice(0, 2)}</span>
          <Badge tone="info">{item.audience}</Badge>
          <h3>{item.name}</h3>
        </div>
        <Badge tone={tone}>{item.availability}</Badge>
      </div>
      <p>{item.summary}</p>
      <dl>
        <div><dt>Authentication</dt><dd>{item.authentication_required ? "Required" : "Public"}</dd></div>
        <div><dt>Version</dt><dd>{item.version}</dd></div>
        <div><dt>Region</dt><dd>{item.region}</dd></div>
        <div><dt>Health</dt><dd>{item.health}</dd></div>
        <div><dt>Release channel</dt><dd>{item.release_channel}</dd></div>
      </dl>
      <a className="text-action" href={item.url} rel="noreferrer">Launch</a>
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
      <div className="detail-grid">
        <article>
          <h3>Security</h3>
          <p>Zero-trust routing, no invented certifications, and evidence-backed claims only.</p>
        </article>
        <article>
          <h3>Compliance</h3>
          <p>Policy, release, and approval records are separated from public marketing claims.</p>
        </article>
        <article>
          <h3>Certificates</h3>
          <p>Readiness, release, and verification certificates are generated from approved evidence.</p>
        </article>
        <article>
          <h3>Data residency</h3>
          <p>Supported regions are displayed explicitly and do not imply unverified availability.</p>
        </article>
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

function AppsPage({ launcher, services }) {
  const grouped = useMemo(() => launcher.reduce((acc, item) => {
    const key = item.audience || "Other";
    acc[key] = [...(acc[key] || []), item];
    return acc;
  }, {}), [launcher]);
  return (
    <section className="detail">
      <Badge tone="info">Application surfaces</Badge>
      <h1>Application launcher</h1>
      <p>Customers, businesses, partners, employees, and developers enter through a shared launcher. Each card shows availability, authentication, region, and release channel.</p>
      <div className="grid services-grid">
        {Object.entries(grouped).map(([audience, records]) => (
          <div key={audience} className="fabric-group">
            <div className="fabric-group-head">
              <h2>{audience}</h2>
              <p>{records.length} apps</p>
            </div>
            <div className="grid launcher-grid">
              {records.map((item) => <LauncherCard key={item.slug} item={item} />)}
            </div>
          </div>
        ))}
      </div>
      <div className="detail-grid">
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
      <section className="section" aria-labelledby="launcher-title">
        <div className="section-heading">
          <Badge tone="info">Launcher</Badge>
          <h2 id="launcher-title">One entry point for customers, partners, employees, and developers</h2>
          <p>Launch surfaces are grouped by audience and annotated with operational posture.</p>
        </div>
        <div className="grid launcher-grid">
          {(data.site?.launcher || fallbackSite.launcher || []).slice(0, 6).map((item) => <LauncherCard key={item.slug} item={item} />)}
        </div>
      </section>
      <FabricSection services={data.services || fallbackServices} />
      <AudienceTabs />
      <section className="band" aria-labelledby="docs-title">
        <div className="section-heading">
          <Badge tone="info">Documentation</Badge>
          <h2 id="docs-title">Developer docs, architecture, security, support, and knowledge</h2>
        </div>
        <div className="detail-grid">
          {(data.site?.documentation_sections || fallbackSite.documentation_sections || []).map((section) => (
            <article key={section.title} className="result">
              <h3>{section.title}</h3>
              <p>{section.summary}</p>
              <button className="text-action" onClick={() => navigate(section.href)} type="button">Open section</button>
            </article>
          ))}
        </div>
      </section>
      <TrustLayer trust={data.trust} status={data.status} />
      <section className="section" aria-labelledby="downloads-title">
        <div className="section-heading">
          <Badge tone="info">Downloads</Badge>
          <h2 id="downloads-title">Download Center</h2>
          <p>Signed artifacts and release evidence are published through governed download paths.</p>
        </div>
        <div className="detail-grid">
          {(data.downloads || data.site?.downloads || []).slice(0, 4).map((artifact) => (
            <article key={`${artifact.category}-${artifact.name}`} className="result">
              <Badge tone="trust">{artifact.category}</Badge>
              <h3>{artifact.name}</h3>
              <p>{artifact.version} · {artifact.supported_platforms?.join(", ")}</p>
              <small>{artifact.checksum}</small>
            </article>
          ))}
        </div>
      </section>
      <section className="band" aria-labelledby="verify-title">
        <div className="section-heading">
          <Badge tone="trust">Verification</Badge>
          <h2 id="verify-title">Receipts, release certificates, and public evidence</h2>
        </div>
        <div className="detail-grid">
          {(data.verifications || data.site?.verification_records || []).slice(0, 4).map((record) => (
            <article key={`${record.category}-${record.name}`} className="result">
              <Badge tone="info">{record.category}</Badge>
              <h3>{record.name}</h3>
              <p>{record.summary}</p>
            </article>
          ))}
        </div>
      </section>
      <Insights />
      <ContactCta />
    </>
  );
}

function ProductDetail({ products, slug }) {
  const product = products.find((item) => item.slug === slug) || fallbackProducts.find((item) => item.slug === slug);
  if (!product) return <GenericPage title="Product not found" description="The requested product is not published in the public catalog." />;
  const sections = [
    ["Capabilities", joinText(product.features)],
    ["Architecture", joinText(product.architecture) || `${product.name} is served through governed public routes and authenticated portals.`],
    ["Pricing", product.pricing || "Commercial terms are provided through the contact workflow and approved product guidance."],
    ["Demo", `Open ${product.portal_url}`],
    ["Documentation", product.documentation_url || "/developers"],
    ["API", product.api_url || "/developers"],
    ["Downloads", product.downloads_url || "/downloads"],
    ["Roadmap", product.lifecycle],
    ["Support", product.support_url || "/support"],
    ["Trust", product.trust_status || "Verified"],
  ];
  return (
    <section className="detail">
      <Badge tone={toneForAvailability(product.availability)}>{product.availability}</Badge>
      <h1>{product.name}</h1>
      <p>{product.summary}</p>
      <div className="detail-grid">
        <article>
          <h2>Release channel</h2>
          <p>{product.release_channel || "General availability"}</p>
        </article>
        <article>
          <h2>Version</h2>
          <p>{product.release_version || "Published"}</p>
        </article>
        <article>
          <h2>Health</h2>
          <p>{product.health || "Healthy"}</p>
        </article>
        <article>
          <h2>Regions</h2>
          <p>{joinText(product.regions)}</p>
        </article>
      </div>
      <div className="detail-grid">
        {sections.map(([title, summary]) => (
          <article key={title}>
            <h2>{title}</h2>
            <p>{summary}</p>
          </article>
        ))}
      </div>
      {product.screenshots && (
        <div className="grid">
          {product.screenshots.map((shot) => (
            <article key={shot} className="result">
              <h3>{shot}</h3>
              <p>Approved preview from the governed product record.</p>
            </article>
          ))}
        </div>
      )}
      {product.faqs && (
        <div className="detail-grid">
          {product.faqs.map((faq) => (
            <article key={faq}>
              <h2>FAQ</h2>
              <p>{faq}</p>
            </article>
          ))}
        </div>
      )}
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
      const downloadResults = (fallbackSite.downloads || [])
        .filter((artifact) => `${artifact.name} ${artifact.category} ${artifact.version} ${artifact.checksum}`.toLowerCase().includes(q))
        .map((artifact) => ({ type: "download", title: artifact.name, summary: `${artifact.category} · ${artifact.version}`, href: artifact.href, availability: artifact.version }));
      const verificationResults = (fallbackSite.verifications || [])
        .filter((record) => `${record.name} ${record.category} ${record.summary} ${record.evidence}`.toLowerCase().includes(q))
        .map((record) => ({ type: "verification", title: record.name, summary: `${record.category} · ${record.evidence}`, href: record.lookup, availability: "Public" }));
      setState({
        status: "degraded",
        results: [...productResults, ...serviceResults, ...downloadResults, ...verificationResults],
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
            <Badge tone={result.type === "download" ? "warning" : result.type === "verification" ? "trust" : "info"}>{result.type || "result"}</Badge>
            <h2>{result.title}</h2>
            <p>{result.summary}</p>
            <button className="text-action" onClick={() => openHref(result.href)}>Open result</button>
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

function DashboardPage({ workspace, status, products, services }) {
  const workspaceLabel = workspace === "guest" ? "Guest" : workspace[0].toUpperCase() + workspace.slice(1);
  return (
    <section className="detail">
      <Badge tone="trust">Workspace</Badge>
      <h1>{workspaceLabel} dashboard</h1>
      <p>Signed-in users see projects, approvals, saved items, and AI recommendations from the shared shell.</p>
      <div className="grid dashboard-grid">
        <article className="result"><h2>Recent projects</h2><p>Governed delivery, product rollouts, integration work, and release verification.</p></article>
        <article className="result"><h2>Approvals</h2><p>Pending product, release, and policy approvals are grouped here.</p></article>
        <article className="result"><h2>Notifications</h2><p>Evidence updates, release notices, and support responses appear in one stream.</p></article>
        <article className="result"><h2>Health</h2><p>{status.overall} · {status.components?.length || 0} monitored public surfaces.</p></article>
      </div>
      <div className="detail-grid">
        <article>
          <h2>Recommended products</h2>
          <p>{products.slice(0, 3).map((product) => product.name).join(", ")}</p>
        </article>
        <article>
          <h2>Relevant surfaces</h2>
          <p>{services.slice(0, 3).map((service) => service.name).join(", ")}</p>
        </article>
      </div>
    </section>
  );
}

function KnowledgePage() {
  const topics = [
    ["Architecture", "Reference architecture, models, and platform boundaries."],
    ["Runbooks", "Operational procedures and recovery steps."],
    ["Policies", "Governed rules for safety, finance, and compliance."],
    ["Guides", "Task-oriented product and integration guidance."],
    ["FAQs", "Common questions for customers, partners, and developers."],
    ["Tutorials", "Walkthroughs for supported workflows and release steps."],
  ];
  return (
    <section className="detail">
      <Badge>Knowledge</Badge>
      <h1>Enterprise knowledge portal</h1>
      <p>A single place for architecture, runbooks, playbooks, FAQs, and governed operational guidance.</p>
      <div className="grid">
        {topics.map(([name, summary]) => (
          <article className="result" key={name}>
            <h2>{name}</h2>
            <p>{summary}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function PartnerPage() {
  const features = ["Partner dashboard", "Partner APIs", "Marketplace", "Training", "Certification", "Revenue", "Co-selling", "Support handoff"];
  return (
    <section className="detail">
      <Badge tone="info">Partners</Badge>
      <h1>Partner portal</h1>
      <p>Partner access groups integration, certification, and co-selling into a governed workspace.</p>
      <div className="grid">
        {features.map((feature) => (
          <article className="result" key={feature}>
            <h2>{feature}</h2>
            <p>Tracked through the shell and the partner program workflow.</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function DeveloperExperiencePage({ site = fallbackSite }) {
  const sections = site.documentation_sections || [
    { title: "Developer Docs", summary: "API reference, SDKs, sandbox, and status.", href: "/developers" },
    { title: "Quick Starts", summary: "Launch guides for customers, businesses, partners, and developers.", href: "/knowledge" },
    { title: "Security", summary: "Trust, verification, and release integrity.", href: "/trust" },
    { title: "Support", summary: "Guided support entry and contact workflow.", href: "/support" },
  ];
  const features = ["API Explorer", "OpenAPI", "SDK Downloads", "CLI", "Examples", "Sandbox", "Authentication", "Rate limits", "Status", "Changelog"];
  return (
    <section className="detail">
      <Badge tone="info">Developers</Badge>
      <h1>Developer portal</h1>
      <p>Documentation, API discovery, and sandbox tooling are exposed as a governed experience.</p>
      <div className="detail-grid">
        {sections.map((section) => (
          <article key={section.title}>
            <h2>{section.title}</h2>
            <p>{section.summary}</p>
            <button className="text-action" type="button" onClick={() => navigate(section.href)}>Open section</button>
          </article>
        ))}
      </div>
      <div className="grid">
        {features.map((feature) => (
          <article className="result" key={feature}>
            <h2>{feature}</h2>
            <p>Available through the public shell and platform routes.</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function ArchitectureExplorerPage() {
  const layers = [
    ["Governance", "Policies, approvals, risk, compliance."],
    ["Platform", "NovaID, NovaAI, NovaCloud, NovaConnect, NovaGateway."],
    ["Knowledge", "Runbooks, ADRs, evidence, lessons learned."],
    ["Products", "NovaRide, NovaPay, NovaHealth, NovaCommerce, NovaHouseReach, NovaDashDoor, NovaLogistics."],
    ["Apps", "Public web, portals, dashboards, and workspace shells."],
  ];
  return (
    <section className="detail">
      <Badge tone="trust">Architecture</Badge>
      <h1>Enterprise architecture explorer</h1>
      <p>Navigate the layers from governance to apps using governed records rather than static diagrams.</p>
      <div className="detail-grid">
        {layers.map(([name, summary]) => (
          <article key={name}>
            <h2>{name}</h2>
            <p>{summary}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function VerifyPage({ records = fallbackSite.verifications || [] }) {
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
      <div className="grid">
        {records.map((record) => (
          <article key={`${record.category}-${record.name}`} className="result">
            <Badge tone={record.category === "Releases" ? "warning" : record.category === "Certificates" ? "trust" : "info"}>{record.category}</Badge>
            <h3>{record.name}</h3>
            <p>{record.summary}</p>
            <p>{record.evidence}</p>
          </article>
        ))}
      </div>
    </GenericPage>
  );
}

function DownloadsPage({ artifacts = fallbackSite.downloads || [] }) {
  const grouped = useMemo(() => artifacts.reduce((acc, artifact) => {
    const key = artifact.category || "Other";
    acc[key] = [...(acc[key] || []), artifact];
    return acc;
  }, {}), [artifacts]);
  return (
    <GenericPage title="Download Center" description="Signed artifacts, release bundles, and evidence exports are published through governed download paths.">
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
      {Object.entries(grouped).map(([category, items]) => (
        <section key={category} className="fabric-group">
          <div className="fabric-group-head">
            <h2>{category}</h2>
            <p>{items.length} artifacts</p>
          </div>
          <div className="grid">
            {items.map((artifact) => (
              <article key={`${artifact.name}-${artifact.version}`} className="result">
                <Badge tone={category === "Evidence Packages" ? "trust" : "warning"}>{artifact.version}</Badge>
                <h3>{artifact.name}</h3>
                <p>{joinText(artifact.supported_platforms)}</p>
                <p><code>{artifact.checksum}</code></p>
                <p><code>{artifact.signature}</code></p>
                <p>{artifact.published_at}</p>
                <div className="actions">
                  <a className="text-action" href={artifact.href} rel="noreferrer">Open artifact</a>
                  <button className="text-action" type="button" onClick={() => navigate(artifact.release_notes)}>Release notes</button>
                </div>
              </article>
            ))}
          </div>
        </section>
      ))}
    </GenericPage>
  );
}

function StatusPage({ status }) {
  return (
    <GenericPage title="Public Status" description={status.note || "Measured status appears here after live operational verification."}>
      <div className="detail-grid">
        <article>
          <h2>Current incidents</h2>
          <p>{(status.current_incidents || []).length ? status.current_incidents.map((incident) => incident.title).join(", ") : "None reported."}</p>
        </article>
        <article>
          <h2>Latency</h2>
          <p>{status.latency?.p95_ms ? `p95 ${status.latency.p95_ms}ms` : "No measured latency yet."}</p>
        </article>
        <article>
          <h2>Availability</h2>
          <p>{status.availability ? `${status.availability.public_site} · ${status.availability.apps} · ${status.availability.api}` : status.overall}</p>
        </article>
        <article>
          <h2>Regions</h2>
          <p>{(status.regions || []).map((region) => region.region).join(", ")}</p>
        </article>
      </div>
      <div className="grid">
        {["Gateway", "Authentication", "Payments", "Messaging", "Observability"].map((name) => {
          const component = (status.components || []).find((item) => item.name.toLowerCase().includes(name.toLowerCase()));
          return (
            <article className="capability" key={name}>
              <h2>{name}</h2>
              <p>{component?.state || "Measured via public evidence"}</p>
            </article>
          );
        })}
      </div>
      <div className="grid">
        {(status.components || []).map((component) => (
          <article className="capability" key={component.name}>
            <h2>{component.name}</h2>
            <p>{component.state}</p>
          </article>
        ))}
      </div>
      <div className="detail-grid">
        {(status.history || []).map((entry) => (
          <article key={entry.label}>
            <h2>{entry.label}</h2>
            <p>{entry.value}</p>
          </article>
        ))}
      </div>
    </GenericPage>
  );
}

function App() {
  const path = usePath();
  const [data, setData] = useState(null);
  const [theme, setTheme] = useStoredState("afritech-public-theme", "light");
  const [language, setLanguage] = useStoredState("afritech-public-language", "en");
  const [workspace, setWorkspace] = useStoredState("afritech-public-workspace", "guest");
  const [signedIn, setSignedIn] = useStoredState("afritech-public-signed-in", "false");
  const [commandOpen, setCommandOpen] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(true);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  useEffect(() => {
    loadPublicGateway().then(setData);
  }, []);
  useEffect(() => {
    const isNovaHouseReach = path === "/products/novahousereach";
    const isNovaDashDoor = path === "/products/novadashdoor";
    const isNovaLogistics = path === "/products/novalogistics";
    const isNovaPay = path === "/products/novapay";
    const isNovaID = path === "/products/novaid";
    const isNovaTrust = path === "/products/novatrust";
    const isNovaCommerce = path === "/products/novacommerce";
    const isNovaCloud = path === "/products/novacloud";
    const isNovaConnect = path === "/products/novaconnect";
    const title = pages[path]
      ? `${pages[path]} | AfriTechnology`
      : path.startsWith("/products/")
        ? "Product | AfriTechnology"
        : "AfriTechnology | Trusted Digital Platforms";
    document.title = path === "/" ? "AfriTechnology | Trusted Digital Platforms" : title;
    const description = path === "/downloads"
      ? "Signed artifacts, checksums, and release evidence for AfriTechnology."
      : path === "/verify"
        ? "Receipt, release, and evidence verification for the AfriTechnology ecosystem."
        : path === "/apps"
          ? "Application launcher and governed portal discovery for the AfriTechnology ecosystem."
          : path === "/products"
            ? "Governed product catalog for AfriTechnology platforms and services."
            : isNovaHouseReach
              ? "NovaHouseReach is NovaTech's property operating system for discovery, finance, lease management, maintenance, and trust."
              : isNovaDashDoor
                ? "NovaDashDoor is NovaTech's AI-powered local commerce and last-mile delivery platform."
                : isNovaLogistics
                  ? "NovaLogistics X is NovaTech's logistics operating system for parcels, freight, warehousing, and chain of custody."
                  : isNovaPay
                    ? "NovaPay is NovaTech's payments and financial operations platform for wallets, settlement, and trust-backed money movement."
                    : isNovaID
                      ? "NovaID is NovaTech's identity and access platform for passkeys, verification, consent, and device trust."
                      : isNovaTrust
                        ? "NovaTrust is NovaTech's evidence, assurance, policy, and verification platform."
                        : isNovaCommerce
                          ? "NovaCommerce is NovaTech's commerce operating system for merchants, customers, inventory, and checkout."
                          : isNovaCloud
                            ? "NovaCloud is NovaTech's cloud infrastructure and platform services layer."
                            : isNovaConnect
                              ? "NovaConnect is NovaTech's API gateway, integrations, and partner ecosystem."
            : "Secure, intelligent, and connected digital platforms for payments, mobility, identity, commerce, healthcare, logistics, government, and enterprise operations.";
    const robots = path === "/dashboard" ? "noindex,nofollow" : "index,follow";
    document.querySelector('meta[name="description"]')?.setAttribute("content", description);
    document.querySelector('meta[name="robots"]')?.setAttribute("content", robots);
    document.querySelector('meta[property="og:title"]')?.setAttribute("content", document.title);
    document.querySelector('meta[property="og:description"]')?.setAttribute("content", description);
    document.querySelector('link[rel="canonical"]')?.setAttribute("href", path === "/" ? "https://afritechnology.com/" : `https://afritechnology.com${path}`);
    document.documentElement.lang = language === "sw" ? "sw" : language === "fr" ? "fr" : "en";
  }, [path, language]);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.language = language;
  }, [theme, language]);
  useEffect(() => {
    const onKeyDown = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((current) => !current);
      }
      if (event.key === "Escape") {
        setCommandOpen(false);
        setAssistantOpen(false);
        setNotificationsOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
  const shellSite = data?.site || fallbackSite;
  const shellServices = data?.services || fallbackServices;
  const shellProducts = data?.products || fallbackProducts;
  const shellDownloads = data?.downloads || shellSite.downloads || [];
  const shellVerifications = data?.verifications || shellSite.verifications || [];
  const searchIndex = useMemo(
    () => buildSearchIndex(shellSite, shellProducts, shellServices, shellDownloads, shellVerifications),
    [shellSite, shellProducts, shellServices, shellDownloads, shellVerifications],
  );
  const route = useMemo(() => path.replace(/\/$/, "") || "/", [path]);
  if (!data) return <main id="main" className="loading" aria-live="polite">Loading AfriTechnology...</main>;
  const page = route.startsWith("/products/") ? (
    route === "/products/novahousereach" ? (
      <NovaHouseReachDetail navigate={navigate} />
    ) : route === "/products/novadashdoor" ? (
      <NovaDashDoorDetail navigate={navigate} />
    ) : route === "/products/novalogistics" ? (
      <NovaLogisticsDetail navigate={navigate} />
    ) : route === "/products/novapay" ? (
      <NovaPayDetail navigate={navigate} />
    ) : route === "/products/novaid" ? (
      <NovaIDDetail navigate={navigate} />
    ) : route === "/products/novatrust" ? (
      <NovaTrustDetail navigate={navigate} />
    ) : route === "/products/novacommerce" ? (
      <NovaCommerceDetail navigate={navigate} />
    ) : route === "/products/novacloud" ? (
      <NovaCloudDetail navigate={navigate} />
    ) : route === "/products/novaconnect" ? (
      <NovaConnectDetail navigate={navigate} />
    ) : (
      <ProductDetail products={data.products} slug={route.split("/").pop()} />
    )
  ) : route === "/" ? (
    <Home data={data} />
  ) : route === "/products" ? (
    <ProductsPage products={data.products} />
  ) : route === "/apps" ? (
    <AppsPage launcher={shellSite.launcher || fallbackSite.launcher || []} services={shellServices} />
  ) : route === "/dashboard" ? (
    <DashboardPage workspace={workspace} status={data.status} products={data.products} services={data.services || fallbackServices} />
  ) : route === "/platform" ? (
    <><PlatformSection /><AudienceTabs /></>
  ) : route === "/trust" ? (
    <TrustLayer trust={data.trust} status={data.status} />
  ) : route === "/knowledge" ? (
    <KnowledgePage />
  ) : route === "/partners" ? (
    <PartnerPage />
  ) : route === "/verify" ? (
    <VerifyPage records={shellVerifications} />
  ) : route === "/downloads" ? (
    <DownloadsPage artifacts={shellDownloads} />
  ) : route === "/contact" ? (
    <ContactPage />
  ) : route === "/search" ? (
    <SearchPage />
  ) : route === "/status" ? (
    <StatusPage status={data.status} />
  ) : route === "/developers" ? (
    <DeveloperExperiencePage site={shellSite} />
  ) : route === "/solutions" ? (
    <GenericPage title="Solutions" description="Audience-specific paths for customers, businesses, enterprises, developers, partners, and governments." />
  ) : route === "/industries" ? (
    <GenericPage title="Industries" description="Payments, mobility, identity, commerce, healthcare, logistics, government, and enterprise operations." />
  ) : route === "/architecture" ? (
    <ArchitectureExplorerPage />
  ) : route === "/support" ? (
    <GenericPage title="Support" description="Support requests are routed through the contact workflow and assigned an auditable reference." />
  ) : route === "/accessibility" ? (
    <GenericPage title="Accessibility" description="AfriTechnology targets WCAG 2.2 AA with automated checks and human review for major releases." />
  ) : route === "/legal/privacy" ? (
    <GenericPage title="Privacy" description="Privacy-conscious analytics, consent-aware routing, and data minimization are required for public workflows." />
  ) : route === "/legal/terms" ? (
    <GenericPage title="Terms" description="Public terms and product-specific terms are governed content records." />
  ) : route === "/docs" ? (
    <DeveloperExperiencePage site={shellSite} />
  ) : (
    <GenericPage title={pages[route] || "AfriTechnology"} description="This page is part of the public AfriTechnology gateway and does not serve internal dashboards." />
  );
  return (
    <>
      <NovaShellChrome
        site={shellSite}
        path={route}
        language={language}
        setLanguage={setLanguage}
        workspace={workspace}
        setWorkspace={setWorkspace}
        signedIn={signedIn === "true"}
        setSignedIn={(value) => setSignedIn(String(value))}
        theme={theme}
        setTheme={setTheme}
        commandOpen={commandOpen}
        setCommandOpen={setCommandOpen}
        assistantOpen={assistantOpen}
        setAssistantOpen={setAssistantOpen}
        notificationsOpen={notificationsOpen}
        setNotificationsOpen={setNotificationsOpen}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        searchIndex={searchIndex}
      />
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
