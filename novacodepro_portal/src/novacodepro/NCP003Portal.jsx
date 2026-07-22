import React, { useEffect, useMemo, useState } from "react";

import { classifyNcp003RouteState, createNovaCodeProNcp003Api } from "./api/novacodeproNcp003Api.js";

function parseRoute(pathname) {
  const parts = String(pathname || "")
    .replace(/\/+$/, "")
    .split("/")
    .filter(Boolean);
  if (parts[0] !== "novacodepro") {
    return { section: "workspace", subRoute: "home" };
  }
  const section = parts[1] || "workspace";
  if (section === "workspace") {
    return { section, subRoute: parts[2] || "home", id: parts[3] || null };
  }
  return { section, id: parts[2] || null, subRoute: parts[3] || "home" };
}

function StateBanner({ state, error }) {
  if (state === "ready") {
    return null;
  }
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

function SimpleSection({ title, children, aside }) {
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

function ActionButton({ children, ...props }) {
  return (
    <button type="button" className={props.variant === "secondary" ? "secondary-action" : "primary-action"} {...props}>
      {children}
    </button>
  );
}

function fieldValue(value) {
  return typeof value === "string" ? value : value == null ? "" : String(value);
}

export function NCP003Portal({ session, pathname, navigate, baseUrl = "", onLogout, onSessionChange }) {
  const client = useMemo(() => createNovaCodeProNcp003Api({ baseUrl }), [baseUrl]);
  const route = useMemo(() => parseRoute(pathname), [pathname]);
  const [loadState, setLoadState] = useState("loading");
  const [loadError, setLoadError] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState(session?.workspace_id || session?.workspace?.id || "");
  const [workspaceDetail, setWorkspaceDetail] = useState(null);
  const [workspaceActivity, setWorkspaceActivity] = useState([]);
  const [workspaceNotifications, setWorkspaceNotifications] = useState([]);
  const [workspaceFavorites, setWorkspaceFavorites] = useState([]);
  const [workspaceMembers, setWorkspaceMembers] = useState([]);
  const [workspaceTasks, setWorkspaceTasks] = useState([]);
  const [workspaceApprovals, setWorkspaceApprovals] = useState([]);
  const [projects, setProjects] = useState([]);
  const [requests, setRequests] = useState([]);
  const [projectDetail, setProjectDetail] = useState(null);
  const [projectActivity, setProjectActivity] = useState([]);
  const [projectMembers, setProjectMembers] = useState([]);
  const [projectMilestones, setProjectMilestones] = useState([]);
  const [projectWorkItems, setProjectWorkItems] = useState([]);
  const [projectRisks, setProjectRisks] = useState([]);
  const [projectRoadmap, setProjectRoadmap] = useState(null);
  const [requestDetail, setRequestDetail] = useState(null);
  const [requestHistory, setRequestHistory] = useState([]);
  const [requestAssignments, setRequestAssignments] = useState([]);
  const [requestComments, setRequestComments] = useState([]);
  const [requestAttachments, setRequestAttachments] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [actionError, setActionError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [projectDraft, setProjectDraft] = useState({ name: "", description: "", owner_id: session?.user?.id || "" });
  const [milestoneDraft, setMilestoneDraft] = useState({ name: "", due_date: "" });
  const [workItemDraft, setWorkItemDraft] = useState({ title: "", type: "TASK", description: "", assignee_id: "" });
  const [riskDraft, setRiskDraft] = useState({ title: "", severity: "MEDIUM" });
  const [requestDraft, setRequestDraft] = useState({ title: "", description: "", project_id: "", priority: "MEDIUM", request_type: "TEXT" });
  const [commentDraft, setCommentDraft] = useState("");
  const [assignmentDraft, setAssignmentDraft] = useState({ assignee_id: "", assignment_role: "REVIEWER" });
  const [attachmentDraft, setAttachmentDraft] = useState({ filename: "", content_type: "text/plain", content: "" });
  const [transitionTarget, setTransitionTarget] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [composerOpen, setComposerOpen] = useState(false);
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false);

  const workspaceId = activeWorkspaceId || session?.workspace_id || session?.workspace?.id || "";
  const projectId = route.section === "projects" ? route.id : null;
  const requestId = route.section === "requests" ? route.id : null;
  const permissionSet = useMemo(() => new Set((session?.permissions || []).map(String)), [session?.permissions]);
  const hasPermission = (permission) => permissionSet.has(permission);
  const canCreateProject = hasPermission("project.create");
  const canCreateRequest = hasPermission("request.create");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoadState("loading");
      setLoadError(null);
      try {
        const [workspaceList, notificationList] = await Promise.all([
          client.listWorkspaces(),
          client.listNotifications(),
        ]);
        if (cancelled) {
          return;
        }
        setWorkspaces(workspaceList);
        setNotifications(notificationList);
        const selected = workspaceList.find((item) => item.id === workspaceId) || workspaceList[0] || null;
        if (selected) {
          setActiveWorkspaceId(selected.id);
          const [workspace, activity, favorites, members, tasks, approvals, projectList, requestList] = await Promise.all([
            client.getWorkspace(selected.id),
            client.listWorkspaceActivity(selected.id),
            client.listWorkspaceFavorites(selected.id),
            client.listWorkspaceMembers(selected.id),
            client.listWorkspaceTasks(selected.id),
            client.listWorkspaceApprovals(selected.id),
            client.listProjects(selected.id),
            client.listRequests(selected.id),
          ]);
          if (cancelled) {
            return;
          }
          setWorkspaceDetail(workspace);
          setWorkspaceActivity(activity);
          setWorkspaceFavorites(favorites);
          setWorkspaceMembers(members);
          setWorkspaceTasks(tasks);
          setWorkspaceApprovals(approvals);
          setProjects(projectList);
          setRequests(requestList);
          setProjectDraft((current) => ({ ...current, project_id: current.project_id || projectList[0]?.id || "" }));
          setRequestDraft((current) => ({ ...current, project_id: current.project_id || projectList[0]?.id || "" }));
        } else {
          setWorkspaceDetail(null);
          setProjects([]);
          setRequests([]);
        }
        if (projectId) {
          const [project, activity, members, milestones, workItems, risks, roadmap] = await Promise.all([
            client.getProject(projectId),
            client.listProjectActivity(projectId),
            client.listProjectMembers(projectId),
            client.listProjectMilestones(projectId),
            client.listProjectWorkItems(projectId),
            client.listProjectRisks(projectId),
            client.getProjectRoadmap(projectId),
          ]);
          if (!cancelled) {
            setProjectDetail(project);
            setProjectActivity(activity);
            setProjectMembers(members);
            setProjectMilestones(milestones);
            setProjectWorkItems(workItems);
            setProjectRisks(risks);
            setProjectRoadmap(roadmap);
            setMilestoneDraft((current) => ({ ...current, name: current.name || "" }));
            setWorkItemDraft((current) => ({ ...current, title: current.title || "" }));
            setRiskDraft((current) => ({ ...current, title: current.title || "" }));
          }
        } else {
          setProjectDetail(null);
          setProjectActivity([]);
          setProjectMembers([]);
          setProjectMilestones([]);
          setProjectWorkItems([]);
          setProjectRisks([]);
          setProjectRoadmap(null);
        }
        if (requestId) {
          const [request, history, assignments, comments, attachments] = await Promise.all([
            client.getRequest(requestId),
            client.getRequestHistory(requestId),
            client.listRequestAssignments(requestId),
            client.listRequestComments(requestId),
            client.listRequestAttachments(requestId),
          ]);
          if (!cancelled) {
            setRequestDetail(request);
            setRequestHistory(history);
            setRequestAssignments(assignments);
            setRequestComments(comments);
            setRequestAttachments(attachments);
            setAssignmentDraft((current) => ({ ...current, assignee_id: current.assignee_id || "" }));
            setAttachmentDraft((current) => ({ ...current, filename: current.filename || "" }));
          }
        } else {
          setRequestDetail(null);
          setRequestHistory([]);
          setRequestAssignments([]);
          setRequestComments([]);
          setRequestAttachments([]);
        }
        setLoadState("ready");
      } catch (error) {
        if (cancelled) {
          return;
        }
        setLoadError(error);
        setLoadState(classifyNcp003RouteState(error));
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [client, workspaceId, projectId, requestId]);

  const selectWorkspace = async (nextWorkspaceId) => {
    setActionError(null);
    setLoadState("loading");
    setWorkspaceDetail(null);
    setProjects([]);
    setRequests([]);
    try {
      const result = await client.selectWorkspace(nextWorkspaceId);
      setActiveWorkspaceId(result?.session?.workspace_id || nextWorkspaceId);
      onSessionChange?.(result);
      navigate("/novacodepro/workspace");
    } catch (error) {
      setActionError(error);
      setLoadState(classifyNcp003RouteState(error));
    }
  };

  const refreshWorkspace = async () => {
    const nextId = activeWorkspaceId || workspaceId;
    if (!nextId) {
      return;
    }
    const [workspace, activity, favorites, members, tasks, approvals, projectList, requestList, notificationList] = await Promise.all([
      client.getWorkspace(nextId),
      client.listWorkspaceActivity(nextId),
      client.listWorkspaceFavorites(nextId),
      client.listWorkspaceMembers(nextId),
      client.listWorkspaceTasks(nextId),
      client.listWorkspaceApprovals(nextId),
      client.listProjects(nextId),
      client.listRequests(nextId),
      client.listNotifications(),
    ]);
    setWorkspaceDetail(workspace);
    setWorkspaceActivity(activity);
    setWorkspaceFavorites(favorites);
    setWorkspaceMembers(members);
    setWorkspaceTasks(tasks);
    setWorkspaceApprovals(approvals);
    setProjects(projectList);
    setRequests(requestList);
    setNotifications(notificationList);
  };

  const handleCreateProject = async (event) => {
    event.preventDefault();
    setSaving(true);
    setActionError(null);
    try {
      const created = await client.createProject({ ...projectDraft, workspace_id: activeWorkspaceId || workspaceId }, `project-${Date.now()}`);
      navigate(`/novacodepro/projects/${encodeURIComponent(created.id)}`);
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateProject = async (event) => {
    event.preventDefault();
    if (!projectDetail) return;
    setSaving(true);
    setActionError(null);
    try {
      const updated = await client.updateProject(projectDetail.id, projectDraft);
      setProjectDetail(updated);
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleArchiveProject = async () => {
    if (!projectDetail) return;
    setSaving(true);
    setActionError(null);
    try {
      const archived = await client.archiveProject(projectDetail.id);
      setProjectDetail(archived);
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateMilestone = async (event) => {
    event.preventDefault();
    if (!projectDetail) return;
    setSaving(true);
    setActionError(null);
    try {
      const milestone = await client.createProjectMilestone(projectDetail.id, milestoneDraft);
      setProjectMilestones((current) => [milestone, ...current]);
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateWorkItem = async (event) => {
    event.preventDefault();
    if (!projectDetail) return;
    setSaving(true);
    setActionError(null);
    try {
      const workItem = await client.createProjectWorkItem(projectDetail.id, workItemDraft);
      setProjectWorkItems((current) => [workItem, ...current]);
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateRisk = async (event) => {
    event.preventDefault();
    if (!projectDetail) return;
    setSaving(true);
    setActionError(null);
    try {
      const risk = await client.createProjectRisk(projectDetail.id, riskDraft);
      setProjectRisks((current) => [risk, ...current]);
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateRequest = async (event) => {
    event.preventDefault();
    setSaving(true);
    setActionError(null);
    try {
      const created = await client.createRequest({ ...requestDraft, workspace_id: activeWorkspaceId || workspaceId }, `request-${Date.now()}`);
      navigate(`/novacodepro/requests/${encodeURIComponent(created.id)}`);
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateRequest = async (event) => {
    event.preventDefault();
    if (!requestDetail) return;
    setSaving(true);
    setActionError(null);
    try {
      const updated = await client.updateRequest(requestDetail.id, requestDraft);
      setRequestDetail(updated);
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleSubmitRequest = async () => {
    if (!requestDetail) return;
    setSaving(true);
    setActionError(null);
    try {
      const submitted = await client.submitRequest(requestDetail.id);
      setRequestDetail(submitted);
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleTransitionRequest = async () => {
    if (!requestDetail || !transitionTarget) return;
    setSaving(true);
    setActionError(null);
    try {
      const transitioned = await client.transitionRequest(requestDetail.id, { status: transitionTarget, reason: `Changed to ${transitionTarget}` });
      setRequestDetail(transitioned);
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleAddAssignment = async (event) => {
    event.preventDefault();
    if (!requestDetail) return;
    setSaving(true);
    setActionError(null);
    try {
      const assignment = await client.addRequestAssignment(requestDetail.id, assignmentDraft);
      setRequestAssignments((current) => [assignment, ...current]);
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleAddComment = async (event) => {
    event.preventDefault();
    if (!requestDetail || !commentDraft.trim()) return;
    setSaving(true);
    setActionError(null);
    try {
      const comment = await client.addRequestComment(requestDetail.id, { body: commentDraft.trim(), mentions: [] });
      setRequestComments((current) => [comment, ...current]);
      setCommentDraft("");
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  const handleAddAttachment = async (event) => {
    event.preventDefault();
    if (!requestDetail) return;
    setSaving(true);
    setActionError(null);
    try {
      const attachment = await client.addRequestAttachment(requestDetail.id, attachmentDraft);
      setRequestAttachments((current) => [attachment, ...current]);
      await refreshWorkspace();
    } catch (error) {
      setActionError(error);
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    if (projectDetail) {
      setProjectDraft({
        name: fieldValue(projectDetail.name),
        description: fieldValue(projectDetail.description),
        owner_id: fieldValue(projectDetail.owner_id || projectDetail.created_by || session?.user?.id || ""),
        start_date: fieldValue(projectDetail.start_date),
        target_date: fieldValue(projectDetail.target_date),
      });
    }
  }, [projectDetail, session?.user?.id]);

  useEffect(() => {
    if (requestDetail) {
      setRequestDraft({
        title: fieldValue(requestDetail.title),
        description: fieldValue(requestDetail.description),
        project_id: fieldValue(requestDetail.project_id || projectDetail?.id || requestDraft.project_id),
        priority: fieldValue(requestDetail.priority || "MEDIUM"),
        request_type: fieldValue(requestDetail.request_type || "TEXT"),
      });
      setTransitionTarget((requestDetail.available_transitions || [])[0] || "");
    }
  }, [requestDetail, projectDetail?.id]);

  const workspaceLabel = workspaceDetail?.name || session?.workspace?.name || "Workspace";
  const workspaceItems = workspaces.length ? workspaces : [{ id: activeWorkspaceId || "enterprise-developer", name: workspaceLabel }];
  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredProjects = projects.filter((item) =>
    (!normalizedQuery || `${item.name || ""} ${item.description || ""} ${item.owner_id || ""}`.toLowerCase().includes(normalizedQuery)) &&
    (statusFilter === "ALL" || item.status === statusFilter));
  const filteredRequests = requests.filter((item) =>
    (!normalizedQuery || `${item.id || ""} ${item.title || ""} ${item.description || ""}`.toLowerCase().includes(normalizedQuery)) &&
    (statusFilter === "ALL" || item.status === statusFilter));

  const renderWorkspaceHome = () => (
    <div className="ncp003-page-grid" data-testid="workspace-home">
      <section className="ncp003-hero-card">
        <div>
          <p className="section-label">Workspace overview</p>
          <h2>{workspaceLabel}</h2>
          <p>{session?.organization?.name || session?.organization || session?.tenant_id || "NovaTech"} · {session?.active_role || "Member"}</p>
        </div>
        <div className="ncp003-workspace-select">
          <label htmlFor="active-workspace">Active workspace</label>
          <select id="active-workspace" value={activeWorkspaceId} onChange={(event) => selectWorkspace(event.target.value)}>
            {workspaceItems.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
          </select>
        </div>
      </section>

      <section className="ncp003-metrics" aria-label="Workspace portfolio summary">
        {[
          ["Active projects", projects.filter((item) => item.status !== "ARCHIVED").length, "Delivery portfolio"],
          ["Open requests", requests.filter((item) => !["COMPLETED", "CLOSED", "ARCHIVED"].includes(item.status)).length, "Governed intake"],
          ["Pending approvals", workspaceApprovals.filter((item) => item.status === "PENDING").length, "Needs attention"],
          ["Team members", workspaceMembers.length, "Workspace access"],
        ].map(([label, value, note]) => (
          <article className="ncp003-metric" key={label}><span>{label}</span><strong>{value}</strong><small>{note}</small></article>
        ))}
      </section>

      <section className="ncp003-panel ncp003-quick-actions">
        <div className="ncp003-section-heading"><div><p className="section-label">Start work</p><h3>Quick actions</h3></div></div>
        <div className="ncp003-action-grid">
          <button type="button" disabled={!canCreateProject} onClick={() => navigate("/novacodepro/projects")}>New project<span>Define and govern delivery work</span></button>
          <button type="button" disabled={!canCreateRequest} onClick={() => navigate("/novacodepro/requests")}>New request<span>Capture an idea or change</span></button>
          <button type="button" onClick={() => projects[0] && navigate(`/novacodepro/projects/${projects[0].id}`)} disabled={!projects.length}>Open recent work<span>Resume the latest project</span></button>
        </div>
      </section>

      <section className="ncp003-panel">
        <div className="ncp003-section-heading"><div><p className="section-label">Portfolio</p><h3>Recent projects</h3></div><button type="button" onClick={() => navigate("/novacodepro/projects")}>View all</button></div>
        <List items={projects.slice(0, 4)} empty="No projects yet. Create one when you are ready." renderItem={(item) => (
          <button key={item.id} className="ncp003-list-row" type="button" onClick={() => navigate(`/novacodepro/projects/${item.id}`)}><span><strong>{item.name}</strong><small>{item.description || "No description"}</small></span><b>{item.status}</b></button>
        )} />
      </section>

      <section className="ncp003-panel">
        <div className="ncp003-section-heading"><div><p className="section-label">Traceability</p><h3>Recent activity</h3></div><span>Live workspace events</span></div>
        <List items={workspaceActivity.slice(0, 6)} empty="No workspace activity yet." renderItem={(item) => (
          <div key={item.id || item.event_type} className="ncp003-activity-row"><i aria-hidden="true" /><span><strong>{String(item.event_type || "Activity").replaceAll(".", " ")}</strong><small>{item.actor_id || session?.display_name || "Workspace member"}</small></span><time>{item.timestamp || item.created_at || "Recently"}</time></div>
        )} />
      </section>
    </div>
  );

  const renderProjectDetail = () => {
    if (!projectDetail) {
      return <p className="empty-state">Project not loaded.</p>;
    }
    const archived = projectDetail.status === "ARCHIVED";
    return (
      <div className="grid two-col">
        <SimpleSection title="Project detail" aside={<span>{projectDetail.status}</span>}>
          <form onSubmit={handleUpdateProject} className="stack">
            <label className="field">
              <span>Name</span>
              <input value={projectDraft.name} onChange={(event) => setProjectDraft((current) => ({ ...current, name: event.target.value }))} />
            </label>
            <label className="field">
              <span>Description</span>
              <textarea value={projectDraft.description} onChange={(event) => setProjectDraft((current) => ({ ...current, description: event.target.value }))} rows={4} />
            </label>
            <div className="inline-actions">
              <ActionButton type="submit" disabled={saving || archived}>Save project</ActionButton>
              <ActionButton type="button" variant="secondary" onClick={handleArchiveProject} disabled={saving || archived}>
                Archive project
              </ActionButton>
            </div>
          </form>
          {archived ? <p className="helper-text">Archived projects remain readable but block new milestones, tasks, and other mutations.</p> : null}
        </SimpleSection>

        <SimpleSection title="Milestones">
          <form onSubmit={handleCreateMilestone} className="stack">
            <input placeholder="Milestone name" value={milestoneDraft.name} onChange={(event) => setMilestoneDraft((current) => ({ ...current, name: event.target.value }))} disabled={archived} />
            <input type="date" value={milestoneDraft.due_date} onChange={(event) => setMilestoneDraft((current) => ({ ...current, due_date: event.target.value }))} disabled={archived} />
            <ActionButton type="submit" disabled={saving || archived || !milestoneDraft.name.trim()}>Add milestone</ActionButton>
          </form>
          <List
            items={projectMilestones}
            empty="No milestones."
            renderItem={(item) => (
              <div key={item.id} className="artifact-row">
                <strong>{item.name}</strong>
                <span>{item.status}</span>
              </div>
            )}
          />
        </SimpleSection>

        <SimpleSection title="Work items">
          <form onSubmit={handleCreateWorkItem} className="stack">
            <input placeholder="Work item title" value={workItemDraft.title} onChange={(event) => setWorkItemDraft((current) => ({ ...current, title: event.target.value }))} disabled={archived} />
            <select value={workItemDraft.type} onChange={(event) => setWorkItemDraft((current) => ({ ...current, type: event.target.value }))} disabled={archived}>
              {["EPIC", "FEATURE", "STORY", "TASK", "BUG", "RISK"].map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
            <input placeholder="Assignee" value={workItemDraft.assignee_id} onChange={(event) => setWorkItemDraft((current) => ({ ...current, assignee_id: event.target.value }))} disabled={archived} />
            <ActionButton type="submit" disabled={saving || archived || !workItemDraft.title.trim()}>Add task</ActionButton>
          </form>
          <List
            items={projectWorkItems}
            empty="No work items."
            renderItem={(item) => (
              <div key={item.id} className="artifact-row">
                <strong>{item.title}</strong>
                <span>{item.type} · {item.status}</span>
              </div>
            )}
          />
        </SimpleSection>

        <SimpleSection title="Risks">
          <form onSubmit={handleCreateRisk} className="stack">
            <input placeholder="Risk title" value={riskDraft.title} onChange={(event) => setRiskDraft((current) => ({ ...current, title: event.target.value }))} disabled={archived} />
            <select value={riskDraft.severity} onChange={(event) => setRiskDraft((current) => ({ ...current, severity: event.target.value }))} disabled={archived}>
              {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((severity) => (
                <option key={severity} value={severity}>{severity}</option>
              ))}
            </select>
            <ActionButton type="submit" disabled={saving || archived || !riskDraft.title.trim()}>Add risk</ActionButton>
          </form>
          <List
            items={projectRisks}
            empty="No risks."
            renderItem={(item) => (
              <div key={item.id} className="artifact-row">
                <strong>{item.title}</strong>
                <span>{item.severity} · {item.status}</span>
              </div>
            )}
          />
        </SimpleSection>

        <SimpleSection title="Members">
          <List
            items={projectMembers}
            empty="No project members."
            renderItem={(item) => (
              <div key={item.id} className="artifact-row">
                <strong>{item.user_id}</strong>
                <span>{item.role}</span>
              </div>
            )}
          />
        </SimpleSection>

        <SimpleSection title="Roadmap">
          <pre className="code-block">{JSON.stringify(projectRoadmap || {}, null, 2)}</pre>
        </SimpleSection>

        <SimpleSection title="Project activity">
          <List
            items={projectActivity.slice(0, 8)}
            empty="No project activity yet."
            renderItem={(item) => (
              <div key={item.id || item.event_type} className="artifact-row">
                <strong>{item.event_type}</strong>
                <span>{item.timestamp || item.created_at || ""}</span>
              </div>
            )}
          />
        </SimpleSection>
      </div>
    );
  };

  const renderRequestDetail = () => {
    if (!requestDetail) {
      return <p className="empty-state">Request not loaded.</p>;
    }
    const transitions = requestDetail.available_transitions || [];
    const archived = requestDetail.status === "ARCHIVED";
    return (
      <div className="grid two-col">
        <SimpleSection title="Request detail" aside={<span>{requestDetail.status}</span>}>
          <form onSubmit={handleUpdateRequest} className="stack">
            <label className="field">
              <span>Title</span>
              <input value={requestDraft.title} onChange={(event) => setRequestDraft((current) => ({ ...current, title: event.target.value }))} />
            </label>
            <label className="field">
              <span>Description</span>
              <textarea value={requestDraft.description} onChange={(event) => setRequestDraft((current) => ({ ...current, description: event.target.value }))} rows={4} />
            </label>
            <label className="field">
              <span>Project</span>
              <select value={requestDraft.project_id} onChange={(event) => setRequestDraft((current) => ({ ...current, project_id: event.target.value }))}>
                <option value="">No project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>
            </label>
            <ActionButton type="submit" disabled={saving || archived}>Save request</ActionButton>
          </form>
          <div className="inline-actions">
            <ActionButton disabled={saving || requestDetail.status !== "DRAFT"} onClick={handleSubmitRequest}>Submit request</ActionButton>
            <select value={transitionTarget} onChange={(event) => setTransitionTarget(event.target.value)} aria-label="Request transition">
              <option value="">Transition to...</option>
              {transitions.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
            <ActionButton disabled={saving || !transitionTarget} onClick={handleTransitionRequest}>Move status</ActionButton>
          </div>
        </SimpleSection>

        <SimpleSection title="Review assignment">
          <form onSubmit={handleAddAssignment} className="stack">
            <input placeholder="Reviewer" value={assignmentDraft.assignee_id} onChange={(event) => setAssignmentDraft((current) => ({ ...current, assignee_id: event.target.value }))} />
            <input placeholder="Assignment role" value={assignmentDraft.assignment_role} onChange={(event) => setAssignmentDraft((current) => ({ ...current, assignment_role: event.target.value }))} />
            <ActionButton type="submit" disabled={saving || !assignmentDraft.assignee_id.trim()}>Assign reviewer</ActionButton>
          </form>
          <List
            items={requestAssignments}
            empty="No assignments."
            renderItem={(item) => (
              <div key={item.id} className="artifact-row">
                <strong>{item.assignee_id}</strong>
                <span>{item.assignment_role} · {item.status}</span>
              </div>
            )}
          />
        </SimpleSection>

        <SimpleSection title="Attachments">
          <form onSubmit={handleAddAttachment} className="stack">
            <input placeholder="Filename" value={attachmentDraft.filename} onChange={(event) => setAttachmentDraft((current) => ({ ...current, filename: event.target.value }))} />
            <input placeholder="Content type" value={attachmentDraft.content_type} onChange={(event) => setAttachmentDraft((current) => ({ ...current, content_type: event.target.value }))} />
            <textarea placeholder="Content" value={attachmentDraft.content} onChange={(event) => setAttachmentDraft((current) => ({ ...current, content: event.target.value }))} rows={4} />
            <ActionButton type="submit" disabled={saving || !attachmentDraft.filename.trim()}>Upload attachment</ActionButton>
          </form>
          <List
            items={requestAttachments}
            empty="No attachments."
            renderItem={(item) => (
              <div key={item.id} className="artifact-row">
                <strong>{item.filename}</strong>
                <span>{item.status} · {item.content_type}</span>
              </div>
            )}
          />
        </SimpleSection>

        <SimpleSection title="Comments">
          <form onSubmit={handleAddComment} className="stack">
            <textarea placeholder="Write a comment" value={commentDraft} onChange={(event) => setCommentDraft(event.target.value)} rows={4} />
            <ActionButton type="submit" disabled={saving || !commentDraft.trim()}>Add comment</ActionButton>
          </form>
          <List
            items={requestComments}
            empty="No comments."
            renderItem={(item) => (
              <div key={item.id} className="artifact-row">
                <strong>{item.author_id}</strong>
                <span>{item.body}</span>
              </div>
            )}
          />
        </SimpleSection>

        <SimpleSection title="History">
          <List
            items={requestHistory}
            empty="No history."
            renderItem={(item) => (
              <div key={item.id || `${item.previous_status}-${item.new_status}`} className="artifact-row">
                <strong>{item.previous_status || "Draft"} → {item.new_status || requestDetail.status}</strong>
                <span>{item.reason || "Status change"}</span>
              </div>
            )}
          />
        </SimpleSection>
      </div>
    );
  };

  return (
    <div className="app-shell novacodepro-ncp003" data-testid="ncp003-authenticated-shell">
      <a className="skip-link" href="#ncp003-main">Skip to content</a>
      <header className="ncp003-topbar">
        <div className="brand-block">
          <img className="brand-logo" src="/brand/NOVACODEPRO.webp" alt="NovaCodePro" />
          <div>
            <strong>NovaCodePro</strong>
            <span>Governed product workspace</span>
          </div>
        </div>
        <div className="ncp003-topbar-actions">
          <span className="ncp003-environment">Local · Secure</span>
          <button type="button" aria-label="Open navigation" className="ncp003-mobile-menu" onClick={() => setMobileNavigationOpen((value) => !value)}>☰</button>
          <button type="button" className="ncp003-user-menu" onClick={onLogout} aria-label="Sign out">
            <span>{(session?.display_name || "User").slice(0, 1)}</span>
            <span><strong>{session?.display_name || "User"}</strong><small>{session?.active_role || "Member"}</small></span>
          </button>
        </div>
      </header>

      <StateBanner state={loadState} error={loadError || actionError} />

      <div className="ncp003-layout">
        <aside className={mobileNavigationOpen ? "ncp003-sidebar open" : "ncp003-sidebar"} aria-label="Application navigation">
          <div className="ncp003-sidebar-workspace"><small>Current workspace</small><strong>{workspaceLabel}</strong><span>{session?.organization?.name || session?.organization || "NovaTech"}</span></div>
          <nav>
            {[
              ["Overview", "/novacodepro/dashboard"],
              ["Workspace", "/novacodepro/workspace"],
              ["Projects", "/novacodepro/projects"],
              ["Requests", "/novacodepro/requests"],
              ["Activity", "/novacodepro/workspace/activity"],
              ["Notifications", "/novacodepro/workspace/notifications"],
            ].map(([label, path]) => <button key={path} type="button" aria-current={pathname === path ? "page" : undefined} onClick={() => { setMobileNavigationOpen(false); navigate(path); }}><span aria-hidden="true">{label.slice(0, 1)}</span>{label}</button>)}
          </nav>
          <div className="ncp003-sidebar-trust"><span>✓</span><div><strong>Protected by NovaID</strong><small>Tenant and workspace enforced</small></div></div>
        </aside>

        <main id="ncp003-main" className="ncp003-main" tabIndex={-1}>
          <header className="ncp003-page-header">
            <div>
              <p className="ncp003-breadcrumb">NovaCodePro / {route.section}</p>
              <h1>{route.section === "projects" ? "Projects" : route.section === "requests" ? "Requests" : "Workspace"}</h1>
              <p>{route.section === "projects" ? "Plan, govern, and deliver your product portfolio." : route.section === "requests" ? "Capture ideas, requirements, change requests, incidents, and delivery work." : "Your governed home for teams, work, approvals, and traceability."}</p>
            </div>
            {route.section === "projects" && !projectId && canCreateProject ? <button type="button" className="primary-action" onClick={() => setComposerOpen(true)}>Create project</button> : null}
            {route.section === "requests" && !requestId && canCreateRequest ? <button type="button" className="primary-action" onClick={() => setComposerOpen(true)}>Create request</button> : null}
          </header>

        {loadState === "ready" ? (
          <>
            {route.section === "workspace" ? renderWorkspaceHome() : null}
            {route.section === "projects" && !projectId ? (
              <div data-testid="projects-page" className="ncp003-page-stack">
                <section className="ncp003-metrics" aria-label="Project summary">
                  {[["Total projects", projects.length], ["Active", projects.filter((item) => item.status === "ACTIVE").length], ["At risk", projects.filter((item) => item.health === "AT_RISK").length], ["Recently updated", projects.slice(0, 7).length]].map(([label, value]) => <article className="ncp003-metric" key={label}><span>{label}</span><strong>{value}</strong><small>Current workspace</small></article>)}
                </section>
                <section className="ncp003-panel">
                  <div className="ncp003-toolbar">
                    <label><span className="sr-only">Search projects</span><input type="search" placeholder="Search projects" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} /></label>
                    <label><span className="sr-only">Project status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="ALL">All statuses</option><option value="ACTIVE">Active</option><option value="ARCHIVED">Archived</option></select></label>
                    {(searchQuery || statusFilter !== "ALL") ? <button type="button" onClick={() => { setSearchQuery(""); setStatusFilter("ALL"); }}>Clear filters</button> : null}
                  </div>
                  <div className="ncp003-project-grid">
                    {filteredProjects.map((item) => <button key={item.id} type="button" className="ncp003-project-card" onClick={() => navigate(`/novacodepro/projects/${encodeURIComponent(item.id)}`)}><span className="ncp003-card-top"><b>{item.status || "ACTIVE"}</b><small>{item.updated_at || item.created_at || "Recently updated"}</small></span><strong>{item.name}</strong><p>{item.description || "No project description has been added."}</p><span className="ncp003-card-meta"><small>Owner</small><b>{item.owner_id || item.created_by || "Workspace team"}</b></span><span className="ncp003-progress"><i style={{ width: item.status === "ARCHIVED" ? "100%" : "48%" }} /></span></button>)}
                    {!filteredProjects.length ? <div className="ncp003-empty"><strong>{projects.length ? "No projects match these filters." : "Create your first governed project."}</strong><span>Projects connect requests, delivery activity, evidence, and approvals.</span></div> : null}
                  </div>
                </section>
                {composerOpen ? <section className="ncp003-composer" role="dialog" aria-modal="true" aria-labelledby="create-project-title"><div className="ncp003-composer-head"><div><p className="section-label">New governed work</p><h2 id="create-project-title">Create project</h2></div><button type="button" aria-label="Close create project" onClick={() => setComposerOpen(false)}>×</button></div><form onSubmit={handleCreateProject} className="stack"><label className="field"><span>Project name</span><input autoFocus required value={projectDraft.name} onChange={(event) => setProjectDraft((current) => ({ ...current, name: event.target.value }))} /></label><label className="field"><span>Description</span><textarea rows={4} value={projectDraft.description} onChange={(event) => setProjectDraft((current) => ({ ...current, description: event.target.value }))} /></label><label className="field"><span>Owner</span><input value={projectDraft.owner_id} onChange={(event) => setProjectDraft((current) => ({ ...current, owner_id: event.target.value }))} /></label><ActionButton type="submit" disabled={saving || !projectDraft.name.trim()}>{saving ? "Creating…" : "Create project"}</ActionButton></form></section> : null}
              </div>
            ) : null}
            {route.section === "projects" && projectId ? renderProjectDetail() : null}
            {route.section === "requests" && !requestId ? (
              <div data-testid="requests-page" className="ncp003-page-stack">
                <section className="ncp003-metrics" aria-label="Request pipeline summary">
                  {["DRAFT", "SUBMITTED", "ANALYSING", "APPROVED"].map((status) => <article className="ncp003-metric" key={status}><span>{status === "ANALYSING" ? "Under review" : status.toLowerCase()}</span><strong>{requests.filter((item) => item.status === status).length}</strong><small>Governed intake</small></article>)}
                </section>
                <section className="ncp003-panel">
                  <div className="ncp003-toolbar"><label><span className="sr-only">Search requests</span><input type="search" placeholder="Search requests" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} /></label><label><span className="sr-only">Request status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="ALL">All statuses</option>{["DRAFT", "SUBMITTED", "ANALYSING", "APPROVED", "REJECTED", "COMPLETED"].map((status) => <option key={status}>{status}</option>)}</select></label></div>
                  <div className="ncp003-request-table" role="table" aria-label="Requests"><div className="ncp003-request-row heading" role="row"><span>Request</span><span>Type</span><span>Priority</span><span>Status</span><span>Updated</span></div>{filteredRequests.map((item) => <button type="button" role="row" className="ncp003-request-row" key={item.id} onClick={() => navigate(`/novacodepro/requests/${encodeURIComponent(item.id)}`)}><span><strong>{item.title}</strong><small>{item.id}</small></span><span>{item.request_type || "TEXT"}</span><span>{item.priority || "MEDIUM"}</span><span><b>{item.status}</b></span><span>{item.updated_at || item.created_at || "Recently"}</span></button>)}</div>
                  {!filteredRequests.length ? <div className="ncp003-empty"><strong>{requests.length ? "No requests match these filters." : "Your request pipeline is ready."}</strong><span>Capture ideas, requirements, incidents, and governed delivery work.</span></div> : null}
                </section>
                {composerOpen ? <section className="ncp003-composer" role="dialog" aria-modal="true" aria-labelledby="create-request-title"><div className="ncp003-composer-head"><div><p className="section-label">Governed intake</p><h2 id="create-request-title">Create request</h2></div><button type="button" aria-label="Close create request" onClick={() => setComposerOpen(false)}>×</button></div><form onSubmit={handleCreateRequest} className="stack"><label className="field"><span>Title</span><input autoFocus required value={requestDraft.title} onChange={(event) => setRequestDraft((current) => ({ ...current, title: event.target.value }))} /></label><label className="field"><span>Request type</span><select value={requestDraft.request_type} onChange={(event) => setRequestDraft((current) => ({ ...current, request_type: event.target.value }))}><option value="TEXT">Product request</option><option value="CHANGE">Change request</option><option value="INCIDENT">Incident</option></select></label><label className="field"><span>Description</span><textarea required rows={5} value={requestDraft.description} onChange={(event) => setRequestDraft((current) => ({ ...current, description: event.target.value }))} /></label><label className="field"><span>Related project</span><select value={requestDraft.project_id} onChange={(event) => setRequestDraft((current) => ({ ...current, project_id: event.target.value }))}><option value="">No project</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label><label className="field"><span>Priority</span><select value={requestDraft.priority} onChange={(event) => setRequestDraft((current) => ({ ...current, priority: event.target.value }))}>{["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((value) => <option key={value}>{value}</option>)}</select></label><ActionButton type="submit" disabled={saving || !requestDraft.title.trim() || !requestDraft.description.trim()}>{saving ? "Saving…" : "Create draft"}</ActionButton></form></section> : null}
              </div>
            ) : null}
            {route.section === "requests" && requestId ? renderRequestDetail() : null}
            {route.section === "workspace" && route.subRoute === "activity" ? (
              <SimpleSection title="Workspace activity">
                <List
                  items={workspaceActivity}
                  empty="No activity."
                  renderItem={(item) => (
                    <div key={item.id || item.event_type} className="artifact-row">
                      <strong>{item.event_type}</strong>
                      <span>{item.timestamp || item.created_at || ""}</span>
                    </div>
                  )}
                />
              </SimpleSection>
            ) : null}
            {route.section === "workspace" && route.subRoute === "tasks" ? (
              <SimpleSection title="Workspace tasks">
                <List
                  items={workspaceTasks}
                  empty="No tasks."
                  renderItem={(item) => (
                    <div key={item.id} className="artifact-row">
                      <strong>{item.title}</strong>
                      <span>{item.status}</span>
                    </div>
                  )}
                />
              </SimpleSection>
            ) : null}
            {route.section === "workspace" && route.subRoute === "approvals" ? (
              <SimpleSection title="Workspace approvals">
                <List
                  items={workspaceApprovals}
                  empty="No approvals."
                  renderItem={(item) => (
                    <div key={item.id} className="artifact-row">
                      <strong>{item.assignment_role}</strong>
                      <span>{item.status}</span>
                    </div>
                  )}
                />
              </SimpleSection>
            ) : null}
            {route.section === "workspace" && route.subRoute === "favorites" ? (
              <SimpleSection title="Workspace favorites">
                <List
                  items={workspaceFavorites}
                  empty="No favorites."
                  renderItem={(item) => (
                    <div key={item.id} className="artifact-row">
                      <strong>{item.label}</strong>
                      <span>{item.route}</span>
                    </div>
                  )}
                />
              </SimpleSection>
            ) : null}
            {route.section === "workspace" && route.subRoute === "notifications" ? (
              <SimpleSection title="Workspace notifications">
                <List
                  items={notifications}
                  empty="No notifications."
                  renderItem={(item) => (
                    <div key={item.id} className="artifact-row">
                      <strong>{item.title}</strong>
                      <span>{item.status}</span>
                    </div>
                  )}
                />
              </SimpleSection>
            ) : null}
            {route.section === "workspace" && route.subRoute === "team" ? (
              <SimpleSection title="Workspace team">
                <List
                  items={workspaceMembers}
                  empty="No members."
                  renderItem={(item) => (
                    <div key={item.id} className="artifact-row">
                      <strong>{item.user_id}</strong>
                      <span>{item.role}</span>
                    </div>
                  )}
                />
              </SimpleSection>
            ) : null}
            {route.section === "workspace" && route.subRoute === "settings" ? (
              <SimpleSection title="Workspace settings">
                <pre className="code-block">{JSON.stringify(workspaceDetail?.settings || {}, null, 2)}</pre>
              </SimpleSection>
            ) : null}
            {route.section === "projects" && projectId ? null : null}
            {route.section === "requests" && requestId ? null : null}
          </>
        ) : null}
        </main>
      </div>
    </div>
  );
}
