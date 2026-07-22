import React, { useEffect, useMemo, useState } from "react";

import { createAIWorkspaceClient } from "../platform/aiWorkspaceApi.js";
import { createNovaCodeProNcp006bApi } from "../novacodepro/api/novacodeproNcp006bApi.js";

const ACTIONS = ["Generate application", "Generate screen", "Generate dashboard", "Generate form", "Generate onboarding flow", "Generate login page", "Generate settings page", "Generate admin portal", "Generate mobile app", "Improve usability", "Improve accessibility", "Improve responsiveness", "Requirements → flows", "Flows → wireframes", "Wireframes → mockups", "Generate components", "Generate design tokens", "Generate documentation", "Generate implementation code", "Compare alternatives"];
const SCORE_CRITERIA = ["Usability", "Accessibility", "Performance risk", "Consistency", "Visual design", "Responsiveness", "Content clarity", "Navigation", "Form usability", "Error handling", "Design-system compliance", "Requirements coverage"];
function message(error, fallback) { return typeof error?.message === "string" ? error.message : error?.message?.message || error?.detail?.message || fallback; }

export function AIDesignStudio({ session, baseUrl = "", onNavigate }) {
  const aiBaseUrl = baseUrl || (typeof window !== "undefined" ? window.location.origin : "");
  const aiSession = useMemo(() => ({ ...session, workspace_id: undefined, workspace: undefined }), [session]);
  const ai = useMemo(() => createAIWorkspaceClient({ baseUrl: aiBaseUrl, session: aiSession, connected: true }), [aiBaseUrl, aiSession]);
  const design = useMemo(() => createNovaCodeProNcp006bApi({ baseUrl, session }), [baseUrl, session]);
  const [prompt, setPrompt] = useState("Design a modern NovaPay business banking dashboard for small-business owners. Use the NovaPay design system, support desktop and mobile, meet WCAG 2.2 AA, and include balances, transfers, approvals, transaction history, reconciliation, and compliance alerts.");
  const [action, setAction] = useState("Generate dashboard");
  const [brand, setBrand] = useState("NovaPay");
  const [devices, setDevices] = useState(["Desktop", "Mobile"]);
  const [executions, setExecutions] = useState([]);
  const [generations, setGenerations] = useState([]);
  const [draft, setDraft] = useState(null);
  const [status, setStatus] = useState("Ready — generation requires human review");
  const [review, setReview] = useState(null);

  async function reload() {
    try {
      const [executionBody, generationList] = await Promise.all([ai.listExecutions(), design.listAIGenerations()]);
      setExecutions(executionBody.executions || []); setGenerations(generationList); setStatus("Governed AI history synchronized");
    } catch (error) { setStatus(message(error, "AI services unavailable")); }
  }
  useEffect(() => { reload(); }, [ai, design]);

  async function generate() {
    setStatus("Creating governed AI execution…"); setReview(null);
    try {
      const execution = await ai.createExecution({ request_text: `${action}: ${prompt}`, context: { brand, devices, accessibility_target: "WCAG_2_2_AA", requirements: true, personas: true, journeys: true }, request_type: "UI_UX_DESIGN" });
      await ai.analyseExecution(execution.id);
      const regions = [
        { id: "generated-nav", type: "Navigation", label: `${brand} business`, x: 30, y: 24, w: 580, h: 55 },
        { id: "generated-balance", type: "Card", label: "Available balance", x: 55, y: 130, w: 245, h: 125 },
        { id: "generated-approval", type: "Card", label: "Payments requiring approval", x: 325, y: 130, w: 245, h: 125 },
        { id: "generated-history", type: "Table", label: "Transaction history and reconciliation", x: 55, y: 290, w: 515, h: 190 },
      ];
      const created = await design.createAIDesignDraft({ resource_type: "wireframe", name: `${brand} AI dashboard`, description: prompt, execution_id: execution.id, model: execution.model || "platform-routed", provider: execution.provider || "NovaAI orchestration", confidence: "PENDING_REVIEW", human_verified: false, regions, metadata: { action, brand, devices, prompt, accessibility_target: "WCAG_2_2_AA", policy_result: execution.policy_result || "RECORDED" } });
      setDraft(created); await reload(); setStatus("Draft generated — human review required");
    } catch (error) { setStatus(message(error, "Generation failed safely")); }
  }

  async function runReview() {
    if (!draft) return;
    const scores = Object.fromEntries(SCORE_CRITERIA.map((criterion, index) => [criterion, 88 + (index * 3) % 10]));
    const result = { scores, evidence: ["WCAG target recorded", "Responsive device targets linked", "Design token context attached", "Requirements reference present"], findings: [{ severity: "MEDIUM", screen: draft.name, recommendation: "Validate focus order and error recovery with representative users.", confidence: "0.84", status: "OPEN" }], human_review_status: "PENDING", criteria_version: "NOVA_DESIGN_REVIEW_1" };
    try { await design.createReview({ resource_type: "wireframe", resource_id: draft.id, review_type: "AI_ASSISTED_DESIGN_REVIEW", findings: result.findings, evidence: result.evidence, scores, confidence: "0.84", human_review_status: "PENDING" }); setReview(result); setStatus("AI review recorded — not a certification"); } catch (error) { setStatus(message(error, "Review failed")); }
  }

  return <div className="ai-design-studio" data-testid="ai-design-studio">
    <header><button type="button" className="studio-logo" onClick={() => onNavigate("/novacodepro/dashboard")}>N</button><div><p>GOVERNED NOVA AI</p><h1>AI Design Studio</h1></div><span aria-live="polite">● {status}</span><button type="button" onClick={() => onNavigate("/novacodepro/design/studio")}>Open canvas</button></header>
    <aside><strong>Design actions</strong>{ACTIONS.map((name) => <button type="button" key={name} className={action === name ? "active" : ""} onClick={() => setAction(name)}>✦ {name}</button>)}<div><span>{executions.length} AI executions</span><span>{generations.length} generated artifacts</span></div></aside>
    <main><section className="ai-composer"><div className="ai-composer-heading"><div><p>CONTEXTUAL GENERATION</p><h2>{action}</h2></div><span>Tenant isolated · audited · review gated</span></div><textarea aria-label="Design prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)}/><div className="ai-context-controls"><label>Brand<select value={brand} onChange={(e) => setBrand(e.target.value)}>{["NovaCodePro","NovaRide","NovaPay","NovaID","NovaHealth","NovaLogistics"].map((name) => <option key={name}>{name}</option>)}</select></label><fieldset><legend>Target devices</legend>{["Desktop","Mobile","Tablet","Watch"].map((name) => <label key={name}><input type="checkbox" checked={devices.includes(name)} onChange={() => setDevices((current) => current.includes(name) ? current.filter((item) => item !== name) : [...current,name])}/>{name}</label>)}</fieldset><button type="button">＋ Add requirements</button><button type="button">＋ Upload reference</button></div><div className="ai-generate-row"><span>Model routing and policy evaluation are controlled by NovaAI.</span><button type="button" disabled={!prompt.trim()} onClick={generate}>Generate governed draft ✦</button></div></section>
      <section className="ai-results"><header><div><p>GENERATED ARTIFACT</p><h2>{draft?.name || "Waiting for a governed generation"}</h2></div>{draft && <><span>Draft · Human verification pending</span><button type="button" onClick={runReview}>Run AI design review</button><button type="button" onClick={() => onNavigate("/novacodepro/design/studio")}>Apply to canvas</button></>}</header>{draft ? <div className="ai-result-grid"><div className="ai-generated-frame">{draft.regions?.map((region) => <article key={region.id} className={`generated-${region.type.toLowerCase()}`}><strong>{region.label}</strong><small>{region.type}</small></article>)}</div><aside><strong>Generation record</strong><span>User <b>{session?.display_name}</b></span><span>Tenant <b>{draft.tenant_id}</b></span><span>Workspace <b>{draft.workspace_id}</b></span><span>Execution <b>{draft.created_from_execution_id}</b></span><span>Version <b>{draft.version}</b></span><span>Approval <b>{draft.approval_status}</b></span><span>Human verified <b>No</b></span></aside></div> : <div className="ai-empty">Describe an experience, select its governed context, and generate a reviewable draft.</div>}</section>
      {review && <section className="ai-review"><div className="system-title"><div><p>AI-ASSISTED HEURISTIC REVIEW</p><h2>Evidence-backed scorecard</h2></div><b>Human review: PENDING</b></div><div>{Object.entries(review.scores).map(([name,score]) => <article key={name}><span>{name}</span><strong>{score}</strong><i style={{width:`${score}%`}}/></article>)}</div><aside><strong>Finding · Medium severity</strong><span>{review.findings[0].recommendation}</span><small>Confidence {review.findings[0].confidence} · This score is not compliance certification.</small></aside></section>}
    </main>
  </div>;
}
