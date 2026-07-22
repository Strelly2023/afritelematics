import React, { useEffect, useMemo, useState } from "react";

import { createNovaCodeProNcp006bApi } from "../novacodepro/api/novacodeproNcp006bApi.js";

const SECTIONS = ["Research", "Personas", "Journeys", "Flows"];
const JOURNEY_STAGES = ["Discover", "Evaluate", "Register", "Authenticate", "Verify identity", "Configure", "Perform task", "Confirm", "Receive support", "Return"];
const FLOW_TYPES = ["START", "SCREEN", "USER_ACTION", "DECISION", "VALIDATION", "API_CALL", "AUTHENTICATION", "AUTHORIZATION", "EXTERNAL_SERVICE", "ERROR", "RETRY", "NOTIFICATION", "BACKGROUND_PROCESS", "END"];
const SINGULAR = { Research: "Research", Personas: "Persona", Journeys: "Journey", Flows: "Flow" };
const initialDrafts = {
  Research: { name: "Small-business banking discovery", research_questions: "How do owners review cash flow and approve payments?", market_observations: "Mobile-first operations with desktop reconciliation.", evidence_references: "" },
  Personas: { name: "Amina — Business owner", role: "Owner and payment approver", region: "East Africa", language: "English, Swahili", goals: "Understand cash position; approve urgent payments", frustrations: "Fragmented balances and unclear trust signals", accessibility_needs: "Plain language; large touch targets", device_preferences: "Mobile and laptop" },
  Journeys: { name: "Approve a supplier payment", persona: "Amina — Business owner", goal: "Safely review and approve a payment" },
  Flows: { name: "Payment approval flow", description: "Login → MFA → Dashboard → Payment → Review → Approval → Confirmation" },
};

function Field({ label, value, onChange, area = false }) {
  const Element = area ? "textarea" : "input";
  return <label className="mapping-field"><span>{label}</span><Element value={value || ""} onChange={(event) => onChange(event.target.value)}/></label>;
}

export function ExperienceMappingStudio({ session, baseUrl = "", initialSection = "Research", onNavigate }) {
  const api = useMemo(() => createNovaCodeProNcp006bApi({ baseUrl, session }), [baseUrl, session]);
  const [section, setSection] = useState(SECTIONS.includes(initialSection) ? initialSection : "Research");
  const [records, setRecords] = useState({ Research: [], Personas: [], Journeys: [], Flows: [] });
  const [drafts, setDrafts] = useState(initialDrafts);
  const [selected, setSelected] = useState(null);
  const [status, setStatus] = useState("Loading governed experience data…");

  async function reload() {
    try {
      const [research, personas, journeys, flows] = await Promise.all([api.listResearchStudies(), api.listPersonas(), api.listJourneys(), api.listUserFlows()]);
      setRecords({ Research: research, Personas: personas, Journeys: journeys, Flows: flows });
      setSelected((current) => current || research[0] || null);
      setStatus("All changes are tenant-scoped and versioned");
    } catch (error) { setStatus(error?.message || "Experience services unavailable"); }
  }
  useEffect(() => { reload(); }, [api]);
  useEffect(() => { setSection(SECTIONS.includes(initialSection) ? initialSection : "Research"); }, [initialSection]);

  function setDraft(name, value) { setDrafts((current) => ({ ...current, [section]: { ...current[section], [name]: value } })); }
  async function createRecord() {
    setStatus("Saving…");
    const draft = drafts[section];
    try {
      let record;
      if (section === "Research") record = await api.createResearchStudy({ ...draft, status: "ACTIVE", confidence: "MEDIUM", findings: [], opportunities: [], recommendations: [] });
      if (section === "Personas") record = await api.createPersona({ ...draft, type: "PRIMARY", motivations: ["Confidence and control"], behaviours: ["Reviews payments between customer tasks"], trust_concerns: ["Fraud and mistaken approval"], linked_requirements: [], evidence_references: [] });
      if (section === "Journeys") record = await api.createJourney({ ...draft, stages: JOURNEY_STAGES.map((name, index) => ({ id: `stage-${index + 1}`, name, order: index + 1, user_action: "", goal: "", emotion: "NEUTRAL", pain_point: "", touchpoint: "", risk: "", opportunity: "", owner: "" })) });
      if (section === "Flows") record = await api.createUserFlow({ ...draft, nodes: [{ id: "start", type: "START", name: "Start", x: 40, y: 120 }, { id: "screen", type: "SCREEN", name: "Dashboard", x: 240, y: 120 }, { id: "end", type: "END", name: "Complete", x: 440, y: 120 }], edges: [{ id: "edge-1", source_id: "start", target_id: "screen", type: "SUCCESS" }, { id: "edge-2", source_id: "screen", target_id: "end", type: "SUCCESS" }] });
      setSelected(record);
      await reload();
      setStatus(`${SINGULAR[section]} saved with audit evidence`);
    } catch (error) { setStatus(error?.message || "Save failed"); }
  }

  async function addJourneyStage() {
    if (!selected?.id) return;
    const stage = { name: `Stage ${(selected.stages?.length || 0) + 1}`, order: (selected.stages?.length || 0) + 1, user_action: "Describe the user action", goal: "Complete this step", emotion: "NEUTRAL", evidence: [], requirement_references: [] };
    try { await api.addJourneyStage(selected.id, stage); await reload(); setStatus("Journey stage saved"); } catch (error) { setStatus(error?.message || "Stage save failed"); }
  }

  async function addFlowNode(type) {
    if (!selected?.id) return;
    const count = selected.nodes?.length || 0;
    try { await api.addFlowNode(selected.id, { id: `node-${crypto.randomUUID()}`, type, name: type.replaceAll("_", " "), x: 80 + count * 35, y: 100 + (count % 3) * 90 }); await reload(); setStatus(`${type.replaceAll("_", " ")} node saved`); } catch (error) { setStatus(error?.message || "Node save failed"); }
  }

  const list = records[section];
  const draft = drafts[section];
  return <div className="mapping-studio" data-testid="experience-mapping-studio">
    <header className="mapping-header"><button type="button" className="studio-logo" onClick={() => onNavigate("/novacodepro/dashboard")}>N</button><div><p>EXPERIENCE INTELLIGENCE</p><h1>Research & experience mapping</h1></div><span aria-live="polite">● {status}</span><button type="button" onClick={() => onNavigate("/novacodepro/design/studio")}>Open design canvas</button></header>
    <nav aria-label="Experience mapping navigation">{SECTIONS.map((name) => <button type="button" className={section === name ? "active" : ""} key={name} onClick={() => { setSection(name); setSelected(records[name][0] || null); }}>{name}</button>)}</nav>
    <aside className="mapping-records"><div><strong>{section}</strong><span>{list.length} records</span></div>{list.map((record) => <button type="button" key={record.id} className={selected?.id === record.id ? "active" : ""} onClick={() => setSelected(record)}><strong>{record.name || record.title}</strong><span>{record.status} · v{record.version || 1}</span></button>)}{!list.length && <p>No {section.toLowerCase()} yet. Create the first governed record.</p>}</aside>
    <main className="mapping-main">
      <section className="mapping-editor"><header><div><p>NEW {SINGULAR[section].toUpperCase()}</p><h2>{draft.name}</h2></div><button type="button" onClick={createRecord}>Save {SINGULAR[section]}</button></header>
        {section === "Research" && <div className="mapping-form"><Field label="Research brief" value={draft.name} onChange={(v) => setDraft("name", v)}/><Field area label="Research questions" value={draft.research_questions} onChange={(v) => setDraft("research_questions", v)}/><Field area label="Market observations" value={draft.market_observations} onChange={(v) => setDraft("market_observations", v)}/><Field label="Evidence references" value={draft.evidence_references} onChange={(v) => setDraft("evidence_references", v)}/><div className="insight-preview"><strong>Summary structure</strong>{["Competitor strengths", "Competitor weaknesses", "User pain points", "Opportunity areas", "Design implications", "Confidence & evidence"].map((item) => <span key={item}>✓ {item}</span>)}</div></div>}
        {section === "Personas" && <div className="mapping-form persona-form">{Object.entries(draft).map(([key, value]) => <Field key={key} area={["goals","frustrations","accessibility_needs"].includes(key)} label={key.replaceAll("_", " ")} value={value} onChange={(v) => setDraft(key, v)}/>)}</div>}
        {section === "Journeys" && <><div className="mapping-form"><Field label="Journey name" value={draft.name} onChange={(v) => setDraft("name", v)}/><Field label="Persona" value={draft.persona} onChange={(v) => setDraft("persona", v)}/><Field label="Journey goal" value={draft.goal} onChange={(v) => setDraft("goal", v)}/></div><div className="journey-board" aria-label="Journey map">{(selected?.stages || JOURNEY_STAGES.map((name) => ({ name }))).map((stage, index) => <article key={stage.id || stage.name}><small>{index + 1}</small><strong>{stage.name}</strong><span>{stage.user_action || "User action"}</span><span>Emotion: {stage.emotion || "Neutral"}</span><em>{stage.opportunity || "Add opportunity"}</em></article>)}</div><button type="button" className="mapping-add" disabled={!selected?.id} onClick={addJourneyStage}>＋ Add journey stage</button></>}
        {section === "Flows" && <><div className="mapping-form"><Field label="Flow name" value={draft.name} onChange={(v) => setDraft("name", v)}/><Field area label="Description" value={draft.description} onChange={(v) => setDraft("description", v)}/></div><div className="flow-palette">{FLOW_TYPES.map((type) => <button type="button" key={type} disabled={!selected?.id} onClick={() => addFlowNode(type)}>{type.replaceAll("_", " ")}</button>)}</div><div className="flow-board" aria-label="User flow canvas">{(selected?.nodes || []).map((node, index) => <React.Fragment key={node.id}><article className={`flow-${node.type?.toLowerCase()}`}><small>{node.type}</small><strong>{node.name}</strong></article>{index < selected.nodes.length - 1 && <i>→</i>}</React.Fragment>)}{!selected?.nodes?.length && <p>Save a flow to begin connecting success and failure paths.</p>}</div></>}
      </section>
      <aside className="mapping-evidence"><strong>Traceability</strong><span>Tenant <b>{session?.tenant_id || "required"}</b></span><span>Workspace <b>{session?.workspace_id || "selected"}</b></span><span>Linked requirements <b>{selected?.linked_requirements?.length || 0}</b></span><span>Evidence references <b>{selected?.evidence_references?.length || 0}</b></span><span>Review status <b>{selected?.review_status || "DRAFT"}</b></span><span>Approval status <b>{selected?.approval_status || "DRAFT"}</b></span></aside>
    </main>
  </div>;
}
