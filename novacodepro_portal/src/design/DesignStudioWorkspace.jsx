import React, { useEffect, useMemo, useState } from "react";

import { createNovaCodeProNcp006bApi } from "../novacodepro/api/novacodeproNcp006bApi.js";

const TABS = ["Requirements", "Research", "Flow", "Wireframe", "Mockup", "Prototype", "Components", "Code", "Preview", "Documentation"];
const DEVICES = { Desktop: [1280, 800], Laptop: [1024, 700], Tablet: [768, 900], Phone: [390, 760], Foldable: [540, 720], Watch: [220, 260], TV: [1440, 810], Vehicle: [960, 360] };
const STARTER_NODES = [
  { id: "nav", type: "Navigation", x: 38, y: 30, w: 550, h: 55, label: "NovaPay Business" },
  { id: "hero", type: "Heading", x: 62, y: 118, w: 290, h: 60, label: "Good morning, Amina" },
  { id: "balance", type: "Card", x: 62, y: 205, w: 235, h: 125, label: "Available balance\n$84,240.00" },
  { id: "approvals", type: "Card", x: 322, y: 205, w: 235, h: 125, label: "Payments awaiting approval\n6 requests" },
  { id: "activity", type: "Table", x: 62, y: 360, w: 495, h: 185, label: "Recent transactions" },
];

function clamp(value, minimum, maximum) { return Math.max(minimum, Math.min(maximum, value)); }
function errorMessage(error, fallback) { return typeof error?.message === "string" ? error.message : error?.message?.message || error?.detail?.message || fallback; }

export function DesignStudioWorkspace({ session, baseUrl = "", onNavigate }) {
  const api = useMemo(() => createNovaCodeProNcp006bApi({ baseUrl, session }), [baseUrl, session]);
  const [tab, setTab] = useState("Wireframe");
  const [device, setDevice] = useState("Desktop");
  const [zoom, setZoom] = useState(75);
  const [nodes, setNodes] = useState(STARTER_NODES);
  const [selectedId, setSelectedId] = useState("balance");
  const [saveState, setSaveState] = useState("Saved");
  const [wireframeId, setWireframeId] = useState(null);
  const [panels, setPanels] = useState({ left: true, right: true, assistant: true, bottom: true });
  const selected = nodes.find((node) => node.id === selectedId);
  const [width, height] = DEVICES[device];

  useEffect(() => {
    api.listWireframes().then((records) => {
      const latest = records.find((record) => record.metadata?.studio_document);
      if (!latest) return;
      setWireframeId(latest.id);
      setNodes(latest.regions?.length ? latest.regions : STARTER_NODES);
    }).catch(() => setSaveState("Offline — changes stay local until reconnected"));
  }, [api]);

  function updateSelected(patch) {
    setNodes((current) => current.map((node) => node.id === selectedId ? { ...node, ...patch } : node));
    setSaveState("Unsaved changes");
  }

  function addNode(type) {
    const id = `${type.toLowerCase()}-${crypto.randomUUID()}`;
    setNodes((current) => [...current, { id, type, label: `New ${type}`, x: 90 + current.length * 14, y: 100 + current.length * 12, w: 180, h: 72 }]);
    setSelectedId(id);
    setSaveState("Unsaved changes");
  }

  async function save() {
    setSaveState("Saving…");
    const payload = { name: "NovaPay Business Dashboard", title: "NovaPay Business Dashboard", artifact_type: "wireframe", creation_method: "MANUAL", regions: nodes, metadata: { studio_document: true, device, viewport: { width, height }, zoom }, change_summary: wireframeId ? "canvas updated" : "canvas created" };
    try {
      const record = wireframeId ? await api.updateWireframe(wireframeId, payload) : await api.createWireframe(payload);
      setWireframeId(record.id || wireframeId);
      setSaveState("Saved to governed workspace");
    } catch (error) {
      setSaveState(errorMessage(error, "Save failed — retry safely"));
    }
  }

  return <div className="studio-workspace" data-testid="design-studio-workspace">
    <header className="studio-toolbar">
      <button type="button" className="studio-logo" onClick={() => onNavigate("/novacodepro/dashboard")}>N</button>
      <div><strong>NovaPay Business Dashboard</strong><span>Dashboard / Overview</span></div>
      <span className={`studio-save ${saveState.startsWith("Saved") ? "saved" : ""}`} aria-live="polite">● {saveState}</span>
      <div className="studio-history"><button type="button" aria-label="Undo">↶</button><button type="button" aria-label="Redo">↷</button></div>
      <label>Device<select value={device} onChange={(event) => setDevice(event.target.value)}>{Object.keys(DEVICES).map((name) => <option key={name}>{name}</option>)}</select></label>
      <label>Zoom<input type="range" min="25" max="150" value={zoom} onChange={(event) => setZoom(Number(event.target.value))}/><output>{zoom}%</output></label>
      <div className="studio-toolbar-actions"><button type="button">Preview</button><button type="button">Present</button><button type="button">Share</button><button type="button">Review</button><button type="button">Export</button><button type="button" className="primary" onClick={save}>Save version</button></div>
    </header>
    <nav className="studio-tabs" aria-label="Design workspace tabs">{TABS.map((name) => <button key={name} type="button" className={tab === name ? "active" : ""} onClick={() => name === "Research" ? onNavigate("/novacodepro/design/research") : name === "Flow" ? onNavigate("/novacodepro/design/user-flows") : setTab(name)}>{name}</button>)}</nav>
    <aside className={`studio-layers ${panels.left ? "" : "collapsed"}`}><button type="button" className="panel-toggle" onClick={() => setPanels((p) => ({ ...p, left: !p.left }))}>{panels.left ? "‹" : "›"}</button>{panels.left && <><div className="studio-panel-title"><strong>Pages & layers</strong><button type="button">＋</button></div><label className="layer-search">⌕ <input aria-label="Search layers" placeholder="Search layers"/></label><div className="page-row">⌄ Dashboard</div>{nodes.map((node) => <button type="button" key={node.id} className={`layer-row ${selectedId === node.id ? "active" : ""}`} onClick={() => setSelectedId(node.id)}>◇ {node.label.split("\n")[0]}</button>)}<div className="layer-library"><strong>Insert</strong>{["Frame","Card","Text","Button","Input","Table"].map((type) => <button type="button" key={type} onClick={() => addNode(type)}>＋ {type}</button>)}</div></>}</aside>
    <main className="studio-canvas" aria-label="Infinite design canvas"><div className="canvas-ruler horizontal"/><div className="canvas-ruler vertical"/><div className="device-caption"><strong>{device}</strong><span>{width} × {height}</span></div><section className="device-frame" style={{ width: width * zoom / 140, minHeight: height * zoom / 140 }} aria-label={`${device} design frame`}>{nodes.map((node) => <button type="button" key={node.id} className={`canvas-node type-${node.type.toLowerCase()} ${selectedId === node.id ? "selected" : ""}`} style={{ left: node.x * zoom / 100, top: node.y * zoom / 100, width: node.w * zoom / 100, height: node.h * zoom / 100 }} onClick={() => setSelectedId(node.id)}>{node.label.split("\n").map((line) => <span key={line}>{line}</span>)}</button>)}</section><div className="canvas-tools"><button type="button">↖</button><button type="button">✋</button><button type="button">T</button><button type="button">□</button></div></main>
    <aside className={`studio-properties ${panels.right ? "" : "collapsed"}`}><button type="button" className="panel-toggle" onClick={() => setPanels((p) => ({ ...p, right: !p.right }))}>{panels.right ? "›" : "‹"}</button>{panels.right && selected && <><div className="studio-panel-title"><strong>Properties</strong><span>{selected.type}</span></div><label>Layer name<input value={selected.label} onChange={(event) => updateSelected({ label: event.target.value })}/></label><div className="property-grid"><label>X<input type="number" value={selected.x} onChange={(event) => updateSelected({ x: Number(event.target.value) })}/></label><label>Y<input type="number" value={selected.y} onChange={(event) => updateSelected({ y: Number(event.target.value) })}/></label><label>W<input type="number" value={selected.w} onChange={(event) => updateSelected({ w: clamp(Number(event.target.value), 24, width) })}/></label><label>H<input type="number" value={selected.h} onChange={(event) => updateSelected({ h: clamp(Number(event.target.value), 24, height) })}/></label></div><fieldset><legend>Layout</legend><button type="button">Auto layout</button><button type="button">Constraints</button><button type="button">Grid</button></fieldset><fieldset><legend>Accessibility metadata</legend><label>Semantic role<select><option>Region</option><option>Heading</option><option>Button</option></select></label><label>Accessible name<input defaultValue={selected.label.split("\n")[0]}/></label></fieldset></>}</aside>
    <aside className={`studio-assistant ${panels.assistant ? "" : "collapsed"}`}><header><strong>✦ Nova AI Designer</strong><button type="button" onClick={() => setPanels((p) => ({ ...p, assistant: !p.assistant }))}>×</button></header>{panels.assistant && <><div className="assistant-context"><span>Using this project</span><b>NovaPay brand · WCAG 2.2 AA · Desktop + Mobile</b></div><div className="assistant-thread"><p><b>AI</b>I can turn requirements into flows, wireframes, components, accessible copy, or implementation guidance.</p><p className="suggestion">Improve this dashboard for keyboard users and mobile breakpoints.</p></div><form onSubmit={(event) => event.preventDefault()}><textarea aria-label="Ask Nova AI Designer" placeholder="Describe what you want to design…"/><div><button type="button" aria-label="Attach reference">＋</button><button type="submit">Generate ✦</button></div></form></>}</aside>
    <footer className={`studio-activity ${panels.bottom ? "" : "collapsed"}`}><button type="button" onClick={() => setPanels((p) => ({ ...p, bottom: !p.bottom }))}>Activity</button><button type="button">Comments <b>3</b></button><button type="button">Timeline</button><button type="button">Build</button><button type="button">Review</button><span>Version {wireframeId ? "2" : "1"} · governed autosave ready</span></footer>
  </div>;
}
