import React, { useState } from "react";

const CAPABILITIES = [
  ["AI Designer", "Turn governed requirements into flows, screens, components, and implementation-ready specifications."],
  ["Wireframing", "Move from low-fidelity structure to responsive, content-aware layouts without losing traceability."],
  ["Prototyping", "Connect states, decisions, forms, and transitions in reviewable end-to-end journeys."],
  ["Design systems", "Manage tokens, themes, variants, accessibility metadata, and controlled product brands."],
  ["Research & personas", "Link evidence, people, pain points, journeys, and design decisions in one workspace."],
  ["Accessibility", "Find issues early, document human review, and preserve evidence against applicable standards."],
  ["Collaboration", "Coordinate comments, tasks, reviews, approvals, presence, and version history."],
  ["Developer handoff", "Deliver responsive rules, tokens, states, contracts, assets, and acceptance criteria."],
  ["Governed export", "Create permission-controlled packages with versions, checksums, approvals, and audit history."],
];

const DEMO_PROJECTS = [
  ["NovaRide Rider", "Mobility", "Mobile journey · 18 screens"],
  ["NovaPay Wallet", "Financial services", "Responsive wallet · 24 screens"],
  ["NovaID Identity Centre", "Identity", "Accessible sign-in · 12 states"],
  ["NovaHealth Portal", "Healthcare", "Patient service · 16 flows"],
  ["NovaLogistics Operations", "Logistics", "Operations console · 9 views"],
  ["Government Services Portal", "Public sector", "Citizen services · 21 screens"],
];

const TRUST_CONTROLS = [
  "NovaID authentication",
  "Encryption in transit and at rest",
  "Tenant and workspace isolation",
  "Role-based access control",
  "Immutable audit history",
  "Version-bound approvals",
  "Evidence traceability",
  "Permission-controlled exports",
];

function PublicIcon({ name }) {
  const paths = {
    canvas: "M4 5h16v14H4z M8 9h8 M8 13h5",
    device: "M7 3h10v18H7z M10 17h4",
    layers: "m4 8 8-4 8 4-8 4z M4 12l8 4 8-4 M4 16l8 4 8-4",
    ai: "M12 3l1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7z M18 15l.8 2.2L21 18l-2.2.8L18 21l-.8-2.2L15 18l2.2-.8z",
  };
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="public-icon">
      <path d={paths[name] || paths.canvas} />
    </svg>
  );
}

export function PublicLandingPage({ session, onNavigate }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [theme, setTheme] = useState("system");
  const [language, setLanguage] = useState("en-AU");
  const go = (path) => onNavigate(path);

  return (
    <div className="public-site" data-theme={theme} data-testid="novacodepro-public-page">
      <a className="skip-link" href="#public-main">Skip to main content</a>
      <header className="public-header">
        <button className="public-brand" type="button" onClick={() => go("/novacodepro/")} aria-label="NovaCodePro home">
          <img src="/novacodepro/brand/NOVACODEPRO.webp" alt="" />
          <span>NovaCodePro</span>
        </button>
        <button
          className="public-menu-button"
          type="button"
          aria-expanded={menuOpen}
          aria-controls="public-navigation"
          onClick={() => setMenuOpen((value) => !value)}
        >
          <span aria-hidden="true">☰</span>
          <span>Menu</span>
        </button>
        <nav id="public-navigation" className={menuOpen ? "public-nav open" : "public-nav"} aria-label="Platform navigation">
          {["Platform", "Products", "Solutions", "Resources", "Developers", "Documentation", "Trust & security"].map((item) => (
            <a key={item} href={`#${item.toLowerCase().replaceAll(/[^a-z]+/g, "-")}`} onClick={() => setMenuOpen(false)}>{item}</a>
          ))}
        </nav>
        <div className="public-header-actions">
          <label className="public-select"><span className="sr-only">Theme</span><select value={theme} onChange={(event) => setTheme(event.target.value)} aria-label="Theme"><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option><option value="contrast">High contrast</option></select></label>
          <label className="public-select"><span className="sr-only">Language</span><select value={language} onChange={(event) => setLanguage(event.target.value)} aria-label="Language"><option value="en-AU">EN</option><option value="fr">FR</option><option value="sw">SW</option></select></label>
          {session ? <button type="button" className="public-text-button" onClick={() => go("/novacodepro/dashboard")}>Open workspace</button> : <button type="button" className="public-text-button" onClick={() => go("/novacodepro/login")}>Sign in</button>}
          <button type="button" className="public-primary compact" onClick={() => go("/novacodepro/login?returnTo=%2Fnovacodepro%2Fdesign")}>Start designing</button>
        </div>
      </header>

      <main id="public-main">
        <section className="public-hero" aria-labelledby="public-title">
          <div className="public-hero-copy">
            <div className="public-kicker"><span /> AI-native enterprise design</div>
            <p className="public-product-name">NovaCodePro</p>
            <h1 id="public-title">UI/UX Design &amp;<br /><span>Wireframing Studio</span></h1>
            <p className="public-lede">Design beautiful, accessible, intelligent applications from one governed workspace.</p>
            <div className="public-hero-actions">
              <button type="button" className="public-primary" onClick={() => go("/novacodepro/login?returnTo=%2Fnovacodepro%2Fdesign")}>Start Designing <span aria-hidden="true">→</span></button>
              <button type="button" className="public-secondary" onClick={() => go("/novacodepro/login?returnTo=%2Fnovacodepro%2Fai")}>Generate from Prompt</button>
              <button type="button" className="public-secondary" onClick={() => go("/novacodepro/login?returnTo=%2Fnovacodepro%2Frequests")}>Import Requirements</button>
              <button type="button" className="public-link-action" onClick={() => go("/novacodepro/login?returnTo=%2Fnovacodepro%2Fprojects")}>Open Existing Project</button>
            </div>
            <ul className="public-proof-list" aria-label="Platform benefits">
              <li>Requirements traceability</li><li>Accessibility-first</li><li>Governed design-to-code</li>
            </ul>
          </div>

          <div className="public-product-preview" aria-label="Interactive NovaCodePro studio preview">
            <div className="preview-topbar"><div className="preview-dots"><i /><i /><i /></div><strong>NovaPay Business Dashboard</strong><span>Saved · v12</span></div>
            <div className="preview-body">
              <aside className="preview-tools" aria-label="Preview tools"><button aria-label="Canvas"><PublicIcon name="canvas" /></button><button aria-label="Devices"><PublicIcon name="device" /></button><button aria-label="Layers"><PublicIcon name="layers" /></button><button aria-label="AI assistant"><PublicIcon name="ai" /></button></aside>
              <aside className="preview-layers"><p>LAYERS</p><strong>Business dashboard</strong><span>⌄ Header</span><span>⌄ Balance cards</span><span>⌄ Activity chart</span><span>⌄ Approval queue</span><span>Compliance alerts</span></aside>
              <div className="preview-canvas">
                <div className="preview-frame">
                  <div className="preview-frame-nav"><b>NovaPay</b><span>Overview</span><span>Transactions</span><span>Approvals</span><i /></div>
                  <div className="preview-welcome"><span>Good morning, Amara</span><strong>Business overview</strong></div>
                  <div className="preview-metrics"><article><span>Available balance</span><strong>$284,920</strong><em>+8.4% this month</em></article><article><span>Pending approvals</span><strong>12</strong><em>3 need attention</em></article><article><span>Compliance</span><strong>96%</strong><em>All checks current</em></article></div>
                  <div className="preview-chart"><div><span>Cash flow</span><strong>Last 30 days</strong></div><svg viewBox="0 0 300 90" role="img" aria-label="Demonstration cash flow chart"><path d="M0 72 C35 65 42 38 76 47 S120 68 150 43 S205 18 230 34 S270 45 300 14" /></svg></div>
                </div>
                <div className="preview-score"><span>Accessibility</span><strong>98</strong><small>WCAG review ready</small></div>
              </div>
              <aside className="preview-properties"><p>DESIGN REVIEW</p><div className="review-ring">94<small>/100</small></div><span><i className="good" /> Accessibility 98</span><span><i className="good" /> Consistency 96</span><span><i /> Usability 92</span><button type="button">Open review</button></aside>
            </div>
            <div className="preview-status"><span><i /> 3 collaborators</span><span>7 comments</span><span>Developer handoff ready</span><strong>142 components mapped</strong></div>
          </div>
        </section>

        <section className="public-process" aria-label="End-to-end design lifecycle">
          {['Idea','Requirements','Research','Personas','Journeys','Flows','Wireframes','Prototype','Handoff'].map((step, index) => <React.Fragment key={step}><span>{step}</span>{index < 8 ? <i aria-hidden="true">→</i> : null}</React.Fragment>)}
        </section>

        <section className="public-section" id="platform">
          <div className="public-section-heading"><p>ONE GOVERNED WORKSPACE</p><h2>From the first idea to production-ready design.</h2><span>Every artifact stays connected to its evidence, requirement, component, review, version, and implementation contract.</span></div>
          <div className="capability-grid">{CAPABILITIES.map(([title, description], index) => <article key={title}><span className="capability-number">{String(index + 1).padStart(2, '0')}</span><h3>{title}</h3><p>{description}</p><a href="#product-preview">Explore capability <span aria-hidden="true">↗</span></a></article>)}</div>
        </section>

        <section className="public-section demo-section" id="product-preview">
          <div className="public-section-heading"><p>EXPLORE THE STUDIO</p><h2>Demonstration projects, clearly separated from your work.</h2><span>These public examples illustrate supported product patterns. Signed-in workspaces load only projects the current tenant permits.</span></div>
          <div className="demo-grid">{DEMO_PROJECTS.map(([name, sector, detail], index) => <article key={name}><div className={`demo-art demo-${index + 1}`}><span>{name.slice(0, 2).toUpperCase()}</span></div><div><p>DEMONSTRATION</p><h3>{name}</h3><span>{sector}</span><small>{detail}</small></div></article>)}</div>
        </section>

        <section className="trust-section" id="trust-security">
          <div><p>ENTERPRISE TRUST</p><h2>Creativity without compromising control.</h2><span>NovaCodePro keeps identity, tenancy, evidence, versions, approvals, and exports inside the same governed operating model.</span><button className="public-secondary inverse" type="button" onClick={() => go("/novacodepro/login")}>Explore trust &amp; security</button></div>
          <div className="trust-grid">{TRUST_CONTROLS.map((control) => <span key={control}><i aria-hidden="true">✓</i>{control}</span>)}</div>
        </section>

        <section className="public-cta"><p>READY TO DESIGN WITH INTELLIGENCE?</p><h2>Build the experience. Prove every decision.</h2><div><button type="button" className="public-primary light" onClick={() => go("/novacodepro/login?returnTo=%2Fnovacodepro%2Fdesign")}>Start Designing</button><button type="button" className="public-secondary inverse" onClick={() => go("/novacodepro/login?returnTo=%2Fnovacodepro%2Fai")}>Generate from Prompt</button></div></section>
      </main>

      <footer className="public-footer">
        <div className="public-footer-brand"><strong>NovaCodePro</strong><p>AI-native design, engineering, and governance for digital products.</p><span>© 2026 AfriTechnology</span></div>
        {[['Product','Platform','AI Designer','Wireframing','Design systems','Accessibility'],['Developers','Documentation','API','SDK','Status','Support'],['Company','Security','Privacy','Terms','Contact','Careers']].map(([title, ...links]) => <div key={title}><strong>{title}</strong>{links.map((link) => <a key={link} href={`#${link.toLowerCase().replaceAll(/[^a-z]+/g, '-')}`}>{link}</a>)}</div>)}
      </footer>
    </div>
  );
}
