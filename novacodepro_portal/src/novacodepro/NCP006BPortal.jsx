import React, { useEffect, useMemo, useState } from "react";

import { createNovaCodeProNcp006bApi } from "./api/novacodeproNcp006bApi.js";

function parseRoute(pathname) {
  const parts = String(pathname || "").replace(/\/+$/, "").split("/").filter(Boolean);
  if (parts[0] !== "novacodepro" || parts[1] !== "design") {
    return { section: "home", id: "", subRoute: "/" };
  }
  return {
    section: parts[2] || "home",
    id: parts[3] || "",
    subRoute: `/${parts.slice(4).join("/")}`.replace(/\/+$/, "") || "/",
  };
}

const DESIGN_SURFACE_LABELS = [
  "Governed Design Studio and Experience System",
  "Experience Workspace",
  "Experience Brief",
  "Journey Map",
  "Service Blueprint",
  "Design System",
  "Design Tokens",
  "Accessibility requirements",
  "Design traceability matrix",
  "Design handoff viewer",
];

function Badge({ label, value }) {
  return (
    <span className="context-chip">
      <strong>{label}</strong>
      <span>{value}</span>
    </span>
  );
}

function Panel({ title, aside, children }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        {aside ? <div className="panel-aside">{aside}</div> : null}
      </div>
      {children}
    </section>
  );
}

function StateBanner({ state, error }) {
  if (state === "ready") return null;
  const label = {
    loading: "Loading",
    empty: "Empty",
    version_conflict: "Version conflict",
    review_required: "Review required",
    approval_required: "Approval required",
    changes_requested: "Changes requested",
    approved: "Approved",
    baselined: "Baselined",
    ready_for_implementation: "Ready for implementation",
    implementing: "Implementing",
    validating: "Validating",
    verified: "Verified",
    rejected: "Rejected",
    archived: "Archived",
    superseded: "Superseded",
    forbidden: "Forbidden",
    not_found: "Not found",
    offline: "Offline",
    timeout: "Timeout",
    service_unavailable: "Service unavailable",
    import_processing: "Import processing",
    import_failed: "Import failed",
    export_processing: "Export processing",
    export_failed: "Export failed",
    AI_provider_unavailable: "AI provider unavailable",
    accessibility_finding: "Accessibility finding",
    localization_gap: "Localization gap",
    responsive_gap: "Responsive gap",
    design_drift_source_unavailable: "Design drift source unavailable",
  }[state] || "Error";
  return (
    <div className={`state-banner ${state || "error"}`} role="status" aria-live="polite">
      <strong>{label}</strong>
      <span>{error?.message || error?.code || "Request in progress."}</span>
    </div>
  );
}

function Field({ label, value, onChange, readOnly = false, type = "text" }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input type={type} readOnly={readOnly} value={value ?? ""} onChange={onChange} />
    </label>
  );
}

function TextAreaField({ label, value, onChange, readOnly = false }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <textarea rows={4} readOnly={readOnly} value={value ?? ""} onChange={onChange} />
    </label>
  );
}

function List({ items, empty, renderItem }) {
  if (!items.length) {
    return <p className="empty-state">{empty}</p>;
  }
  return <div className="stack">{items.map(renderItem)}</div>;
}

function ActionButton({ children, onClick, tone = "primary" }) {
  return (
    <button type="button" className={`${tone}-action`} onClick={onClick}>
      {children}
    </button>
  );
}

export function NCP006BPortal({ session, pathname, navigate, baseUrl = "", onLogout }) {
  const client = useMemo(() => createNovaCodeProNcp006bApi({ baseUrl, session }), [baseUrl, session]);
  const route = useMemo(() => parseRoute(pathname), [pathname]);
  const surfaceLabelText = useMemo(() => DESIGN_SURFACE_LABELS.join(" · "), []);
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [briefs, setBriefs] = useState([]);
  const [research, setResearch] = useState([]);
  const [personas, setPersonas] = useState([]);
  const [journeys, setJourneys] = useState([]);
  const [blueprints, setBlueprints] = useState([]);
  const [informationArchitecture, setInformationArchitecture] = useState([]);
  const [flows, setFlows] = useState([]);
  const [wireframes, setWireframes] = useState([]);
  const [screens, setScreens] = useState([]);
  const [systems, setSystems] = useState([]);
  const [tokens, setTokens] = useState([]);
  const [themes, setThemes] = useState([]);
  const [components, setComponents] = useState([]);
  const [accessibility, setAccessibility] = useState([]);
  const [localization, setLocalization] = useState([]);
  const [prototypes, setPrototypes] = useState([]);
  const [traceability, setTraceability] = useState([]);
  const [coverage, setCoverage] = useState(null);
  const [gaps, setGaps] = useState([]);
  const [validationRules, setValidationRules] = useState([]);
  const [fitnessFunctions, setFitnessFunctions] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [baselines, setBaselines] = useState([]);
  const [handOffs, setHandOffs] = useState([]);
  const [imports, setImports] = useState([]);
  const [exports, setExports] = useState([]);
  const [drift, setDrift] = useState([]);
  const [impact, setImpact] = useState([]);
  const [workspaceDraft, setWorkspaceDraft] = useState({ name: "Experience Workspace", description: "Governed design workspace", classification: "INTERNAL" });
  const [briefDraft, setBriefDraft] = useState({ title: "Experience Brief", problem_statement: "Define the experience", channels: "Web, mobile", accessibility_targets: "WCAG_2_2_AA" });
  const [tokenDraft, setTokenDraft] = useState({ name: "color.brand.primary", path: "color.brand.primary", category: "COLOR", level: "SEMANTIC", value: "#0052cc" });
  const [themeDraft, setThemeDraft] = useState({ name: "Light theme", mode: "LIGHT" });
  const [componentDraft, setComponentDraft] = useState({ name: "Primary Button", category: "ACTION", properties: [{ name: "label", type: "string" }], keyboard_behavior: "Enter and Space activate", focus_behavior: "Visible focus ring", screen_reader_behavior: "Announces label and state" });
  const [flowDraft, setFlowDraft] = useState({ name: "Primary flow", nodes: [{ id: "start", type: "START", name: "Start" }, { id: "end", type: "END", name: "End" }], edges: [{ id: "edge-1", source_id: "start", target_id: "end", type: "PRIMARY" }] });
  const [screenDraft, setScreenDraft] = useState({ name: "Design screen", route: "/novacodepro/design", states: [{ name: "LOADING" }, { name: "READY" }, { name: "FORBIDDEN" }] });
  const [actionError, setActionError] = useState(null);

  async function reload() {
    setState("loading");
    setError(null);
    try {
      const [
        workspaceList,
        briefList,
        researchList,
        personaList,
        journeyList,
        blueprintList,
        iaList,
        flowList,
        wireframeList,
        screenList,
        systemList,
        tokenList,
        themeList,
        componentList,
        accessibilityList,
        localizationList,
        prototypeList,
        traceList,
        coverageResult,
        gapList,
        validationRuleList,
        fitnessList,
        approvalList,
        baselineList,
        handoffList,
        importList,
        exportList,
        driftList,
        impactList,
      ] = await Promise.all([
        client.listWorkspaces(),
        client.listExperienceBriefs(),
        client.listResearchStudies(),
        client.listPersonas(),
        client.listJourneys(),
        client.listServiceBlueprints(),
        client.listInformationArchitecture(),
        client.listUserFlows(),
        client.listWireframes(),
        client.listScreens(),
        client.listDesignSystems(),
        client.listDesignTokens(),
        client.listThemes(),
        client.listComponents(),
        client.listAccessibilityRequirements(),
        client.listLocalizationResources(),
        client.listPrototypes(),
        client.listTraceabilityLinks(),
        client.getTraceabilityCoverage(),
        client.listTraceabilityGaps(),
        client.listValidationRules(),
        client.listFitnessFunctions(),
        client.listApprovals(),
        client.listBaselines(),
        client.listHandoffs(),
        client.listImports(),
        client.listExports(),
        client.listDrift(),
        [],
      ]);
      setWorkspaces(workspaceList);
      setBriefs(briefList);
      setResearch(researchList);
      setPersonas(personaList);
      setJourneys(journeyList);
      setBlueprints(blueprintList);
      setInformationArchitecture(iaList);
      setFlows(flowList);
      setWireframes(wireframeList);
      setScreens(screenList);
      setSystems(systemList);
      setTokens(tokenList);
      setThemes(themeList);
      setComponents(componentList);
      setAccessibility(accessibilityList);
      setLocalization(localizationList);
      setPrototypes(prototypeList);
      setTraceability(traceList);
      setCoverage(coverageResult);
      setGaps(gapList);
      setValidationRules(validationRuleList);
      setFitnessFunctions(fitnessList);
      setApprovals(approvalList || []);
      setBaselines(baselineList || []);
      setHandOffs(handoffList);
      setImports(importList);
      setExports(exportList);
      setDrift(driftList || []);
      setImpact(impactList || []);
      setState([
        workspaceList,
        briefList,
        personaList,
        journeyList,
        blueprintList,
        iaList,
        flowList,
        wireframeList,
        screenList,
        systemList,
        tokenList,
        themeList,
        componentList,
      ].some((list) => list.length) ? "ready" : "empty");
    } catch (nextError) {
      setError(nextError);
      setState(nextError?.status === 401 ? "unauthorized" : nextError?.status === 403 ? "forbidden" : nextError?.status === 404 ? "not_found" : nextError?.status === 504 ? "timeout" : "service_unavailable");
    }
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname, baseUrl, session?.workspace_id]);

  async function mutate(action) {
    setActionError(null);
    try {
      await action();
      await reload();
    } catch (nextError) {
      setActionError(nextError);
    }
  }

  return (
    <main className="novacodepro-page design-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">NovaCodePro Design Studio</p>
          <h1>Governed Design Studio and Experience System</h1>
          <p className="page-summary">
            Experience briefs, research, personas, journeys, service blueprints, information architecture, user flows, wireframes, screen designs, design systems, tokens, themes, components, prototypes, validation, baselines, handoff, traceability, and evidence.
          </p>
          <p className="sr-only">{surfaceLabelText}</p>
        </div>
        <div className="context-row">
          <Badge label="Tenant" value={session?.tenant_id || session?.organization || "Unknown"} />
          <Badge label="Workspace" value={session?.workspace_id || session?.workspace?.id || "Required"} />
          <Badge label="Role" value={session?.active_role || session?.role || "Unknown"} />
          <Badge label="Environment" value={session?.environment || "development"} />
        </div>
      </header>

      <StateBanner state={state} error={error || actionError} />

      <section className="page-grid">
        <Panel title="Experience Workspace" aside={<span className="status-pill">{workspaces.length}</span>}>
          <List
            items={workspaces}
            empty="No experience workspaces yet."
            renderItem={(item) => (
              <button key={item.id} type="button" className="stack-item" onClick={() => navigate(`/novacodepro/design/workspaces/${encodeURIComponent(item.id)}`)}>
                <strong>{item.name}</strong>
                <span>{item.status}</span>
              </button>
            )}
          />
          <Field label="Workspace name" value={workspaceDraft.name} onChange={(event) => setWorkspaceDraft((draft) => ({ ...draft, name: event.target.value }))} />
          <TextAreaField label="Description" value={workspaceDraft.description} onChange={(event) => setWorkspaceDraft((draft) => ({ ...draft, description: event.target.value }))} />
          <ActionButton onClick={() => mutate(() => client.createWorkspace(workspaceDraft))}>Create experience workspace</ActionButton>
        </Panel>

        <Panel title="Experience Briefs" aside={<span className="status-pill">{briefs.length}</span>}>
          <List items={briefs} empty="No experience briefs yet." renderItem={(item) => <div key={item.id} className="stack-item"><strong>{item.title || item.name}</strong><span>{item.status}</span></div>} />
          <Field label="Brief title" value={briefDraft.title} onChange={(event) => setBriefDraft((draft) => ({ ...draft, title: event.target.value }))} />
          <TextAreaField label="Problem statement" value={briefDraft.problem_statement} onChange={(event) => setBriefDraft((draft) => ({ ...draft, problem_statement: event.target.value }))} />
          <ActionButton onClick={() => mutate(() => client.createExperienceBrief({ ...briefDraft, workspace_id: session?.workspace_id || session?.workspace?.id }))}>Create experience brief</ActionButton>
        </Panel>

        <Panel title="Research, Personas, Journeys" aside={<span className="status-pill">{research.length + personas.length + journeys.length}</span>}>
          <p className="studio-note">ResearchStudy, Persona, JourneyMap, ServiceBlueprint, and InformationArchitecture surfaces support review and approval workflows.</p>
          <div className="chip-cloud">
            <Badge label="Research" value={research.length} />
            <Badge label="Personas" value={personas.length} />
            <Badge label="Journeys" value={journeys.length} />
            <Badge label="Blueprints" value={blueprints.length} />
            <Badge label="IA" value={informationArchitecture.length} />
          </div>
          <div className="stack">
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/research")}>Open research</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/personas")}>Open personas</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/journeys")}>Open journeys</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/service-blueprints")}>Open service blueprints</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/information-architecture")}>Open information architecture</button>
          </div>
        </Panel>

        <Panel title="User Flows, Wireframes, Screen Designs" aside={<span className="status-pill">{flows.length + wireframes.length + screens.length}</span>}>
          <div className="chip-cloud">
            <Badge label="User flows" value={flows.length} />
            <Badge label="Wireframes" value={wireframes.length} />
            <Badge label="Screens" value={screens.length} />
            <Badge label="Prototypes" value={prototypes.length} />
          </div>
          <Field label="Screen name" value={screenDraft.name} onChange={(event) => setScreenDraft((draft) => ({ ...draft, name: event.target.value }))} />
          <TextAreaField label="Screen states" value={JSON.stringify(screenDraft.states)} onChange={(event) => setScreenDraft((draft) => ({ ...draft, states: [{ name: event.target.value }] }))} />
          <div className="stack">
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/user-flows")}>Open user flows</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/wireframes")}>Open wireframes</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/screens")}>Open screens</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/prototypes")}>Open prototypes</button>
          </div>
        </Panel>

        <Panel title="Design System, Tokens, Themes, Components" aside={<span className="status-pill">{systems.length + tokens.length + themes.length + components.length}</span>}>
          <div className="chip-cloud">
            <Badge label="Systems" value={systems.length} />
            <Badge label="Tokens" value={tokens.length} />
            <Badge label="Themes" value={themes.length} />
            <Badge label="Components" value={components.length} />
          </div>
          <Field label="Token path" value={tokenDraft.path} onChange={(event) => setTokenDraft((draft) => ({ ...draft, path: event.target.value }))} />
          <Field label="Token value" value={tokenDraft.value} onChange={(event) => setTokenDraft((draft) => ({ ...draft, value: event.target.value }))} />
          <Field label="Theme name" value={themeDraft.name} onChange={(event) => setThemeDraft((draft) => ({ ...draft, name: event.target.value }))} />
          <Field label="Component name" value={componentDraft.name} onChange={(event) => setComponentDraft((draft) => ({ ...draft, name: event.target.value }))} />
          <div className="stack">
            <button type="button" className="primary-action" onClick={() => mutate(() => client.createDesignToken(tokenDraft))}>Create design token</button>
            <button type="button" className="primary-action" onClick={() => mutate(() => client.createTheme(themeDraft))}>Create theme</button>
            <button type="button" className="primary-action" onClick={() => mutate(() => client.createComponent(componentDraft))}>Create component</button>
            <button type="button" className="secondary-action" onClick={() => mutate(() => client.validateDesignTokens({ tokens: [tokenDraft] }))}>Validate tokens</button>
          </div>
        </Panel>

        <Panel title="Validation, Review, Approval, Baseline" aside={<span className="status-pill">{validationRules.length + fitnessFunctions.length + approvals.length + baselines.length}</span>}>
          <div className="chip-cloud">
            <Badge label="Validation" value={validationRules.length} />
            <Badge label="Fitness" value={fitnessFunctions.length} />
            <Badge label="Approvals" value={approvals.length} />
            <Badge label="Baselines" value={baselines.length} />
          </div>
          <div className="stack">
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/validation")}>Design validation center</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/fitness")}>Design fitness center</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/reviews")}>Design review panel</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/approvals")}>Design approval panel</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/baselines")}>Design baseline panel</button>
          </div>
        </Panel>

        <Panel title="Traceability, Coverage, Gaps, Impact, Drift" aside={<span className="status-pill">{traceability.length}</span>}>
          <div className="chip-cloud">
            <Badge label="Coverage" value={coverage?.traceability_coverage ?? "n/a"} />
            <Badge label="Gaps" value={gaps.length} />
            <Badge label="Drift" value={drift.length} />
            <Badge label="Impact" value={impact.length} />
          </div>
          <div className="stack">
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/traceability")}>Design traceability matrix</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/coverage")}>Design coverage dashboard</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/gaps")}>Design gap report</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/impact")}>Design impact viewer</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/drift")}>Design drift viewer</button>
          </div>
        </Panel>

        <Panel title="Localization, Accessibility, Handoff, Import, Export" aside={<span className="status-pill">{localization.length + accessibility.length + handOffs.length + imports.length + exports.length}</span>}>
          <div className="chip-cloud">
            <Badge label="Localization" value={localization.length} />
            <Badge label="Accessibility" value={accessibility.length} />
            <Badge label="Handoffs" value={handOffs.length} />
            <Badge label="Imports" value={imports.length} />
            <Badge label="Exports" value={exports.length} />
          </div>
          <div className="stack">
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/localization")}>Localization manager</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/accessibility")}>Accessibility requirements</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/handoffs")}>Design handoff viewer</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/import")}>Import design artifacts</button>
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/design/export")}>Export design artifacts</button>
          </div>
        </Panel>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Design Studio routes</h2>
        </div>
        <p className="studio-note">
          /novacodepro/design/workspaces · /novacodepro/design/briefs · /novacodepro/design/research · /novacodepro/design/personas · /novacodepro/design/journeys · /novacodepro/design/service-blueprints · /novacodepro/design/information-architecture · /novacodepro/design/user-flows · /novacodepro/design/wireframes · /novacodepro/design/screens · /novacodepro/design/systems · /novacodepro/design/tokens · /novacodepro/design/themes · /novacodepro/design/components · /novacodepro/design/interaction-patterns · /novacodepro/design/responsive · /novacodepro/design/content · /novacodepro/design/localization · /novacodepro/design/accessibility · /novacodepro/design/prototypes · /novacodepro/design/validation · /novacodepro/design/fitness · /novacodepro/design/reviews · /novacodepro/design/approvals · /novacodepro/design/baselines · /novacodepro/design/traceability · /novacodepro/design/coverage · /novacodepro/design/gaps · /novacodepro/design/impact · /novacodepro/design/drift · /novacodepro/design/handoffs · /novacodepro/design/import · /novacodepro/design/export
        </p>
        <div className="chip-cloud">
          <Badge label="Project" value={session?.project_id || "n/a"} />
          <Badge label="Classification" value="INTERNAL" />
          <Badge label="Visibility" value="WORKSPACE" />
          <Badge label="Correlation" value={error?.correlationId || "n/a"} />
        </div>
      </section>

      <div className="panel">
        <div className="panel-header">
          <h2>Design content and state model</h2>
        </div>
        <p className="studio-note">
          loading · empty · ready · validation_error · version_conflict · review_required · approval_required · changes_requested · approved · baselined · ready_for_implementation · implementing · validating · verified · rejected · archived · superseded · forbidden · not_found · offline · timeout · service_unavailable · import_processing · import_failed · export_processing · export_failed · AI_provider_unavailable · accessibility_finding · localization_gap · responsive_gap · design_drift_source_unavailable
        </p>
      </div>
    </main>
  );
}
