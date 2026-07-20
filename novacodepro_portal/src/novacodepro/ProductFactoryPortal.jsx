import React, { useEffect, useMemo, useState } from "react";

import { ROUTES } from "../platform/routes.js";
import { createNovaCodeProProductFactoryApi } from "./api/novacodeproProductFactoryApi.js";

const NAV_ITEMS = [
  { id: "overview", label: "Overview" },
  { id: "requests", label: "Requests" },
  { id: "blueprints", label: "Blueprints" },
  { id: "requirements", label: "Requirements" },
  { id: "lifecycle", label: "Lifecycle" },
  { id: "workflows", label: "Workflows" },
  { id: "releases", label: "Releases" },
  { id: "archetypes", label: "Archetypes" },
  { id: "phases", label: "Phases" },
  { id: "traceability", label: "Traceability" },
  { id: "reports", label: "Reports" },
  { id: "search", label: "Search" },
  { id: "cross-product", label: "Cross-Product" },
  { id: "migrations", label: "Migrations" },
  { id: "evidence", label: "Evidence" },
  { id: "prr", label: "PRR" },
  { id: "gates", label: "Gates" },
  { id: "improvements", label: "Improvements" },
  { id: "demo", label: "Demo Product" },
];

function parseRoute(pathname) {
  const parts = String(pathname || "").replace(/\/+$/, "").split("/").filter(Boolean);
  if (parts[0] !== "novacodepro" || parts[1] !== "product-factory") {
    return { section: "overview" };
  }
  return { section: parts[2] || "overview" };
}

function formatDate(value) {
  if (!value) return "Not updated";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString();
}

function Panel({ title, aside, children, testId }) {
  return (
    <section className="panel" data-testid={testId || undefined}>
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
  return (
    <div className={`state-banner ${state || "error"}`} role="status" aria-live="polite">
      <strong>{state === "loading" ? "Loading" : state === "degraded" ? "Degraded" : "Error"}</strong>
      <span>{error?.message || error?.code || "Request in progress."}</span>
    </div>
  );
}

function Badge({ label, value }) {
  return (
    <span className="context-chip">
      <strong>{label}</strong>
      <span>{value}</span>
    </span>
  );
}

function Toolbar({ children }) {
  return <div className="toolbar">{children}</div>;
}

function TextField({ label, value, onChange, placeholder = "" }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input value={value} onChange={onChange} placeholder={placeholder} />
    </label>
  );
}

function TextArea({ label, value, onChange, placeholder = "", rows = 4 }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <textarea value={value} onChange={onChange} placeholder={placeholder} rows={rows} />
    </label>
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <select value={value} onChange={onChange}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function kvRows(record, keys) {
  const readPath = (source, path) => {
    if (!path) return undefined;
    return String(path)
      .split(".")
      .reduce((value, segment) => (value && typeof value === "object" ? value[segment] : undefined), source);
  };
  return keys.map(([label, key]) => {
    const value = readPath(record, key);
    return [label, Array.isArray(value) ? value.join(", ") : String(value || "—")];
  });
}

function Table({ rows }) {
  if (!rows.length) return <p className="empty-state">No records yet.</p>;
  return (
    <div className="table-wrap">
      <table>
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <th>{label}</th>
              <td>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ProductFactoryPortal({ session, pathname, navigate, baseUrl = "", onLogout }) {
  const client = useMemo(() => createNovaCodeProProductFactoryApi({ baseUrl, session }), [baseUrl, session]);
  const route = useMemo(() => parseRoute(pathname), [pathname]);
  const [activeTab, setActiveTab] = useState(route.section);
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);
  const [overview, setOverview] = useState(null);
  const [inventory, setInventory] = useState(null);
  const [gaps, setGaps] = useState(null);
  const [requests, setRequests] = useState([]);
  const [blueprints, setBlueprints] = useState([]);
  const [requirements, setRequirements] = useState([]);
  const [lifecycleTemplates, setLifecycleTemplates] = useState([]);
  const [lifecycles, setLifecycles] = useState([]);
  const [workflowDefinitions, setWorkflowDefinitions] = useState([]);
  const [releases, setReleases] = useState([]);
  const [archetypes, setArchetypes] = useState([]);
  const [phases, setPhases] = useState([]);
  const [traceability, setTraceability] = useState(null);
  const [traceabilityLinks, setTraceabilityLinks] = useState([]);
  const [traceabilityCoverage, setTraceabilityCoverage] = useState(null);
  const [traceabilityGaps, setTraceabilityGaps] = useState(null);
  const [reports, setReports] = useState([]);
  const [searchResult, setSearchResult] = useState(null);
  const [crossProductGraph, setCrossProductGraph] = useState(null);
  const [migrations, setMigrations] = useState([]);
  const [prr, setPrr] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [gates, setGates] = useState([]);
  const [improvements, setImprovements] = useState([]);
  const [audit, setAudit] = useState([]);
  const [selectedRequestId, setSelectedRequestId] = useState("");
  const [selectedBlueprintId, setSelectedBlueprintId] = useState("");
  const [selectedRequirementId, setSelectedRequirementId] = useState("");
  const [selectedLifecycleId, setSelectedLifecycleId] = useState("");
  const [selectedWorkflowId, setSelectedWorkflowId] = useState("");
  const [selectedReleaseId, setSelectedReleaseId] = useState("");
  const [selectedArchetypeId, setSelectedArchetypeId] = useState("");
  const [selectedPhaseId, setSelectedPhaseId] = useState("");
  const [selectedGateId, setSelectedGateId] = useState("");
  const [selectedImprovementId, setSelectedImprovementId] = useState("");
  const [requestDraft, setRequestDraft] = useState({
    product_name: "NovaFactory Product",
    product_description: "Governed digital product factory request",
    core_business_problem: "Accelerate product delivery with traceable governance",
    target_market: "Enterprise",
    product_category: "Digital Product Factory",
    geographic_scope: "Australia",
    supported_languages: "en-AU",
    supported_currencies: "AUD",
    status: "Draft",
  });
  const [blueprintDraft, setBlueprintDraft] = useState({
    vision: "Deliver products safely and quickly.",
    mission: "Guide every product from idea to production with traceability.",
    recommended_architecture: "NovaCodePro platform + governed service layer",
    technology_profile: "React, FastAPI, SQLite/Postgres-ready",
    delivery_strategy: "Iterative delivery with approval gates",
    status: "Draft",
  });
  const [requirementDraft, setRequirementDraft] = useState({
    class: "Functional",
    title: "Trace requirement",
    statement: "The factory shall maintain governed traceability.",
    mandatory_for_ga: true,
  });
  const [lifecycleDraft, setLifecycleDraft] = useState({
    name: "Standard Product Lifecycle",
    description: "Governed end-to-end product lifecycle.",
  });
  const [workflowDraft, setWorkflowDraft] = useState({
    name: "Approval workflow",
    description: "Separated-duties approval workflow.",
  });
  const [releaseDraft, setReleaseDraft] = useState({
    name: "Product release",
  });
  const [migrationDraft, setMigrationDraft] = useState({
    source_system: "legacy-products",
    target_system: "product-factory",
    mode: "dry-run",
  });
  const [evidenceDraft, setEvidenceDraft] = useState({ title: "Evidence record", type: "artifact", result: "PASS" });
  const [gateDraft, setGateDraft] = useState({ name: "Product Gate", decision: "Deferred", role: "PRODUCT_MANAGER" });
  const [improvementDraft, setImprovementDraft] = useState({ title: "Improve factory baseline", description: "", priority: "medium" });

  useEffect(() => {
    setActiveTab(route.section);
  }, [route.section]);

  function go(tab) {
    setActiveTab(tab);
    if (typeof navigate === "function") {
      navigate(tab === "overview" ? ROUTES.productFactoryRoot : `${ROUTES.productFactoryRoot}/${tab}`);
    }
  }

  async function reload() {
    setState("loading");
    setError(null);
    try {
      const [overviewBody, inventoryBody, gapsBody, requestBody, blueprintBody, archetypeBody, phaseBody, traceBody, evidenceBody, gateBody, improvementBody, auditBody] =
        await Promise.all([
          client.getOverview(),
          client.getInventory(),
          client.getGaps(),
          client.listRequests(),
          client.listBlueprints(),
          client.listArchetypes(),
          client.listPhases(),
          client.getTraceability(),
          client.listEvidence(),
          client.listGates(),
          client.listImprovements(),
          client.listAudit(),
        ]);
      const [requirementsBody, lifecycleTemplatesBody, releasesBody, workflowDefinitionsBody, traceabilityLinksBody, coverageBody, gapsBody2, reportsBody, crossProductBody, migrationBody] =
        await Promise.all([
          client.listRequirements(),
          client.listLifecycleTemplates(),
          client.listReleases(),
          client.listWorkflowDefinitions(),
          client.listTraceabilityLinks(),
          client.getTraceabilityCoverage(),
          client.getTraceabilityGaps(),
          client.reportCatalog(),
          client.getCrossProductGraph(),
          client.listMigrations(),
        ]);
      setOverview(overviewBody);
      setInventory(inventoryBody);
      setGaps(gapsBody);
      setRequests(requestBody?.requests || []);
      setBlueprints(blueprintBody?.blueprints || []);
      setRequirements(requirementsBody?.requirements || []);
      setLifecycleTemplates(lifecycleTemplatesBody?.templates || []);
      setReleases(releasesBody?.releases || []);
      setWorkflowDefinitions(workflowDefinitionsBody?.definitions || []);
      setArchetypes(archetypeBody?.archetypes || []);
      setPhases(phaseBody?.phases || []);
      setTraceability(traceBody);
      setTraceabilityLinks(traceabilityLinksBody?.links || []);
      setTraceabilityCoverage(coverageBody);
      setTraceabilityGaps(gapsBody2);
      setReports(reportsBody?.reports || []);
      setCrossProductGraph(crossProductBody);
      setMigrations(migrationBody?.migrations || []);
      setEvidence(evidenceBody?.evidence || []);
      setGates(gateBody?.gates || []);
      setImprovements(improvementBody?.improvements || []);
      setAudit(auditBody?.audit || []);
      setSelectedRequestId((requestBody?.requests || [])[0]?.id || "");
      setSelectedBlueprintId((blueprintBody?.blueprints || [])[0]?.id || "");
      setSelectedRequirementId((requirementsBody?.requirements || [])[0]?.id || "");
      setSelectedLifecycleId((lifecycleTemplatesBody?.templates || [])[0]?.id || "");
      setSelectedWorkflowId((workflowDefinitionsBody?.definitions || [])[0]?.id || "");
      setSelectedReleaseId((releasesBody?.releases || [])[0]?.id || "");
      setSelectedArchetypeId((archetypeBody?.archetypes || [])[0]?.id || "");
      setSelectedPhaseId((phaseBody?.phases || [])[0]?.id || "");
      setSelectedGateId((gateBody?.gates || [])[0]?.id || "");
      setSelectedImprovementId((improvementBody?.improvements || [])[0]?.id || "");
      setState("ready");
    } catch (cause) {
      setError(cause);
      setState("error");
    }
  }

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  async function createRequest() {
    await client.createRequest(
      {
        ...requestDraft,
        target_users: ["Product Manager", "Architect", "Engineer"],
        supported_languages: requestDraft.supported_languages ? requestDraft.supported_languages.split(",").map((item) => item.trim()).filter(Boolean) : [],
        supported_currencies: requestDraft.supported_currencies ? requestDraft.supported_currencies.split(",").map((item) => item.trim()).filter(Boolean) : [],
      },
      client.createIdempotencyKey(),
    );
    await reload();
  }

  async function seedDemo() {
    await client.createDemoProduct();
    await reload();
  }

  async function createBlueprint() {
    if (!selectedRequestId) return;
    await client.createBlueprint(selectedRequestId, {
      ...blueprintDraft,
      capabilities: ["request intake", "blueprints", "traceability", "gates"],
      mvp_scope: ["request intake", "blueprint", "traceability"],
      future_scope: ["mobile generation", "integrations", "continuous improvement"],
    });
    await reload();
  }

  async function createRequirement() {
    if (!selectedBlueprintId) return;
    await client.createRequirement({
      ...requirementDraft,
      product_id: overview?.summary?.requests ? "product-factory" : "product-factory",
      blueprint_id: selectedBlueprintId,
      status: "Draft",
      implementation_links: [],
      test_links: [],
      evidence_links: [],
      release_links: [],
    });
    await reload();
  }

  async function createLifecycle() {
    if (!selectedRequestId) return;
    await client.createLifecycle(selectedRequestId, {
      ...lifecycleDraft,
      phases: phases.map((phase) => phase.name),
    });
    await reload();
  }

  async function createWorkflow() {
    await client.createWorkflowDefinition({
      ...workflowDraft,
      steps: ["review", "approve", "execute", "verify"],
      roles: ["PRODUCT_MANAGER", "ARCHITECT", "QA_ENGINEER"],
      approvals: ["independent approval"],
      quorum: 1,
    });
    await reload();
  }

  async function createReleaseRecord() {
    await client.createRelease({
      ...releaseDraft,
      product_id: "product-factory",
      candidate_id: selectedBlueprintId || undefined,
      blueprint_version_id: selectedBlueprintId || undefined,
      status: "Draft",
    });
    await reload();
  }

  async function createMigrationRecord() {
    await client.createMigration({
      ...migrationDraft,
      product_id: "product-factory",
      counts: { source: 1, target: 1 },
      evidence: [],
    });
    await reload();
  }

  async function approveBlueprint() {
    if (!selectedBlueprintId) return;
    await client.approveBlueprint(selectedBlueprintId, { evidence: [selectedBlueprintId] });
    await reload();
  }

  async function transitionPhase(status) {
    if (!selectedPhaseId) return;
    await client.transitionPhase(selectedPhaseId, { status, note: `Product Factory ${status.toLowerCase()}` });
    await reload();
  }

  async function createEvidence() {
    await client.createEvidence({
      ...evidenceDraft,
      request_id: selectedRequestId || undefined,
      blueprint_id: selectedBlueprintId || undefined,
      phase_id: selectedPhaseId || undefined,
      gate_id: selectedGateId || undefined,
      subject: selectedRequestId || selectedBlueprintId || selectedPhaseId || "product-factory",
      integrity_status: "VERIFIED",
      verification_status: "PASS",
      source_records: selectedRequestId ? [selectedRequestId] : [],
      timeline: [{ at: new Date().toISOString(), event: "Evidence created" }],
      manifest: { product: "novacodepro", scope: "product-factory" },
    });
    await reload();
  }

  async function createRequirementTraceLink() {
    if (!selectedRequirementId || !selectedBlueprintId) return;
    await client.createTraceabilityLink({
      source_entity_type: "requirement",
      source_entity_id: selectedRequirementId,
      target_entity_type: "blueprint",
      target_entity_id: selectedBlueprintId,
      relationship_type: "supports",
      product_id: "product-factory",
      product_version: "1",
      status: "DRAFT",
      provenance: "portal",
      confidence: "1.0",
      evidence: [selectedBlueprintId],
    });
    await reload();
  }

  async function runTraceabilityValidation() {
    await client.validateTraceability();
    await reload();
  }

  async function runReleaseEvaluation() {
    if (!selectedReleaseId) return;
    await client.evaluateRelease(selectedReleaseId);
    await reload();
  }

  async function createPrr() {
    if (!selectedReleaseId) return;
    await client.exportPrr(selectedReleaseId);
    await reload();
  }

  async function searchFactory() {
    setSearchResult(await client.searchPost({ query: requestDraft.product_name || "factory", product: "product-factory" }));
  }

  async function createGate() {
    await client.createGateDecision({
      ...gateDraft,
      phase_id: selectedPhaseId || undefined,
      linked_commit: "workspace",
      evidence: selectedBlueprintId ? [selectedBlueprintId] : [],
      conditions: ["Human approval required"],
      exceptions: [],
      rationale: "Controlled release gate",
    });
    await reload();
  }

  async function createImprovement() {
    await client.createImprovement({
      ...improvementDraft,
      linked_request_id: selectedRequestId || undefined,
      evidence: selectedBlueprintId ? [selectedBlueprintId] : [],
    });
    await reload();
  }

  const selectedRequest = requests.find((item) => item.id === selectedRequestId) || requests[0] || null;
  const selectedBlueprint = blueprints.find((item) => item.id === selectedBlueprintId) || blueprints[0] || null;
  const selectedArchetype = archetypes.find((item) => item.id === selectedArchetypeId) || archetypes[0] || null;
  const selectedPhase = phases.find((item) => item.id === selectedPhaseId) || phases[0] || null;
  const selectedGate = gates.find((item) => item.id === selectedGateId) || gates[0] || null;
  const selectedImprovement = improvements.find((item) => item.id === selectedImprovementId) || improvements[0] || null;

  return (
    <div className="solution-shell product-factory-shell">
      <header className="solution-topbar">
        <div>
          <p className="eyebrow">Governed digital product factory</p>
          <h1>NovaCodePro Product Factory</h1>
          <p className="studio-note">
            Request intake, blueprint generation, SDLC orchestration, traceability, evidence, and release governance in one workspace.
          </p>
        </div>
        <div className="solution-topbar-actions">
          <button type="button" className="toolbar-chip" onClick={seedDemo}>
            Seed demo product
          </button>
          <button type="button" className="toolbar-chip" onClick={onLogout}>
            Logout
          </button>
        </div>
      </header>

      <StateBanner state={state} error={error} />

      <nav className="solution-nav" aria-label="Product Factory sections">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={activeTab === item.id ? "solution-nav-item active" : "solution-nav-item"}
            aria-pressed={activeTab === item.id}
            onClick={() => go(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <section className="solution-summary" aria-label="Product Factory summary">
        <Badge label="Requests" value={String(overview?.summary?.requests ?? requests.length)} />
        <Badge label="Blueprints" value={String(overview?.summary?.blueprints ?? blueprints.length)} />
        <Badge label="Archetypes" value={String(overview?.summary?.archetypes ?? archetypes.length)} />
        <Badge label="Phases" value={String(overview?.summary?.phases ?? phases.length)} />
        <Badge label="Evidence" value={String(overview?.summary?.evidence_items ?? evidence.length)} />
        <Badge label="Open gaps" value={String(overview?.summary?.open_gaps ?? gaps?.matrix?.length ?? 0)} />
      </section>

      {activeTab === "overview" ? (
        <div className="solution-grid">
          <Panel title="Inventory" testId="product-factory-inventory">
            <Table rows={kvRows(inventory || {}, [["Generated", "generated_at"], ["Total capabilities", "summary.total"], ["Implemented", "summary.implemented"], ["Partial", "summary.partial"], ["Missing", "summary.missing"]])} />
          </Panel>
          <Panel title="Gap matrix">
            <div className="stack">
              {(gaps?.matrix || []).slice(0, 8).map((item) => (
                <article key={item.capability} className="card">
                  <strong>{item.capability}</strong>
                  <p>{item.upgrade_strategy}</p>
                  <p>{item.missing?.join(", ") || "No listed gaps."}</p>
                </article>
              ))}
            </div>
          </Panel>
          <Panel title="Recent activity">
            <div className="stack">
              {(overview?.operations?.latest_activity || audit || []).slice(0, 8).map((item, index) => (
                <article key={item.id || `${item.event_type || "item"}-${index}`} className="card">
                  <strong>{item.event_type || item.action || "Activity"}</strong>
                  <p>{item.detail || item.evidence || item.subject || item.name || "Recorded by the Product Factory"}</p>
                </article>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === "requests" ? (
        <div className="solution-grid">
          <Panel title="Create request" aside={<button type="button" className="toolbar-chip" onClick={createRequest}>Create</button>}>
            <div className="form-grid">
              <TextField label="Product name" value={requestDraft.product_name} onChange={(event) => setRequestDraft((current) => ({ ...current, product_name: event.target.value }))} />
              <TextField label="Product category" value={requestDraft.product_category} onChange={(event) => setRequestDraft((current) => ({ ...current, product_category: event.target.value }))} />
              <TextField label="Geography" value={requestDraft.geographic_scope} onChange={(event) => setRequestDraft((current) => ({ ...current, geographic_scope: event.target.value }))} />
              <TextField label="Languages" value={requestDraft.supported_languages} onChange={(event) => setRequestDraft((current) => ({ ...current, supported_languages: event.target.value }))} />
              <TextField label="Currencies" value={requestDraft.supported_currencies} onChange={(event) => setRequestDraft((current) => ({ ...current, supported_currencies: event.target.value }))} />
              <TextArea label="Business problem" value={requestDraft.core_business_problem} onChange={(event) => setRequestDraft((current) => ({ ...current, core_business_problem: event.target.value }))} />
            </div>
          </Panel>
          <Panel title="Requests" aside={<Badge label="Count" value={String(requests.length)} />}>
            <Select label="Selected request" value={selectedRequestId} onChange={(event) => setSelectedRequestId(event.target.value)} options={requests.map((request) => ({ value: request.id, label: request.name }))} />
            <div className="stack">
              {selectedRequest ? <Table rows={kvRows(selectedRequest, [["Name", "name"], ["Status", "status"], ["Market", "target_market"], ["Category", "product_category"], ["Reviewer", "reviewer_assignment"], ["Created", "created_at"], ["Updated", "updated_at"]])} /> : <p className="empty-state">No request selected.</p>}
            </div>
            <Toolbar>
              <button type="button" className="toolbar-chip" onClick={() => selectedRequestId && client.submitRequest(selectedRequestId, { note: "Submitted from Product Factory" }).then(reload)}>Submit</button>
              <button type="button" className="toolbar-chip" onClick={() => selectedRequestId && client.approveRequest(selectedRequestId, { note: "Approved" }).then(reload)}>Approve</button>
              <button type="button" className="toolbar-chip" onClick={() => selectedRequestId && client.rejectRequest(selectedRequestId, { note: "Needs revision" }).then(reload)}>Reject</button>
              <button type="button" className="toolbar-chip" onClick={() => selectedRequestId && client.convertRequestToProduct(selectedRequestId).then(reload)}>Convert to product</button>
              <button type="button" className="toolbar-chip" onClick={() => selectedRequestId && client.convertRequestToProject(selectedRequestId).then(reload)}>Convert to project</button>
              <button type="button" className="toolbar-chip" onClick={() => selectedRequestId && client.archiveRequest(selectedRequestId).then(reload)}>Archive</button>
            </Toolbar>
          </Panel>
        </div>
      ) : null}

      {activeTab === "blueprints" ? (
        <div className="solution-grid">
          <Panel title="Create blueprint" aside={<button type="button" className="toolbar-chip" onClick={createBlueprint}>Generate</button>}>
            <Select label="Source request" value={selectedRequestId} onChange={(event) => setSelectedRequestId(event.target.value)} options={requests.map((request) => ({ value: request.id, label: request.name }))} />
            <div className="form-grid">
              <TextField label="Vision" value={blueprintDraft.vision} onChange={(event) => setBlueprintDraft((current) => ({ ...current, vision: event.target.value }))} />
              <TextField label="Mission" value={blueprintDraft.mission} onChange={(event) => setBlueprintDraft((current) => ({ ...current, mission: event.target.value }))} />
              <TextField label="Architecture" value={blueprintDraft.recommended_architecture} onChange={(event) => setBlueprintDraft((current) => ({ ...current, recommended_architecture: event.target.value }))} />
              <TextField label="Technology profile" value={blueprintDraft.technology_profile} onChange={(event) => setBlueprintDraft((current) => ({ ...current, technology_profile: event.target.value }))} />
              <TextArea label="Delivery strategy" value={blueprintDraft.delivery_strategy} onChange={(event) => setBlueprintDraft((current) => ({ ...current, delivery_strategy: event.target.value }))} />
            </div>
          </Panel>
          <Panel title="Blueprints" aside={<Badge label="Count" value={String(blueprints.length)} />}>
            <Select label="Selected blueprint" value={selectedBlueprintId} onChange={(event) => setSelectedBlueprintId(event.target.value)} options={blueprints.map((blueprint) => ({ value: blueprint.id, label: `${blueprint.product_name} v${blueprint.version}` }))} />
            {selectedBlueprint ? <Table rows={kvRows(selectedBlueprint, [["Product", "product_name"], ["Status", "status"], ["Version", "version"], ["Request", "request_id"], ["Vision", "vision"], ["Mission", "mission"], ["Approved", "approved_at"]])} /> : null}
            <Toolbar>
              <button type="button" className="toolbar-chip" onClick={() => selectedBlueprintId && client.approveBlueprint(selectedBlueprintId, { evidence: [selectedBlueprintId] }).then(reload)}>Approve</button>
              <button type="button" className="toolbar-chip" onClick={() => selectedBlueprintId && client.amendBlueprint(selectedBlueprintId, { notes: "Controlled amendment" }).then(reload)}>Amend</button>
            </Toolbar>
          </Panel>
        </div>
      ) : null}

      {activeTab === "requirements" ? (
        <div className="solution-grid">
          <Panel title="Create requirement" aside={<button type="button" className="toolbar-chip" onClick={createRequirement}>Create</button>}>
            <div className="form-grid">
              <TextField label="Class" value={requirementDraft.class} onChange={(event) => setRequirementDraft((current) => ({ ...current, class: event.target.value }))} />
              <TextField label="Title" value={requirementDraft.title} onChange={(event) => setRequirementDraft((current) => ({ ...current, title: event.target.value }))} />
              <TextArea label="Statement" value={requirementDraft.statement} onChange={(event) => setRequirementDraft((current) => ({ ...current, statement: event.target.value }))} />
            </div>
          </Panel>
          <Panel title="Requirements" aside={<Badge label="Count" value={String(requirements.length)} />}>
            <Select label="Selected requirement" value={selectedRequirementId} onChange={(event) => setSelectedRequirementId(event.target.value)} options={requirements.map((item) => ({ value: item.id, label: item.title }))} />
            {selectedRequirement ? <Table rows={kvRows(selectedRequirement, [["Title", "title"], ["Class", "class"], ["Status", "status"], ["Statement", "statement"], ["Implementation", "implementation_links"], ["Tests", "test_links"], ["Evidence", "evidence_links"]])} /> : null}
            <Toolbar>
              <button type="button" className="toolbar-chip" onClick={createRequirementTraceLink}>Link to blueprint</button>
            </Toolbar>
          </Panel>
        </div>
      ) : null}

      {activeTab === "lifecycle" ? (
        <div className="solution-grid">
          <Panel title="Lifecycle template" aside={<button type="button" className="toolbar-chip" onClick={createLifecycle}>Create lifecycle</button>}>
            <div className="form-grid">
              <TextField label="Name" value={lifecycleDraft.name} onChange={(event) => setLifecycleDraft((current) => ({ ...current, name: event.target.value }))} />
              <TextArea label="Description" value={lifecycleDraft.description} onChange={(event) => setLifecycleDraft((current) => ({ ...current, description: event.target.value }))} />
            </div>
          </Panel>
          <Panel title="Lifecycle templates" aside={<Badge label="Count" value={String(lifecycleTemplates.length)} />}>
            <div className="stack">
              {lifecycleTemplates.map((item) => (
                <article key={item.id} className="card">
                  <strong>{item.name}</strong>
                  <p>{item.status} · {item.phases?.length || 0} phases</p>
                </article>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === "workflows" ? (
        <div className="solution-grid">
          <Panel title="Workflow definition" aside={<button type="button" className="toolbar-chip" onClick={createWorkflow}>Create</button>}>
            <div className="form-grid">
              <TextField label="Name" value={workflowDraft.name} onChange={(event) => setWorkflowDraft((current) => ({ ...current, name: event.target.value }))} />
              <TextArea label="Description" value={workflowDraft.description} onChange={(event) => setWorkflowDraft((current) => ({ ...current, description: event.target.value }))} />
            </div>
          </Panel>
          <Panel title="Workflow definitions" aside={<Badge label="Count" value={String(workflowDefinitions.length)} />}>
            <div className="stack">
              {workflowDefinitions.map((item) => (
                <article key={item.id} className="card">
                  <strong>{item.name}</strong>
                  <p>{item.status} · quorum {item.quorum}</p>
                </article>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === "releases" ? (
        <div className="solution-grid">
          <Panel title="Release" aside={<Toolbar><button type="button" className="toolbar-chip" onClick={createReleaseRecord}>Create</button><button type="button" className="toolbar-chip" onClick={runReleaseEvaluation}>Evaluate</button></Toolbar>}>
            <div className="form-grid">
              <TextField label="Name" value={releaseDraft.name} onChange={(event) => setReleaseDraft((current) => ({ ...current, name: event.target.value }))} />
            </div>
          </Panel>
          <Panel title="Releases" aside={<Badge label="Count" value={String(releases.length)} />}>
            <Select label="Selected release" value={selectedReleaseId} onChange={(event) => setSelectedReleaseId(event.target.value)} options={releases.map((item) => ({ value: item.id, label: item.name }))} />
            {selectedRelease ? <Table rows={kvRows(selectedRelease, [["Name", "name"], ["Status", "status"], ["Candidate", "candidate_id"], ["Commit", "commit_sha"], ["Decision", "decision"]])} /> : null}
          </Panel>
        </div>
      ) : null}

      {activeTab === "archetypes" ? (
        <div className="solution-grid">
          <Panel title="Archetypes" aside={<Badge label="Count" value={String(archetypes.length)} />}>
            <Select label="Selected archetype" value={selectedArchetypeId} onChange={(event) => setSelectedArchetypeId(event.target.value)} options={archetypes.map((archetype) => ({ value: archetype.id, label: archetype.name }))} />
            {selectedArchetype ? <Table rows={kvRows(selectedArchetype, [["Name", "name"], ["Status", "status"], ["Roles", "roles"], ["Capabilities", "capabilities"], ["Modules", "modules"], ["Release gates", "release_gates"]])} /> : null}
            <Toolbar>
              <button type="button" className="toolbar-chip" onClick={() => selectedArchetypeId && client.cloneArchetype(selectedArchetypeId, { name: `${selectedArchetype?.name || "Archetype"} Clone` }).then(reload)}>Clone</button>
              <button type="button" className="toolbar-chip" onClick={() => selectedArchetypeId && client.publishArchetype(selectedArchetypeId).then(reload)}>Publish</button>
              <button type="button" className="toolbar-chip" onClick={() => selectedArchetypeId && client.deprecateArchetype(selectedArchetypeId).then(reload)}>Deprecate</button>
            </Toolbar>
          </Panel>
        </div>
      ) : null}

      {activeTab === "phases" ? (
        <div className="solution-grid">
          <Panel title="Phases" aside={<Badge label="Count" value={String(phases.length)} />}>
            <Select label="Selected phase" value={selectedPhaseId} onChange={(event) => setSelectedPhaseId(event.target.value)} options={phases.map((phase) => ({ value: phase.id, label: phase.name }))} />
            {selectedPhase ? <Table rows={kvRows(selectedPhase, [["Name", "name"], ["Status", "status"], ["Gate decision", "gate_decision"], ["Readiness", "readiness_score"], ["Entry criteria", "entry_criteria"], ["Exit criteria", "exit_criteria"]])} /> : null}
            <Toolbar>
              <button type="button" className="toolbar-chip" onClick={() => transitionPhase("Ready")}>Ready</button>
              <button type="button" className="toolbar-chip" onClick={() => transitionPhase("In Progress")}>In progress</button>
              <button type="button" className="toolbar-chip" onClick={() => transitionPhase("Generated")}>Generated</button>
              <button type="button" className="toolbar-chip" onClick={() => transitionPhase("Under Review")}>Under review</button>
              <button type="button" className="toolbar-chip" onClick={() => transitionPhase("Approved")}>Approved</button>
              <button type="button" className="toolbar-chip" onClick={() => transitionPhase("Completed")}>Completed</button>
            </Toolbar>
          </Panel>
        </div>
      ) : null}

      {activeTab === "traceability" ? (
        <div className="solution-grid">
          <Panel title="Traceability matrix" aside={<Toolbar><button type="button" className="toolbar-chip" onClick={runTraceabilityValidation}>Validate</button></Toolbar>}>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Requirement</th>
                    <th>Status</th>
                    <th>Linked phase</th>
                    <th>Tests</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {(traceability?.matrix || []).map((row) => (
                    <tr key={row.requirement_id}>
                      <th>{row.requirement}</th>
                      <td>{row.status}</td>
                      <td>{row.linked_phase || "—"}</td>
                      <td>{(row.test_ids || []).length}</td>
                      <td>{(row.evidence_ids || []).length}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
          <Panel title="Coverage">
            <Table rows={kvRows(traceabilityCoverage || {}, [["Requirements", "requirements"], ["Implementation", "implementation"], ["Tests", "tests"], ["Evidence", "evidence"], ["Releases", "release"], ["Links", "links"]])} />
            <div className="stack">
              {(traceabilityGaps?.gaps || []).slice(0, 6).map((gap) => (
                <article key={gap.requirement_id} className="card">
                  <strong>{gap.requirement_id}</strong>
                  <p>{(gap.missing || []).join(", ")}</p>
                </article>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === "reports" ? (
        <Panel title="Reports catalog">
          <div className="stack">
            {reports.map((report) => (
              <article key={report.id} className="card">
                <strong>{report.name}</strong>
                <p>{report.id}</p>
              </article>
            ))}
          </div>
        </Panel>
      ) : null}

      {activeTab === "search" ? (
        <Panel title="Search factory" aside={<button type="button" className="toolbar-chip" onClick={searchFactory}>Search</button>}>
          <p className="studio-note">Search scans the current tenant scoped Product Factory records.</p>
          <Table rows={kvRows(searchResult || {}, [["Count", "count"], ["Query", "query"]])} />
        </Panel>
      ) : null}

      {activeTab === "cross-product" ? (
        <Panel title="Cross-product graph">
          <Table rows={kvRows(crossProductGraph || {}, [["Relationships", "relationships"]])} />
        </Panel>
      ) : null}

      {activeTab === "migrations" ? (
        <div className="solution-grid">
          <Panel title="Migration" aside={<button type="button" className="toolbar-chip" onClick={createMigrationRecord}>Create</button>}>
            <div className="form-grid">
              <TextField label="Source system" value={migrationDraft.source_system} onChange={(event) => setMigrationDraft((current) => ({ ...current, source_system: event.target.value }))} />
              <TextField label="Target system" value={migrationDraft.target_system} onChange={(event) => setMigrationDraft((current) => ({ ...current, target_system: event.target.value }))} />
              <TextField label="Mode" value={migrationDraft.mode} onChange={(event) => setMigrationDraft((current) => ({ ...current, mode: event.target.value }))} />
            </div>
          </Panel>
          <Panel title="Migrations" aside={<Badge label="Count" value={String(migrations.length)} />}>
            <div className="stack">
              {migrations.map((item) => (
                <article key={item.id} className="card">
                  <strong>{item.source_system} → {item.target_system}</strong>
                  <p>{item.status} · {item.mode}</p>
                </article>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === "prr" ? (
        <Panel title="Production readiness review" aside={<button type="button" className="toolbar-chip" onClick={createPrr}>Generate PRR</button>}>
          <Table rows={kvRows(prr || {}, [["Decision", "decision"], ["Release", "release_id"], ["Generated", "generated_at"]])} />
        </Panel>
      ) : null}

      {activeTab === "evidence" ? (
        <div className="solution-grid">
          <Panel title="Create evidence" aside={<button type="button" className="toolbar-chip" onClick={createEvidence}>Record</button>}>
            <div className="form-grid">
              <TextField label="Title" value={evidenceDraft.title} onChange={(event) => setEvidenceDraft((current) => ({ ...current, title: event.target.value }))} />
              <TextField label="Type" value={evidenceDraft.type} onChange={(event) => setEvidenceDraft((current) => ({ ...current, type: event.target.value }))} />
              <TextField label="Result" value={evidenceDraft.result} onChange={(event) => setEvidenceDraft((current) => ({ ...current, result: event.target.value }))} />
            </div>
          </Panel>
          <Panel title="Evidence" aside={<Badge label="Count" value={String(evidence.length)} />}>
            <div className="stack">
              {evidence.slice(0, 12).map((item) => (
                <article key={item.id} className="card">
                  <strong>{item.title}</strong>
                  <p>{item.type} · {item.result} · {formatDate(item.created_at)}</p>
                </article>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === "gates" ? (
        <div className="solution-grid">
          <Panel title="Gate decision" aside={<button type="button" className="toolbar-chip" onClick={createGate}>Record</button>}>
            <div className="form-grid">
              <TextField label="Gate name" value={gateDraft.name} onChange={(event) => setGateDraft((current) => ({ ...current, name: event.target.value }))} />
              <TextField label="Decision" value={gateDraft.decision} onChange={(event) => setGateDraft((current) => ({ ...current, decision: event.target.value }))} />
              <TextField label="Role" value={gateDraft.role} onChange={(event) => setGateDraft((current) => ({ ...current, role: event.target.value }))} />
            </div>
          </Panel>
          <Panel title="Gate records" aside={<Badge label="Count" value={String(gates.length)} />}>
            <Select label="Selected gate" value={selectedGateId} onChange={(event) => setSelectedGateId(event.target.value)} options={gates.map((gate) => ({ value: gate.id, label: gate.name }))} />
            {selectedGate ? <Table rows={kvRows(selectedGate, [["Name", "name"], ["Decision", "decision"], ["Decision maker", "decision_maker"], ["Role", "role"], ["Phase", "phase_id"], ["Linked commit", "linked_commit"]])} /> : null}
          </Panel>
        </div>
      ) : null}

      {activeTab === "improvements" ? (
        <div className="solution-grid">
          <Panel title="Improvement backlog" aside={<Badge label="Count" value={String(improvements.length)} />}>
            <div className="stack">
              {improvements.map((item) => (
                <article key={item.id} className="card">
                  <strong>{item.title}</strong>
                  <p>{item.status} · {item.priority}</p>
                </article>
              ))}
            </div>
          </Panel>
          <Panel title="Create improvement" aside={<button type="button" className="toolbar-chip" onClick={createImprovement}>Create</button>}>
            <div className="form-grid">
              <TextField label="Title" value={improvementDraft.title} onChange={(event) => setImprovementDraft((current) => ({ ...current, title: event.target.value }))} />
              <TextField label="Priority" value={improvementDraft.priority} onChange={(event) => setImprovementDraft((current) => ({ ...current, priority: event.target.value }))} />
              <TextArea label="Description" value={improvementDraft.description} onChange={(event) => setImprovementDraft((current) => ({ ...current, description: event.target.value }))} />
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === "demo" ? (
        <Panel title="Demo product" aside={<button type="button" className="toolbar-chip" onClick={seedDemo}>Generate demo</button>}>
          <p>The demo product creates a governed request and blueprint that can be used to explore the Product Factory lifecycle.</p>
          <div className="stack">
            <article className="card">
              <strong>Selected request</strong>
              <p>{selectedRequest?.name || "No request selected."}</p>
            </article>
            <article className="card">
              <strong>Selected blueprint</strong>
              <p>{selectedBlueprint?.product_name || "No blueprint selected."}</p>
            </article>
          </div>
        </Panel>
      ) : null}
    </div>
  );
}
