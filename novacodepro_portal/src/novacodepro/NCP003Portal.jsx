import React, { useEffect, useMemo, useState } from "react";

import { createNovaCodeProNcp003Api } from "./api/novacodeproNcp003Api.js";

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

export function NCP003Portal({ session, pathname, navigate, baseUrl = "", onLogout }) {
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

  const workspaceId = activeWorkspaceId || session?.workspace_id || session?.workspace?.id || "";
  const projectId = route.section === "projects" ? route.id : null;
  const requestId = route.section === "requests" ? route.id : null;

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
        setLoadState(error?.code === "session_required" ? "unauthorized" : error?.code === "workspace_forbidden" ? "forbidden" : error?.code === "workspace_not_found" || error?.code === "project_not_found" || error?.code === "request_not_found" ? "not_found" : error?.code === "timeout" ? "timeout" : error?.retryable === false ? "error" : "service_unavailable");
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [client, workspaceId, projectId, requestId]);

  const selectWorkspace = async (nextWorkspaceId) => {
    setActionError(null);
    try {
      const result = await client.selectWorkspace(nextWorkspaceId);
      setActiveWorkspaceId(result?.session?.workspace_id || nextWorkspaceId);
      navigate("/novacodepro/workspace");
    } catch (error) {
      setActionError(error);
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

  const renderWorkspaceHome = () => (
    <div className="grid two-col">
      <SimpleSection title="Workspace selection" aside={<span>{workspaceLabel}</span>}>
        <label className="field">
          <span>Active workspace</span>
          <select value={activeWorkspaceId} onChange={(event) => selectWorkspace(event.target.value)} aria-label="Active workspace">
            {workspaceItems.map((workspace) => (
              <option key={workspace.id} value={workspace.id}>
                {workspace.name}
              </option>
            ))}
          </select>
        </label>
        <p className="helper-text">Selecting a workspace updates the server-side session and clears stale workspace context.</p>
      </SimpleSection>

      <SimpleSection title="Create project">
        <form onSubmit={handleCreateProject} className="stack">
          <label className="field">
            <span>Project name</span>
            <input value={projectDraft.name} onChange={(event) => setProjectDraft((current) => ({ ...current, name: event.target.value }))} required />
          </label>
          <label className="field">
            <span>Description</span>
            <textarea value={projectDraft.description} onChange={(event) => setProjectDraft((current) => ({ ...current, description: event.target.value }))} rows={4} />
          </label>
          <label className="field">
            <span>Owner</span>
            <input value={projectDraft.owner_id} onChange={(event) => setProjectDraft((current) => ({ ...current, owner_id: event.target.value }))} />
          </label>
          <ActionButton type="submit" disabled={saving || !projectDraft.name.trim()}>Create project</ActionButton>
        </form>
      </SimpleSection>

      <SimpleSection title="Create request draft">
        <form onSubmit={handleCreateRequest} className="stack">
          <label className="field">
            <span>Title</span>
            <input value={requestDraft.title} onChange={(event) => setRequestDraft((current) => ({ ...current, title: event.target.value }))} required />
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
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <ActionButton type="submit" disabled={saving || !requestDraft.title.trim()}>Create request draft</ActionButton>
        </form>
      </SimpleSection>

      <SimpleSection title="Recent activity">
        <List
          items={workspaceActivity.slice(0, 5)}
          empty="No workspace activity yet."
          renderItem={(item) => (
            <div key={item.id || item.event_type} className="artifact-row">
              <strong>{item.event_type}</strong>
              <span>{item.timestamp || item.created_at || ""}</span>
            </div>
          )}
        />
      </SimpleSection>

      <SimpleSection title="Notifications">
        <List
          items={workspaceNotifications.slice(0, 5)}
          empty="No notifications."
          renderItem={(item) => (
            <div key={item.id} className="artifact-row">
              <strong>{item.title}</strong>
              <span>{item.status}</span>
            </div>
          )}
        />
      </SimpleSection>
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
    <div className="app-shell novacodepro-ncp003">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">N</div>
          <div>
            <p className="eyebrow">NovaCodePro Internal Development Platform</p>
            <strong>NCP-003 Workspace, Projects and Requests</strong>
          </div>
        </div>
        <div className="topbar-actions">
          <button type="button" className="toolbar-chip" onClick={() => navigate("/novacodepro/workspace")}>Workspace</button>
          <button type="button" className="toolbar-chip" onClick={() => navigate("/novacodepro/projects")}>Projects</button>
          <button type="button" className="toolbar-chip" onClick={() => navigate("/novacodepro/requests")}>Requests</button>
          <button type="button" className="toolbar-chip danger" onClick={onLogout}>Log out</button>
        </div>
      </header>

      <StateBanner state={loadState} error={loadError || actionError} />

      <main className="workspace-shell">
        <section className="workspace-band">
          <div className="workspace-band-header">
            <div>
              <p className="section-label">Authenticated session</p>
              <h1>{session?.display_name || session?.user?.display_name || session?.user?.username || "User"}</h1>
              <p>{session?.organization?.name || session?.organization || "NovaTech"} · {workspaceLabel}</p>
            </div>
            <div className="workspace-summary">
              <span>{session?.active_role || session?.user?.active_role || "Member"}</span>
              <span>{workspaceId || "workspace-required"}</span>
            </div>
          </div>
          <div className="workspace-tabs" role="tablist" aria-label="NovaCodePro navigation">
            {[
              { label: "Workspace", route: "/novacodepro/workspace" },
              { label: "Projects", route: "/novacodepro/projects" },
              { label: "Requests", route: "/novacodepro/requests" },
              { label: "Activity", route: "/novacodepro/workspace/activity" },
              { label: "Notifications", route: "/novacodepro/workspace/notifications" },
            ].map((item) => (
              <button key={item.route} type="button" className="workspace-tab" onClick={() => navigate(item.route)}>
                {item.label}
              </button>
            ))}
          </div>
        </section>

        {loadState === "ready" ? (
          <>
            {route.section === "workspace" ? renderWorkspaceHome() : null}
            {route.section === "projects" && !projectId ? (
              <div className="grid two-col">
                <SimpleSection title="Projects">
                  <List
                    items={projects}
                    empty="No projects yet."
                    renderItem={(item) => (
                      <button key={item.id} type="button" className="list-link" onClick={() => navigate(`/novacodepro/projects/${encodeURIComponent(item.id)}`)}>
                        <strong>{item.name}</strong>
                        <span>{item.status}</span>
                      </button>
                    )}
                  />
                </SimpleSection>
                <SimpleSection title="Create project">
                  <form onSubmit={handleCreateProject} className="stack">
                    <input placeholder="Project name" value={projectDraft.name} onChange={(event) => setProjectDraft((current) => ({ ...current, name: event.target.value }))} />
                    <textarea placeholder="Description" rows={4} value={projectDraft.description} onChange={(event) => setProjectDraft((current) => ({ ...current, description: event.target.value }))} />
                    <ActionButton type="submit" disabled={saving || !projectDraft.name.trim()}>Create project</ActionButton>
                  </form>
                </SimpleSection>
              </div>
            ) : null}
            {route.section === "projects" && projectId ? renderProjectDetail() : null}
            {route.section === "requests" && !requestId ? (
              <div className="grid two-col">
                <SimpleSection title="Requests">
                  <List
                    items={requests}
                    empty="No requests yet."
                    renderItem={(item) => (
                      <button key={item.id} type="button" className="list-link" onClick={() => navigate(`/novacodepro/requests/${encodeURIComponent(item.id)}`)}>
                        <strong>{item.title}</strong>
                        <span>{item.status}</span>
                      </button>
                    )}
                  />
                </SimpleSection>
                <SimpleSection title="Request draft">
                  <form onSubmit={handleCreateRequest} className="stack">
                    <input placeholder="Title" value={requestDraft.title} onChange={(event) => setRequestDraft((current) => ({ ...current, title: event.target.value }))} />
                    <textarea placeholder="Description" rows={4} value={requestDraft.description} onChange={(event) => setRequestDraft((current) => ({ ...current, description: event.target.value }))} />
                    <ActionButton type="submit" disabled={saving || !requestDraft.title.trim()}>Create draft</ActionButton>
                  </form>
                </SimpleSection>
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
  );
}
