import React, { useEffect, useMemo, useState } from "react";

import { createNovaCodeProNcp006bApi } from "../novacodepro/api/novacodeproNcp006bApi.js";

const TOKEN_CATEGORIES = ["COLOR", "TYPOGRAPHY", "ICON", "SPACING", "SIZING", "RADIUS", "BORDER", "SHADOW", "ELEVATION", "MOTION", "BREAKPOINT", "GRID", "LAYOUT", "Z_INDEX", "OPACITY"];
const COMPONENTS = ["Button", "Input", "Select", "Checkbox", "Radio", "Switch", "Card", "Navigation", "Breadcrumb", "Tabs", "Form", "Chart", "Table", "Data grid", "Map", "Calendar", "Dialog", "Drawer", "Toast", "Timeline", "Tree", "Kanban", "Upload", "Avatar", "Badge", "Skeleton", "Search", "Pagination", "Command palette"];
const BRANDS = ["NovaCodePro", "NovaRide", "NovaPay", "NovaID", "NovaHealth", "NovaLogistics"];
function errorMessage(error, fallback) { return typeof error?.message === "string" ? error.message : error?.message?.message || error?.detail?.message || fallback; }

export function DesignSystemStudio({ session, baseUrl = "", initialSection = "Components", onNavigate }) {
  const api = useMemo(() => createNovaCodeProNcp006bApi({ baseUrl, session }), [baseUrl, session]);
  const [section, setSection] = useState(initialSection);
  const [data, setData] = useState({ tokens: [], themes: [], components: [], systems: [], brands: [] });
  const [status, setStatus] = useState("Loading design system…");
  const [token, setToken] = useState({ name: "brand.primary", path: "brand.primary", category: "COLOR", level: "SEMANTIC", value: "#5b5ce2" });
  const [component, setComponent] = useState({ name: "Primary Button", category: "ACTION", version: "1.0.0" });
  const [brand, setBrand] = useState({ name: "NovaCodePro", logo_uri: "/novacodepro/brand/NOVACODEPRO.webp", colours: "#5b5ce2, #111827", fonts: "Inter, Georgia", voice: "Precise, accountable, empowering", accessibility_rules: "WCAG 2.2 AA; visible focus; reduced motion" });

  async function reload() {
    try {
      const [tokens, themes, components, systems, brands] = await Promise.all([api.listDesignTokens(), api.listThemes(), api.listComponents(), api.listDesignSystems(), api.listBrands()]);
      setData({ tokens, themes, components, systems, brands }); setStatus("Design system synchronized");
    } catch (error) { setStatus(errorMessage(error, "Design system unavailable")); }
  }
  useEffect(() => { reload(); }, [api]);
  useEffect(() => { setSection(initialSection); }, [initialSection]);

  async function save(kind) {
    setStatus("Saving governed artifact…");
    try {
      if (kind === "token") await api.createDesignToken({ ...token, aliases: [], inheritance: [], metadata: { theme_modes: ["LIGHT", "DARK", "HIGH_CONTRAST"] } });
      if (kind === "component") await api.createComponent({ ...component, properties: [{ name: "label", type: "string", required: true }], variants: ["PRIMARY", "SECONDARY", "DANGER"], states: ["DEFAULT", "HOVER", "FOCUS", "DISABLED", "LOADING"], responsive_behavior: { compact_below: 480 }, accessibility: { role: "button", keyboard: ["Enter", "Space"], focus_visible: true }, usage_documentation: "Use one primary action per task.", code_examples: { react: "<Button variant=\"primary\" />" } });
      if (kind === "brand") await api.createBrand({ ...brand, attributes: brand, inheritance: { controlled_overrides: true }, status: "DRAFT" });
      await reload(); setStatus(`${kind[0].toUpperCase()}${kind.slice(1)} saved and versioned`);
    } catch (error) { setStatus(errorMessage(error, "Save failed")); }
  }

  return <div className="system-studio" data-testid="design-system-studio">
    <header><button type="button" className="studio-logo" onClick={() => onNavigate("/novacodepro/dashboard")}>N</button><div><p>ENTERPRISE DESIGN LANGUAGE</p><h1>Components, tokens & brands</h1></div><span aria-live="polite">● {status}</span><button type="button" onClick={() => onNavigate("/novacodepro/design/studio")}>Open canvas</button></header>
    <nav aria-label="Design system navigation">{["Components","Design System","Brand Studio","Templates"].map((name) => <button type="button" className={section === name ? "active" : ""} key={name} onClick={() => setSection(name)}>{name}</button>)}</nav>
    <aside><label>Search library<input placeholder="Search components and tokens"/></label><strong>Library</strong>{COMPONENTS.map((name) => <button type="button" key={name}>◇ {name}</button>)}</aside>
    <main>
      {section === "Components" && <><div className="system-title"><div><p>COMPONENT LIBRARY</p><h2>Reusable, accessible components</h2></div><b>{data.components.length} governed definitions</b></div><div className="component-showcase">{COMPONENTS.slice(0,12).map((name, index) => <article key={name}><div className={`component-demo demo-${index}`}><span>{name}</span></div><strong>{name}</strong><small>Responsive · Accessible · Versioned</small></article>)}</div><section className="system-editor"><h3>Create component definition</h3><label>Name<input value={component.name} onChange={(e) => setComponent({ ...component, name: e.target.value })}/></label><label>Category<input value={component.category} onChange={(e) => setComponent({ ...component, category: e.target.value })}/></label><button type="button" onClick={() => save("component")}>Save component</button></section></>}
      {section === "Design System" && <><div className="system-title"><div><p>TOKEN ARCHITECTURE</p><h2>Global → semantic → component</h2></div><b>{data.tokens.length} tokens · {data.themes.length} themes</b></div><div className="token-categories">{TOKEN_CATEGORIES.map((name) => <span key={name}>{name.replaceAll("_", " ")}</span>)}</div><section className="token-editor"><div className="token-preview" style={{ background: token.value }} aria-label="Token colour preview"/><label>Token path<input value={token.path} onChange={(e) => setToken({ ...token, path: e.target.value, name: e.target.value })}/></label><label>Category<select value={token.category} onChange={(e) => setToken({ ...token, category: e.target.value })}>{TOKEN_CATEGORIES.map((name) => <option key={name}>{name}</option>)}</select></label><label>Value<input value={token.value} onChange={(e) => setToken({ ...token, value: e.target.value })}/></label><button type="button" onClick={() => save("token")}>Save design token</button></section><div className="theme-strip">{["Light", "Dark", "High contrast", "Brand", "Product", "Tenant"].map((name) => <article key={name}><i/><strong>{name}</strong><span>Live preview</span></article>)}</div></>}
      {section === "Brand Studio" && <><div className="system-title"><div><p>CONTROLLED BRAND INHERITANCE</p><h2>Brand Studio</h2></div><b>{data.brands.length} tenant brands</b></div><div className="brand-picker">{BRANDS.map((name) => <button type="button" key={name} className={brand.name === name ? "active" : ""} onClick={() => setBrand({ ...brand, name })}><i>{name.slice(0,2)}</i><strong>{name}</strong></button>)}</div><section className="brand-editor"><div className="brand-mark">{brand.name.slice(0,2)}</div>{Object.entries(brand).map(([key,value]) => <label key={key}>{key.replaceAll("_"," ")}<input value={value} onChange={(e) => setBrand({ ...brand, [key]: e.target.value })}/></label>)}<button type="button" onClick={() => save("brand")}>Save brand</button></section></>}
      {section === "Templates" && <><div className="system-title"><div><p>WIREFRAME STARTERS</p><h2>Responsive templates</h2></div></div><div className="template-grid">{["Dashboard","Mobile banking","Admin portal","Identity centre","Healthcare portal","Logistics console","Commerce","Settings","Onboarding","Form wizard"].map((name) => <article key={name}><div/><strong>{name}</strong><span>Low · Medium · High fidelity</span></article>)}</div></>}
    </main>
  </div>;
}
