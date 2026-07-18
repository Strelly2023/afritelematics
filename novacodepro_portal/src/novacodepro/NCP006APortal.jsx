import { useEffect, useMemo, useState } from "react";

import { createNovaCodeProNcp006aApi } from "./api/novacodeproNcp006aApi.js";

function parseRoute(pathname) {
  const parts = String(pathname || "").replace(/\/+$/, "").split("/").filter(Boolean);
  if (parts[0] !== "novacodepro") {
    return { section: "architecture", id: null, subRoute: "/" };
  }
  return {
    section: parts[2] || "home",
    id: parts[3] || null,
    subRoute: `/${parts.slice(4).join("/")}`.replace(/\/+$/, "") || "/",
  };
}

function StateBanner({ state, error }) {
  if (state === "ready") return null;
  const label =
    state === "loading"
      ? "Loading"
      : state === "empty"
        ? "Empty"
        : state === "unauthorized"
          ? "Unauthorized"
          : state === "forbidden"
            ? "Forbidden"
            : state === "not_found"
              ? "Not found"
              : state === "offline"
                ? "Offline"
                : state === "timeout"
                  ? "Timeout"
                  : state === "service_unavailable"
                    ? "Service unavailable"
                    : "Error";
  return (
    <div className={`state-banner ${state || "error"}`} role="status" aria-live="polite">
      <strong>{label}</strong>
      <span>{error?.message || error?.code || "Request in progress."}</span>
    </div>
  );
}

function Panel({ title, children, aside }) {
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

function List({ items, empty, renderItem }) {
  if (!items.length) {
    return <p className="empty-state">{empty}</p>;
  }
  return <div className="stack">{items.map(renderItem)}</div>;
}

function Chip({ label, value }) {
  return (
    <span className="context-chip">
      <strong>{label}</strong>
      <span>{value}</span>
    </span>
  );
}

function Field({ label, value, readOnly = true, onChange, type = "text" }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input type={type} readOnly={readOnly} value={value ?? ""} onChange={onChange} />
    </label>
  );
}

function TextAreaField({ label, value, readOnly = true, onChange }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <textarea readOnly={readOnly} value={value ?? ""} onChange={onChange} rows={4} />
    </label>
  );
}

export function NCP006APortal({ session, pathname, navigate, baseUrl = "", onLogout }) {
  const client = useMemo(() => createNovaCodeProNcp006aApi({ baseUrl }), [baseUrl]);
  const route = useMemo(() => parseRoute(pathname), [pathname]);
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [models, setModels] = useState([]);
  const [components, setComponents] = useState([]);
  const [interfaces, setInterfaces] = useState([]);
  const [dataModels, setDataModels] = useState([]);
  const [securityModels, setSecurityModels] = useState([]);
  const [deployments, setDeployments] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [baselines, setBaselines] = useState([]);
  const [validations, setValidations] = useState([]);
  const [fitness, setFitness] = useState([]);
  const [diagrams, setDiagrams] = useState([]);
  const [impacts, setImpacts] = useState([]);
  const [traceabilityLinks, setTraceabilityLinks] = useState([]);
  const [traceabilityCoverage, setTraceabilityCoverage] = useState(null);
  const [activeModelId, setActiveModelId] = useState(route.id || session?.architecture_model_id || "");
  const [workspaceDraft, setWorkspaceDraft] = useState({ name: "Architecture Workspace", description: "", domain: "ENTERPRISE" });
  const [modelDraft, setModelDraft] = useState({ name: "Solution Architecture", description: "", domain: "SOLUTION", technology_standard: "OpenAPI", workspace_id: session?.workspace_id || "", requirement_ids: [] });
  const [componentDraft, setComponentDraft] = useState({ name: "API Gateway", component_type: "GATEWAY", model_id: "", technology: "Nginx", description: "" });
  const [validationType, setValidationType] = useState("POLICY");
  const [diagramType, setDiagramType] = useState("SYSTEM_CONTEXT");
  const [diagramFormat, setDiagramFormat] = useState("JSON");
  const [baselineName, setBaselineName] = useState("Baseline 1");
  const [actionError, setActionError] = useState(null);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState(session?.workspace_id || "");

  async function reload(modelId = activeModelId) {
    setState("loading");
    setError(null);
    try {
      const [workspaceList, modelList] = await Promise.all([client.listWorkspaces(), client.listModels(session?.workspace_id || undefined)]);
      setWorkspaces(workspaceList);
      setModels(modelList);
      const nextModelId = modelId || modelList[0]?.id || "";
      setActiveModelId(nextModelId);
      if (nextModelId) {
        const [componentList, interfaceList, dataList, securityList, deploymentList, reviewList, approvalList, baselineList, validationList, fitnessList, diagramList, impactList, traceLinks, coverage] = await Promise.all([
          client.listComponents(nextModelId),
          client.listInterfaces(nextModelId),
          client.listData(nextModelId),
          client.listSecurity(nextModelId),
          client.listDeployments(nextModelId),
          client.listReviews(nextModelId),
          client.listApprovals(nextModelId),
          client.listBaselines(nextModelId),
          client.listValidationResults(nextModelId),
          client.listFitnessFunctions(nextModelId),
          client.listDiagrams(nextModelId),
          client.listImpact(nextModelId),
          client.listTraceabilityLinks(nextModelId),
          client.calculateTraceabilityCoverage(nextModelId),
        ]);
        setComponents(componentList);
        setInterfaces(interfaceList);
        setDataModels(dataList);
        setSecurityModels(securityList);
        setDeployments(deploymentList);
        setReviews(reviewList);
        setApprovals(approvalList);
        setBaselines(baselineList);
        setValidations(validationList);
        setFitness(fitnessList);
        setDiagrams(diagramList);
        setImpacts(impactList);
        setTraceabilityLinks(traceLinks);
        setTraceabilityCoverage(coverage);
      } else {
        setComponents([]);
        setInterfaces([]);
        setDataModels([]);
        setSecurityModels([]);
        setDeployments([]);
        setReviews([]);
        setApprovals([]);
        setBaselines([]);
        setValidations([]);
        setFitness([]);
        setDiagrams([]);
        setImpacts([]);
        setTraceabilityLinks([]);
        setTraceabilityCoverage(null);
      }
      setState(modelList.length ? "ready" : "empty");
    } catch (loadError) {
      setError(loadError);
      setState(loadError?.status === 403 ? "forbidden" : loadError?.status === 401 ? "unauthorized" : "service_unavailable");
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    reload(activeModelId, controller.signal);
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [baseUrl, session?.workspace_id, route.section, route.id]);

  async function runAction(action) {
    setActionError(null);
    try {
      await action();
      await reload(activeModelId);
    } catch (error) {
      setActionError(error);
    }
  }

  const activeModel = models.find((model) => model.id === activeModelId) || null;
  const aiExecutionId = activeModel?.metadata?.created_from_execution_id || "";

  return (
    <main className="novacodepro-page architecture-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">NovaCodePro Architecture Studio</p>
          <h1>Governed Architecture Foundation</h1>
          <p className="page-summary">
            Approved requirements become architecture models, validations, baselines, diagrams, impact analysis, and traceable evidence.
          </p>
        </div>
        <div className="context-row">
          <Chip label="Tenant" value={session?.tenant_id || session?.organization || "Unknown"} />
          <Chip label="Workspace" value={session?.workspace_id || session?.workspace?.id || "Required"} />
          <Chip label="Role" value={session?.active_role || session?.role || "Unknown"} />
          <Chip label="Environment" value={session?.environment || "development"} />
        </div>
      </header>

      <StateBanner state={state} error={error || actionError} />

      <section className="page-grid">
        <Panel title="Architecture Workspaces" aside={<span className="status-pill">{workspaces.length}</span>}>
          <List
            items={workspaces}
            empty="No architecture workspaces yet."
            renderItem={(workspace) => (
              <button key={workspace.id} type="button" className="stack-item" onClick={() => setSelectedWorkspaceId(workspace.id)}>
                <strong>{workspace.name}</strong>
                <span>{workspace.domain}</span>
              </button>
            )}
          />
          <div className="stack">
            <Field label="Workspace name" value={workspaceDraft.name} onChange={(event) => setWorkspaceDraft((draft) => ({ ...draft, name: event.target.value }))} readOnly={false} />
            <TextAreaField label="Description" value={workspaceDraft.description} onChange={(event) => setWorkspaceDraft((draft) => ({ ...draft, description: event.target.value }))} readOnly={false} />
            <button type="button" className="primary-action" onClick={() => runAction(() => client.createWorkspace(workspaceDraft))}>
              Create architecture workspace
            </button>
          </div>
        </Panel>

        <Panel title="Architecture Models" aside={<span className="status-pill">{models.length}</span>}>
          <List
            items={models}
            empty="No architecture models yet."
            renderItem={(model) => (
              <button
                key={model.id}
                type="button"
                className={model.id === activeModelId ? "stack-item active" : "stack-item"}
                onClick={() => {
                  setActiveModelId(model.id);
                  void reload(model.id);
                }}
              >
                <strong>{model.name}</strong>
                <span>{model.domain} • {model.status}</span>
              </button>
            )}
          />
          <div className="stack">
            <label className="form-field">
              <span>Workspace</span>
              <select value={modelDraft.workspace_id || selectedWorkspaceId} onChange={(event) => setModelDraft((draft) => ({ ...draft, workspace_id: event.target.value }))}>
                <option value="">Select workspace</option>
                {workspaces.map((workspace) => (
                  <option key={workspace.id} value={workspace.id}>{workspace.name}</option>
                ))}
              </select>
            </label>
            <Field label="Model name" value={modelDraft.name} onChange={(event) => setModelDraft((draft) => ({ ...draft, name: event.target.value }))} readOnly={false} />
            <TextAreaField label="Description" value={modelDraft.description} onChange={(event) => setModelDraft((draft) => ({ ...draft, description: event.target.value }))} readOnly={false} />
            <Field label="Technology standard" value={modelDraft.technology_standard} onChange={(event) => setModelDraft((draft) => ({ ...draft, technology_standard: event.target.value }))} readOnly={false} />
            <button
              type="button"
              className="primary-action"
              onClick={() =>
                runAction(() =>
                  client.createModel({
                    ...modelDraft,
                    workspace_id: modelDraft.workspace_id || selectedWorkspaceId || session?.workspace_id,
                    requirement_ids: modelDraft.requirement_ids,
                  }),
                )
              }
            >
              Create architecture model
            </button>
          </div>
        </Panel>

        <Panel title="Model Detail" aside={activeModel ? <span className="status-pill">{activeModel.status}</span> : null}>
          {activeModel ? (
            <div className="stack">
              <Field label="Name" value={activeModel.name} />
              <Field label="Domain" value={activeModel.domain} />
              <TextAreaField label="Description" value={activeModel.description} />
              <div className="context-row">
                <Chip label="Components" value={components.length} />
                <Chip label="Interfaces" value={interfaces.length} />
                <Chip label="Data" value={dataModels.length} />
                <Chip label="Security" value={securityModels.length} />
                <Chip label="Deployments" value={deployments.length} />
              </div>
              <div className="context-row">
                <button type="button" className="secondary-action" onClick={() => runAction(() => client.archiveModel(activeModel.id))}>
                  Archive model
                </button>
                <button
                  type="button"
                  className="secondary-action"
                  disabled={!aiExecutionId}
                  onClick={() => runAction(() => client.draftFromAIExecution(aiExecutionId, { workspace_id: activeModel.workspace_id, project_id: activeModel.project_id, request_id: activeModel.request_id, citations: [] }))}
                >
                  Draft from AI execution
                </button>
              </div>
            </div>
          ) : (
            <p className="empty-state">Select an architecture model to inspect its graph and governance state.</p>
          )}
        </Panel>

        <Panel title="Components" aside={<span className="status-pill">{components.length}</span>}>
          <List
            items={components}
            empty="No components yet."
            renderItem={(component) => (
              <article key={component.id} className="stack-item">
                <strong>{component.name}</strong>
                <span>{component.component_type} • {component.status}</span>
              </article>
            )}
          />
          <div className="stack">
            <Field label="Component name" value={componentDraft.name} onChange={(event) => setComponentDraft((draft) => ({ ...draft, name: event.target.value }))} readOnly={false} />
            <label className="form-field">
              <span>Type</span>
              <select value={componentDraft.component_type} onChange={(event) => setComponentDraft((draft) => ({ ...draft, component_type: event.target.value }))}>
                {["GATEWAY", "APPLICATION", "SERVICE", "MICROSERVICE", "API", "DATABASE", "OBSERVABILITY COMPONENT", "SECURITY COMPONENT", "INFRASTRUCTURE COMPONENT", "EXTERNAL SYSTEM", "WEB APP", "MOBILE APP"].map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </label>
            <Field label="Technology" value={componentDraft.technology} onChange={(event) => setComponentDraft((draft) => ({ ...draft, technology: event.target.value }))} readOnly={false} />
            <button type="button" className="primary-action" onClick={() => runAction(() => client.createComponent({ ...componentDraft, model_id: activeModelId || modelDraft.workspace_id }))}>
              Create component
            </button>
          </div>
        </Panel>

        <Panel title="Validation Center" aside={<span className="status-pill">{validations.length}</span>}>
          <List
            items={validations}
            empty="No validation runs yet."
            renderItem={(validation) => (
              <article key={validation.id} className="stack-item">
                <strong>{validation.validation_type}</strong>
                <span>{validation.status}</span>
              </article>
            )}
          />
          <div className="stack">
            <label className="form-field">
              <span>Validation type</span>
              <select value={validationType} onChange={(event) => setValidationType(event.target.value)}>
                {["DEPENDENCY", "SECURITY", "DATA", "DEPLOYMENT", "POLICY", "STANDARDS"].map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
            <button type="button" className="primary-action" onClick={() => runAction(() => client.validateModel(activeModelId, { validation_type: validationType }))}>
              Run validation
            </button>
          </div>
        </Panel>

        <Panel title="Fitness Center" aside={<span className="status-pill">{fitness.length}</span>}>
          <List
            items={fitness}
            empty="No fitness results yet."
            renderItem={(item) => (
              <article key={item.id} className="stack-item">
                <strong>{item.status}</strong>
                <span>{(item.results || []).map((result) => `${result.name}:${result.status}`).join(" • ")}</span>
              </article>
            )}
          />
          <button type="button" className="primary-action" onClick={() => runAction(() => client.evaluateFitness(activeModelId))}>
            Evaluate fitness
          </button>
        </Panel>

        <Panel title="Review Center" aside={<span className="status-pill">{reviews.length}</span>}>
          <List
            items={reviews}
            empty="No architecture reviews yet."
            renderItem={(review) => (
              <article key={review.id} className="stack-item">
                <strong>{review.review_type}</strong>
                <span>{review.status} • {review.decision}</span>
              </article>
            )}
          />
          <button type="button" className="primary-action" onClick={() => runAction(() => client.createReview({ model_id: activeModelId, review_type: "ARCHITECTURE", required_role: "ARCHITECT" }))}>
            Create architecture review
          </button>
        </Panel>

        <Panel title="Approval Center" aside={<span className="status-pill">{approvals.length}</span>}>
          <List
            items={approvals}
            empty="No approvals yet."
            renderItem={(approval) => (
              <article key={approval.id} className="stack-item">
                <strong>{approval.required_role}</strong>
                <span>{approval.status} • {approval.decision}</span>
              </article>
            )}
          />
          <div className="context-row">
            <button type="button" className="primary-action" onClick={() => runAction(() => client.requestApproval({ model_id: activeModelId, required_role: "ARCHITECT", risk_class: "HIGH" }))}>
              Request approval
            </button>
            {approvals[0] ? (
              <button type="button" className="secondary-action" onClick={() => runAction(() => client.approveApproval(approvals[0].id, { model_id: activeModelId, reason: "Reviewed and approved." }))}>
                Approve first
              </button>
            ) : null}
          </div>
        </Panel>

        <Panel title="Baselines" aside={<span className="status-pill">{baselines.length}</span>}>
          <List
            items={baselines}
            empty="No baselines yet."
            renderItem={(baseline) => (
              <article key={baseline.id} className="stack-item">
                <strong>{baseline.name}</strong>
                <span>{baseline.status}</span>
              </article>
            )}
          />
          <div className="stack">
            <Field label="Baseline name" value={baselineName} onChange={(event) => setBaselineName(event.target.value)} readOnly={false} />
            <button type="button" className="primary-action" onClick={() => runAction(() => client.createBaseline({ model_id: activeModelId, name: baselineName, approval_references: approvals.map((approval) => approval.id) }))}>
              Create baseline
            </button>
          </div>
        </Panel>

        <Panel title="Diagrams" aside={<span className="status-pill">{diagrams.length}</span>}>
          <List
            items={diagrams}
            empty="No diagrams yet."
            renderItem={(diagram) => (
              <article key={diagram.id} className="stack-item">
                <strong>{diagram.diagram_type}</strong>
                <span>{diagram.format}</span>
              </article>
            )}
          />
          <div className="stack">
            <label className="form-field">
              <span>Diagram type</span>
              <select value={diagramType} onChange={(event) => setDiagramType(event.target.value)}>
                {["SYSTEM_CONTEXT", "CONTAINER", "COMPONENT", "SEQUENCE", "DEPLOYMENT", "NETWORK", "DATA_FLOW", "EVENT_FLOW", "TRUST_BOUNDARY", "IDENTITY_FLOW", "RECOVERY_FLOW"].map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>Format</span>
              <select value={diagramFormat} onChange={(event) => setDiagramFormat(event.target.value)}>
                {["JSON", "MERMAID", "PLANTUML", "SVG", "PNG"].map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
            <button type="button" className="primary-action" onClick={() => runAction(() => client.createDiagram(activeModelId, { diagram_type: diagramType, format: diagramFormat, title: `${diagramType} Diagram` }))}>
              Generate diagram
            </button>
          </div>
        </Panel>

        <Panel title="Impact Viewer" aside={<span className="status-pill">{impacts.length}</span>}>
          <List
            items={impacts}
            empty="No impact snapshots yet."
            renderItem={(impact) => (
              <article key={impact.id} className="stack-item">
                <strong>{impact.status}</strong>
                <span>{(impact.affected_requirements || []).length} requirements • {(impact.affected_services || []).length} services</span>
              </article>
            )}
          />
          <button type="button" className="primary-action" onClick={() => runAction(() => client.calculateImpact(activeModelId))}>
            Calculate impact
          </button>
        </Panel>

        <Panel
          title="Traceability Bridge"
          aside={<span className="status-pill">{traceabilityCoverage?.coverage_ratio ?? "—"}</span>}
        >
          <List
            items={traceabilityLinks}
            empty="No traceability links yet."
            renderItem={(link) => (
              <article key={link.id} className="stack-item">
                <strong>{link.relationship}</strong>
                <span>{link.source_type} → {link.target_type}</span>
              </article>
            )}
          />
          <button type="button" className="primary-action" onClick={() => runAction(() => client.calculateTraceabilityCoverage(activeModelId))}>
            Refresh traceability coverage
          </button>
        </Panel>
      </section>

      <footer className="page-footer">
        <button type="button" className="toolbar-chip" onClick={() => navigate?.("/novacodepro/requirements")}>
          Requirements Manager
        </button>
        <button type="button" className="toolbar-chip" onClick={onLogout}>
          Log out
        </button>
      </footer>
    </main>
  );
}

export default NCP006APortal;
