import React, { useEffect, useMemo, useState } from "react";

import { createNovaCodeProNcp003Api } from "../novacodepro/api/novacodeproNcp003Api.js";
import { createNovaCodeProNcp006bApi } from "../novacodepro/api/novacodeproNcp006bApi.js";

const DESIGN_NAVIGATION = ["Dashboard","Projects","AI Designer","Research","User Personas","Journey Maps","Flows","Wireframes","Mockups","Components","Design System","Brand Studio","Accessibility","Prototype","Developer Handoff","Assets","Analytics","Version History","Reviews","Approvals","Export","Settings"];
const DESIGN_ROUTES = { Research: "/novacodepro/design/research", "User Personas": "/novacodepro/design/personas", "Journey Maps": "/novacodepro/design/journeys", Flows: "/novacodepro/design/user-flows", Wireframes: "/novacodepro/design/studio" };
const QUICK_ACTIONS = [
  ["Start Designing", "/novacodepro/design/studio"], ["Create Blank Project", "/novacodepro/projects"],
  ["Generate from Prompt", "/novacodepro/ai"], ["Import Requirements", "/novacodepro/requests"],
  ["Import Existing Design", "/novacodepro/design/imports"], ["Open Repository", "/novacodepro/code"],
  ["Open Existing Project", "/novacodepro/projects"], ["Create from Template", "/novacodepro/design/templates"],
];

function DashboardState({ state, error, onRetry }) {
  if (state === "loading") return <div className="design-dashboard-state" role="status"><i /><strong>Loading your design workspace…</strong><span>Projects, reviews, and governed design activity are being retrieved.</span></div>;
  if (state === "error") return <div className="design-dashboard-state error" role="alert"><strong>We couldn’t load the design dashboard.</strong><span>{error}</span><button type="button" onClick={onRetry}>Try again</button></div>;
  return null;
}

export function DesignDashboard({ session, baseUrl = "", onNavigate, onLogout }) {
  const projectApi = useMemo(() => createNovaCodeProNcp003Api({ baseUrl }), [baseUrl]);
  const designApi = useMemo(() => createNovaCodeProNcp006bApi({ baseUrl, session }), [baseUrl, session]);
  const [state, setState] = useState("loading");
  const [error, setError] = useState("");
  const [data, setData] = useState({ workspaces: [], projects: [], designs: [], approvals: [], exports: [], accessibility: [], handoffs: [] });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState("loading");
    Promise.all([
      projectApi.listWorkspaces(controller.signal), designApi.listWorkspaces(controller.signal),
      designApi.listAccessibilityRequirements(controller.signal), designApi.listHandoffs(controller.signal),
    ]).then(async ([workspaces, designs, accessibility, handoffs]) => {
      const activeWorkspace = workspaces[0];
      const [projects, approvals] = await Promise.all([
        projectApi.listProjects(activeWorkspace?.id, controller.signal),
        activeWorkspace ? projectApi.listWorkspaceApprovals(activeWorkspace.id, controller.signal) : [],
      ]);
      setData({ workspaces, projects, designs, approvals, exports: [], accessibility, handoffs });
      setState("ready");
    }).catch((reason) => {
      if (controller.signal.aborted) return;
      setError(reason?.message || "The design services are unavailable.");
      setState("error");
    });
    return () => controller.abort();
  }, [designApi, projectApi, reloadKey]);

  const visibleProjects = data.projects.filter((project) => !query || `${project.name} ${project.description || ""}`.toLowerCase().includes(query.toLowerCase()));
  const activeWorkspace = data.workspaces[0];

  return <div className="design-dashboard" data-testid="design-dashboard">
    <header className="design-dashboard-header">
      <button className="dashboard-menu" type="button" onClick={() => setSidebarOpen((value) => !value)} aria-expanded={sidebarOpen} aria-label="Toggle design navigation">☰</button>
      <button className="public-brand" type="button" onClick={() => onNavigate("/novacodepro/dashboard")}><img src="/novacodepro/brand/NOVACODEPRO.webp" alt=""/><span>NovaCodePro</span></button>
      <div className="dashboard-context"><button type="button">{activeWorkspace?.name || session?.workspace?.name || "Design workspace"}⌄</button><span>/</span><button type="button">All projects⌄</button></div>
      <label className="dashboard-search"><span className="sr-only">Search projects and designs</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search projects, designs, people…"/><kbd>⌘ K</kbd></label>
      <div className="dashboard-header-actions"><button type="button" aria-label="Notifications">◌</button><button type="button" aria-label="Help">?</button><button type="button" className="dashboard-create" onClick={() => onNavigate("/novacodepro/projects")}>+ Create</button><button type="button" className="dashboard-avatar" aria-label="Open profile menu">{(session?.display_name || "NC").split(" ").map((part) => part[0]).slice(0,2).join("")}</button></div>
    </header>
    <aside className={sidebarOpen ? "design-sidebar open" : "design-sidebar"} aria-label="Design navigation">
      <nav>{DESIGN_NAVIGATION.map((item) => <button type="button" key={item} className={item === "Dashboard" ? "active" : ""} onClick={() => onNavigate(item === "Dashboard" ? "/novacodepro/dashboard" : DESIGN_ROUTES[item] || `/novacodepro/design/${item.toLowerCase().replaceAll(/[^a-z]+/g,"-")}`)}><span>{item.slice(0,1)}</span>{item}</button>)}</nav>
      <div className="design-sidebar-footer"><span><i/> Services connected</span><button type="button" onClick={onLogout}>Sign out</button></div>
    </aside>
    <main className="design-dashboard-main">
      <DashboardState state={state} error={error} onRetry={() => setReloadKey((value) => value + 1)}/>
      {state === "ready" ? <>
        <section className="dashboard-welcome"><div><p>DESIGN WORKSPACE</p><h1>Good morning, {(session?.display_name || "Designer").split(" ")[0]}.</h1><span>Continue shaping accessible, governed product experiences.</span></div><div className="collaboration-presence"><i/><i/><i/><span>3 collaborators active</span></div></section>
        <section className="dashboard-actions" aria-label="Design actions">{QUICK_ACTIONS.map(([label,path],index)=><button type="button" key={label} className={index===0?"primary":""} onClick={()=>onNavigate(path)}><span>{index===0?"✦":"＋"}</span><strong>{label}</strong><small>{index===0?"Open the governed studio":"Create or connect"}</small></button>)}</section>
        <section className="dashboard-grid"><div className="dashboard-column wide"><div className="dashboard-section-title"><div><p>CONTINUE WHERE YOU LEFT OFF</p><h2>Recent projects</h2></div><button type="button" onClick={()=>onNavigate("/novacodepro/projects")}>View all</button></div>{visibleProjects.length?<div className="project-card-grid">{visibleProjects.slice(0,6).map((project,index)=><button type="button" className="project-card" key={project.id} onClick={()=>onNavigate(`/novacodepro/projects/${project.id}`)}><div className={`project-art art-${index%4}`}><span>{(project.name||"Project").slice(0,2).toUpperCase()}</span><i>{project.status||"ACTIVE"}</i></div><strong>{project.name||"Untitled project"}</strong><span>{project.description||"Governed design project"}</span><small>Updated {project.updated_at?new Date(project.updated_at).toLocaleDateString():"recently"}</small></button>)}</div>:<div className="dashboard-empty"><strong>{query?"No matching projects":"No projects yet"}</strong><span>{query?"Try a different search.":"Create a governed project to begin."}</span><button type="button" onClick={()=>onNavigate("/novacodepro/projects")}>Create project</button></div>}</div>
          <aside className="dashboard-column"><div className="dashboard-section-title"><div><p>NEEDS ATTENTION</p><h2>Review queue</h2></div></div><div className="queue-list"><span><i className="purple"/><b>{data.approvals.length}</b> approval requests</span><span><i className="amber"/><b>{data.accessibility.length}</b> accessibility items</span><span><i className="blue"/><b>{data.handoffs.length}</b> handoff packages</span><span><i className="green"/><b>{data.exports.length}</b> export records</span></div></aside>
        </section>
        <section className="dashboard-lower-grid"><article><p>PROJECT HEALTH</p><strong>{data.designs.length || data.projects.length}</strong><span>active governed design workspaces</span><div className="health-bar"><i style={{width:`${Math.min(100,60+data.approvals.length*5)}%`}}/></div></article><article><p>AI RECOMMENDATION</p><strong>Review accessibility before handoff</strong><span>Resolve open requirements and attach human-review evidence to the active version.</span><button type="button" onClick={()=>onNavigate("/novacodepro/design/accessibility")}>Open Accessibility Centre →</button></article><article><p>TEAM ACTIVITY</p><strong>{data.projects.length+data.approvals.length+data.exports.length}</strong><span>project, review, and export records in this workspace</span></article></section>
      </>:null}
    </main>
  </div>;
}
