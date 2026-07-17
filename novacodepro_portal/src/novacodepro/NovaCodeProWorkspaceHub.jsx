import React, { useEffect, useMemo, useState } from "react";

import {
  buildNovaCodeProAppLauncher,
  getNovaCodeProApp,
  listNovaCodeProApps,
  parseNovaCodeProRoute,
} from "../platform/appRegistry.js";
import { ROUTES } from "../platform/routes.js";
import { createSolutionEngineeringClient } from "../platform/solutionEngineeringApi.js";

const PREVIEW_MESSAGE = "Pilot preview: visible and routed, but still under staged completion.";

function formatCount(value) {
  return typeof value === "number" ? value.toLocaleString() : String(value ?? "0");
}

function summarizeSession(session) {
  if (!session) {
    return { user: "Unknown", org: "Unknown", workspace: "Workspace", role: "Member" };
  }
  return {
    user: session.user?.display_name || session.user?.username || session.user?.id || "Unknown",
    org: session.organization?.name || session.organization?.id || "Unknown",
    workspace: session.workspace?.name || session.workspace?.title || session.workspace?.id || "Workspace",
    role: session.user?.active_role || session.user?.role_label || "Member",
  };
}

export function NovaCodeProWorkspaceHub({ session, pathname, navigate, baseUrl = "", onLogout }) {
  const route = useMemo(() => parseNovaCodeProRoute(pathname) || parseNovaCodeProRoute(ROUTES.workspaceRoot), [pathname]);
  const client = useMemo(
    () =>
      createSolutionEngineeringClient({
        baseUrl,
        session,
      }),
    [baseUrl, session],
  );

  const sessionSummary = summarizeSession(session);
  const apps = useMemo(() => buildNovaCodeProAppLauncher(session?.permissions || []), [session?.permissions]);
  const selectedApp = useMemo(() => getNovaCodeProApp(route?.appId || "workspace") || listNovaCodeProApps()[0] || null, [route?.appId]);

  const [projects, setProjects] = useState([]);
  const [workspaces, setWorkspaces] = useState([]);
  const [loadingState, setLoadingState] = useState("idle");
  const [requestState, setRequestState] = useState("idle");
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [projectName, setProjectName] = useState("NovaCodePro Workspace Slice");
  const [customerName, setCustomerName] = useState(session?.organization?.name || "NovaTech");
  const [projectSummary, setProjectSummary] = useState("Vertical slice for the governed NovaCodePro platform.");
  const [requestText, setRequestText] = useState("Build the shared NovaCodePro workspace shell, registry, project manager, and request composer.");
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
  const [selectedAppId, setSelectedAppId] = useState(route?.appId || "workspace");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoadingState("loading");
      setError("");
      try {
        const [workspaceList, projectList] = await Promise.all([
          client.listWorkspaces().catch(() => []),
          client.listProjects().catch(() => []),
        ]);
        if (cancelled) {
          return;
        }
        setWorkspaces(Array.isArray(workspaceList) ? workspaceList : []);
        setProjects(Array.isArray(projectList) ? projectList : []);
        setSelectedWorkspaceId((workspaceList && workspaceList[0]?.id) || "");
        setSelectedProjectId((projectList && projectList[0]?.id) || "");
        setLoadingState("ready");
      } catch (fetchError) {
        if (cancelled) {
          return;
        }
        setLoadingState("error");
        setError(fetchError?.message || "Unable to load the NovaCodePro workspace.");
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [client]);

  useEffect(() => {
    setSelectedAppId(route?.appId || "workspace");
  }, [route?.appId]);

  const launchApp = (app) => {
    if (!app) {
      return;
    }
    navigate(app.route, { replace: false });
  };

  const handleCreateProject = async (event) => {
    event.preventDefault();
    if (requestState === "busy") {
      return;
    }
    setRequestState("busy");
    setError("");
    setResult(null);
    try {
      const createdProject = await client.createProject({
        name: projectName.trim(),
        tenant_id: session?.organization?.id || "novacodepro",
        organization_id: session?.organization?.id || "novacodepro",
        idea: projectSummary.trim(),
        request: projectSummary.trim(),
        domain: "novacodepro",
        region: "Australia",
        owner: session?.user?.id || session?.user?.username || "novacodepro-user",
        surfaces: ["workspace", "projects", "requests", "ai"],
      });
      const projectId = createdProject?.id || createdProject?.project_id || "";
      if (projectId) {
        setProjects((current) => [createdProject, ...current.filter((item) => item.id !== projectId)]);
        setSelectedProjectId(projectId);
        navigate(`/novacodepro/projects/${encodeURIComponent(projectId)}`);
      }
      setResult({
        type: "project-created",
        title: "Project created",
        details: createdProject,
      });
      setRequestState("ready");
    } catch (createError) {
      setRequestState("error");
      setError(createError?.message || "Unable to create the project.");
    }
  };

  const handleSubmitRequest = async (event) => {
    event.preventDefault();
    if (requestState === "busy") {
      return;
    }
    setRequestState("busy");
    setError("");
    setResult(null);
    try {
      let projectId = selectedProjectId || projects[0]?.id || "";
      if (!projectId) {
        const createdProject = await client.createProject({
          name: projectName.trim(),
          idea: projectSummary.trim(),
          request: projectSummary.trim(),
          domain: "novacodepro",
          region: "Australia",
          organization_id: session?.organization?.id || "novacodepro",
          owner: session?.user?.id || session?.user?.username || "novacodepro-user",
          surfaces: ["workspace", "projects", "requests", "ai"],
        });
        projectId = createdProject?.id || createdProject?.project_id || "";
        if (projectId) {
          setProjects((current) => [createdProject, ...current.filter((item) => item.id !== projectId)]);
          setSelectedProjectId(projectId);
          navigate(`/novacodepro/projects/${encodeURIComponent(projectId)}`);
        }
      }
      if (!projectId) {
        throw new Error("A project is required before submitting a request.");
      }
      const request = await client.submitIdea(projectId, {
        title: requestText.trim().slice(0, 120) || "NovaCodePro request",
        problem: requestText.trim(),
        target_users: [customerName.trim() || "NovaTech"],
        market: "NovaCodePro",
        industry: "platform",
        budget_range: "pilot",
        timeline: "incremental",
      });
      setResult({
        type: "request-submitted",
        title: "Request submitted",
        details: request,
      });
      setRequestState("ready");
      navigate(`/novacodepro/projects/${encodeURIComponent(projectId)}/requests`);
    } catch (submitError) {
      setRequestState("error");
      setError(submitError?.message || "Unable to submit the request.");
    }
  };

  const selectedAppState = selectedApp?.status === "preview" ? PREVIEW_MESSAGE : selectedApp?.status === "disabled" ? "This app is disabled." : "Operational";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">N</div>
          <div>
            <p className="eyebrow">NovaCodePro internal development platform</p>
            <strong>Workspace Hub</strong>
          </div>
        </div>
        <div className="topbar-actions">
          <button type="button" className="toolbar-chip" onClick={() => navigate(ROUTES.dashboard)}>
            Shell home
          </button>
          <button type="button" className="toolbar-chip" onClick={() => navigate(ROUTES.workspaceRoot)}>
            Workspace
          </button>
          <button type="button" className="toolbar-chip" onClick={() => onLogout?.()}>
            Log out
          </button>
        </div>
      </header>

      <main className="workspace-shell">
        <section className="workspace-band">
          <div className="workspace-band-header">
            <div>
              <p className="section-label">Unified application shell</p>
              <h1>{selectedApp?.name || "Workspace"}</h1>
              <p>{selectedApp?.description || "Shared NovaCodePro workspace, request flow, and governed app launcher."}</p>
            </div>
            <div className="workspace-summary">
              <span>{sessionSummary.user}</span>
              <span>{sessionSummary.org}</span>
              <span>{sessionSummary.workspace}</span>
              <span>{sessionSummary.role}</span>
            </div>
          </div>
          <div className="workspace-tabs" role="tablist" aria-label="NovaCodePro applications">
            {apps.map((app) => (
              <button
                key={app.id}
                type="button"
                className={app.id === selectedAppId ? "workspace-tab active" : "workspace-tab"}
                onClick={() => {
                  setSelectedAppId(app.id);
                  launchApp(app);
                }}
                aria-label={`Open ${app.name}`}
              >
                {app.name}
                <small>{app.status === "active" ? "Operational" : "Pilot preview"}</small>
              </button>
            ))}
          </div>
        </section>

        <section className="workspace-grid">
          <article className="dashboard-card">
            <p className="section-label">Launcher</p>
            <h2>Application registry</h2>
            <p>One governed registry drives the shared shell and the modular application surfaces.</p>
            <div className="metric-grid">
              <div className="metric-card">
                <strong>{formatCount(apps.length)}</strong>
                <span>Registered apps</span>
              </div>
              <div className="metric-card">
                <strong>{formatCount(apps.filter((app) => app.status === "active").length)}</strong>
                <span>Active surfaces</span>
              </div>
              <div className="metric-card">
                <strong>{formatCount(apps.filter((app) => app.status === "preview").length)}</strong>
                <span>Pilot previews</span>
              </div>
            </div>
            <div className="stacked-actions">
              {apps.map((app) => (
                <button
                  key={`${app.id}-launch`}
                  type="button"
                  className="primary-button"
                  onClick={() => launchApp(app)}
                  disabled={app.status === "disabled"}
                >
                  Open {app.name}
                </button>
              ))}
            </div>
          </article>

          <article className="dashboard-card">
            <p className="section-label">Selected app</p>
            <h2>{selectedApp?.name || "Workspace"}</h2>
            <p>{selectedAppState}</p>
            <div className="artifact-list">
              <div className="artifact-row">
                <strong>Route</strong>
                <span>{selectedApp?.route || ROUTES.workspaceRoot}</span>
              </div>
              <div className="artifact-row">
                <strong>Status</strong>
                <span>{selectedApp?.status || "active"}</span>
              </div>
              <div className="artifact-row">
                <strong>Permissions</strong>
                <span>{selectedApp?.requiredPermissions?.join(", ") || "None"}</span>
              </div>
            </div>
            <button type="button" className="secondary-button" onClick={() => navigate(selectedApp?.route || ROUTES.workspaceRoot)}>
              Open this surface
            </button>
          </article>
        </section>

        <section className="workspace-grid">
          <article className="dashboard-card">
            <p className="section-label">Workspace home</p>
            <h2>Projects and workspaces</h2>
            <p>Use the first governed slice to create a project and push a request through the real solution-engineering API.</p>
            <div className="artifact-list">
              <div className="artifact-row">
                <strong>Workspaces</strong>
                <span>{formatCount(workspaces.length)} available</span>
              </div>
              <div className="artifact-row">
                <strong>Projects</strong>
                <span>{formatCount(projects.length)} loaded</span>
              </div>
              <div className="artifact-row">
                <strong>Selected project</strong>
                <span>{selectedProjectId || "None"}</span>
              </div>
            </div>
            <div className="stacked-actions">
              <button type="button" className="secondary-button" onClick={() => navigate(ROUTES.projectsRoot)}>
                Project manager
              </button>
              <button type="button" className="secondary-button" onClick={() => navigate(ROUTES.requestsRoot)}>
                Request composer
              </button>
              <button type="button" className="secondary-button" onClick={() => navigate(ROUTES.aiRoot)}>
                NovaAI
              </button>
            </div>
          </article>

          <article className="dashboard-card">
            <p className="section-label">Project creation</p>
            <h2>Create a governed project</h2>
            <form className="form-grid" onSubmit={handleCreateProject}>
              <label>
                Project name
                <input value={projectName} onChange={(event) => setProjectName(event.target.value)} />
              </label>
              <label>
                Customer
                <input value={customerName} onChange={(event) => setCustomerName(event.target.value)} />
              </label>
              <label className="span-2">
                Summary
                <textarea rows={3} value={projectSummary} onChange={(event) => setProjectSummary(event.target.value)} />
              </label>
              <button type="submit" className="primary-button" disabled={requestState === "busy" || !projectName.trim()}>
                Create project
              </button>
            </form>
          </article>
        </section>

        <section className="workspace-grid">
          <article className="dashboard-card">
            <p className="section-label">Request composer</p>
            <h2>Submit a request</h2>
            <form className="form-grid" onSubmit={handleSubmitRequest}>
              <label className="span-2">
                Request text
                <textarea rows={5} value={requestText} onChange={(event) => setRequestText(event.target.value)} />
              </label>
              <label>
                Target project
                <select value={selectedProjectId} onChange={(event) => setSelectedProjectId(event.target.value)}>
                  <option value="">Create a new project</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name || project.id}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Workspace
                <select value={selectedWorkspaceId} onChange={(event) => setSelectedWorkspaceId(event.target.value)}>
                  <option value="">Use active workspace</option>
                  {workspaces.map((workspace) => (
                    <option key={workspace.id} value={workspace.id}>
                      {workspace.name || workspace.title || workspace.id}
                    </option>
                  ))}
                </select>
              </label>
              <button type="submit" className="primary-button" disabled={requestState === "busy" || !requestText.trim()}>
                Submit request
              </button>
            </form>
          </article>

          <article className="dashboard-card">
            <p className="section-label">Outcome</p>
            <h2>Latest action</h2>
            {loadingState === "loading" ? (
              <p>Loading workspace data…</p>
            ) : null}
            {error ? <p role="alert">{error}</p> : null}
            {result ? (
              <div className="artifact-list">
                <div className="artifact-row">
                  <strong>{result.title}</strong>
                  <span>{result.type}</span>
                </div>
                <pre>{JSON.stringify(result.details, null, 2)}</pre>
              </div>
            ) : (
              <p>No action has been submitted yet.</p>
            )}
          </article>
        </section>
      </main>
    </div>
  );
}
