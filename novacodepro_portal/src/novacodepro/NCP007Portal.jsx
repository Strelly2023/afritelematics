import React, { useEffect, useMemo, useState } from "react";

import { createNovaCodeProNcp007Api } from "./api/novacodeproNcp007Api.js";

function parseRoute(pathname) {
  const parts = String(pathname || "").replace(/\/+$/, "").split("/").filter(Boolean);
  if (parts[0] !== "novacodepro" || parts[1] !== "development") {
    return { section: "home", id: "", subRoute: "/" };
  }
  return {
    section: parts[2] || "home",
    id: parts[3] || "",
    subRoute: `/${parts.slice(4).join("/")}`.replace(/\/+$/, "") || "/",
  };
}

function StateBanner({ state, error }) {
  if (state === "ready") return null;
  const label = {
    loading: "Loading",
    empty: "Empty",
    forbidden: "Forbidden",
    not_found: "Not found",
    offline: "Offline",
    timeout: "Timeout",
    service_unavailable: "Service unavailable",
    version_conflict: "Version conflict",
    validation_failed: "Validation failed",
    approval_required: "Approval required",
  }[state] || "Error";
  return (
    <div className={`state-banner ${state || "error"}`} role="status" aria-live="polite">
      <strong>{label}</strong>
      <span>{error?.message || error?.code || "Request in progress."}</span>
    </div>
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

function Field({ label, value, onChange, type = "text", placeholder = "", readOnly = false }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input type={type} value={value ?? ""} onChange={onChange} placeholder={placeholder} readOnly={readOnly} />
    </label>
  );
}

function TextAreaField({ label, value, onChange, placeholder = "", readOnly = false, rows = 4 }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <textarea value={value ?? ""} onChange={onChange} placeholder={placeholder} readOnly={readOnly} rows={rows} />
    </label>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <select value={value ?? ""} onChange={onChange}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
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

function List({ items, empty, renderItem }) {
  if (!items.length) return <p className="empty-state">{empty}</p>;
  return <div className="stack">{items.map(renderItem)}</div>;
}

function ActionButton({ children, onClick, tone = "primary", disabled = false }) {
  return (
    <button type="button" className={`${tone}-action`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

export function NCP007Portal({ session, pathname, navigate, baseUrl = "", onLogout }) {
  const client = useMemo(() => createNovaCodeProNcp007Api({ baseUrl, fetchImpl: globalThis.fetch }), [baseUrl]);
  const route = useMemo(() => parseRoute(pathname), [pathname]);
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
  const [selectedSession, setSelectedSession] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [generationRequest, setGenerationRequest] = useState(null);
  const [changeSet, setChangeSet] = useState(null);
  const [validationRuns, setValidationRuns] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [repoStatus, setRepoStatus] = useState(null);
  const [repoTree, setRepoTree] = useState([]);
  const [repoFile, setRepoFile] = useState(null);
  const [repoSearch, setRepoSearch] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [commandRun, setCommandRun] = useState(null);
  const [commitProposal, setCommitProposal] = useState(null);
  const [searchQuery, setSearchQuery] = useState("development");
  const [workspaceDraft, setWorkspaceDraft] = useState({ name: "Development Workspace", description: "Governed code generation workspace", repository_id: "", default_branch: "main" });
  const [sessionDraft, setSessionDraft] = useState({ objective: "Deliver governed repository change", branch_name: "feature/ncp007-governed-code" });
  const [taskDraft, setTaskDraft] = useState({ title: "Implement governed code flow", description: "Build or modify repository code through policy controls.", task_type: "FEATURE", risk_level: "LOW" });
  const [generationDraft, setGenerationDraft] = useState({ instruction: "Implement governed code generation", target_files: "novacodepro_portal/src/novacodepro/NCP007Portal.jsx" });
  const [validationDraft, setValidationDraft] = useState({ validation_type: "FORMAT", command: "python3 -m compileall afritech" });
  const [reviewDraft, setReviewDraft] = useState({ reviewer_id: session?.user?.id || "tech-lead", reviewer_type: "HUMAN", summary: "Review governed change set" });
  const [approvalDraft, setApprovalDraft] = useState({ required_role: "TECH_LEAD", reason: "Governed approval required" });
  const [commandDraft, setCommandDraft] = useState({ command: "python3 -m compileall afritech" });
  const [repositoryPath, setRepositoryPath] = useState("afritech");

  async function reload({ workspaceId = selectedWorkspaceId, sessionId = selectedSession?.id, changeSetId = changeSet?.id } = {}) {
    if (!workspaceId) {
      setState("empty");
      return;
    }
    setState("loading");
    setError(null);
    try {
      const [workspaceList, status, tree, sessions, tasks, evidenceList, timelineList] = await Promise.all([
        client.listWorkspaces(),
        client.repositoryStatus(workspaceId),
        client.repositoryTree(workspaceId, repositoryPath),
        sessionId ? client.getSession(sessionId).then((item) => [item]) : Promise.resolve([]),
        sessionId ? client.listSessionTasks(sessionId) : Promise.resolve([]),
        changeSetId ? client.getEvidence(changeSetId) : Promise.resolve([]),
        sessionId ? client.getTimeline(sessionId) : Promise.resolve([]),
      ]);
      setWorkspaces(workspaceList);
      setRepoStatus(status);
      setRepoTree(tree?.tree || []);
      setSelectedSession(sessions[0] || selectedSession);
      setTimeline(timelineList || []);
      setEvidence(evidenceList || []);
      if (tasks.length && !selectedTask) {
        setSelectedTask(tasks[0]);
      }
      if (!workspaceList.length) {
        setState("empty");
      } else {
        setState("ready");
      }
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  useEffect(() => {
    void reload({ workspaceId: selectedWorkspaceId || workspaces[0]?.id });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWorkspaceId, repositoryPath]);

  useEffect(() => {
    if (!selectedWorkspaceId && workspaces[0]?.id) {
      setSelectedWorkspaceId(workspaces[0].id);
    }
  }, [workspaces, selectedWorkspaceId]);

  async function selectWorkspace(workspaceId) {
    try {
      await client.selectWorkspace(workspaceId);
      setSelectedWorkspaceId(workspaceId);
      await reload({ workspaceId });
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function createWorkspace() {
    try {
      const created = await client.createWorkspace(workspaceDraft);
      setWorkspaces((current) => [created, ...current]);
      setSelectedWorkspaceId(created.id);
      setState("ready");
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function createSession() {
    if (!selectedWorkspaceId) return;
    try {
      const created = await client.createSession(selectedWorkspaceId, sessionDraft);
      setSelectedSession(created);
      setTimeline([]);
      setState("ready");
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function createTask() {
    if (!selectedSession?.id) return;
    try {
      const created = await client.createTask(selectedSession.id, taskDraft);
      setSelectedTask(created);
      setState("ready");
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function generateChangeSet() {
    if (!selectedTask?.id) return;
    try {
      const created = await client.generateTask(
        selectedTask.id,
        {
          instruction: generationDraft.instruction,
          target_files: generationDraft.target_files.split(",").map((item) => item.trim()).filter(Boolean),
          generation_mode: "MODIFY",
        },
        `ncp007-${selectedTask.id}`,
      );
      setGenerationRequest(created.request);
      setChangeSet(created.change_set);
      setValidationRuns([]);
      setReviews([]);
      setApprovals([]);
      setEvidence([]);
      await reload({ workspaceId: selectedWorkspaceId, sessionId: selectedSession?.id, changeSetId: created.change_set?.id });
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function runValidation() {
    if (!changeSet?.id) return;
    try {
      const created = await client.createValidation(changeSet.id, {
        validation_type: validationDraft.validation_type,
        command: validationDraft.command.split(" ").filter(Boolean),
      });
      setValidationRuns((current) => [created, ...current]);
      await reload({ workspaceId: selectedWorkspaceId, sessionId: selectedSession?.id, changeSetId: changeSet.id });
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function createReview() {
    if (!changeSet?.id) return;
    try {
      const created = await client.createReview(changeSet.id, reviewDraft);
      setReviews((current) => [created, ...current]);
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function requestApproval() {
    if (!changeSet?.id) return;
    try {
      const created = await client.requestApproval(changeSet.id, approvalDraft);
      setApprovals((current) => [created, ...current]);
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function approveLatest() {
    if (!approvals[0]?.id) return;
    try {
      const updated = await client.approveApproval(approvals[0].id, { reason: approvalDraft.reason });
      setApprovals((current) => [updated, ...current.slice(1)]);
      await reload({ workspaceId: selectedWorkspaceId, sessionId: selectedSession?.id, changeSetId: changeSet?.id });
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function createCommitProposal() {
    if (!changeSet?.id) return;
    try {
      const created = await client.createCommitProposal(changeSet.id, { branch_name: "feature/ncp007-governed-code", commit_message: "feat(ncp-007): governed development changes" });
      setCommitProposal(created);
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function executeCommitProposal() {
    if (!commitProposal?.id) return;
    try {
      const created = await client.executeCommitProposal(commitProposal.id);
      setCommitProposal(created);
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function executeCommand() {
    if (!selectedSession?.id) return;
    try {
      const created = await client.executeCommand(selectedSession.id, { command: commandDraft.command.split(" ").filter(Boolean), working_directory: "." });
      setCommandRun(created);
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  async function refreshRepositorySearch() {
    if (!selectedWorkspaceId) return;
    try {
      const result = await client.repositorySearch(selectedWorkspaceId, searchQuery, repositoryPath);
      setRepoSearch(result.matches || []);
    } catch (cause) {
      setError(cause);
      setState(mapErrorState(cause));
    }
  }

  const workspaceOptions = [
    { value: "", label: "Select workspace" },
    ...workspaces.map((workspace) => ({ value: workspace.id, label: workspace.name || workspace.id })),
  ];

  const selectedWorkspace = workspaces.find((workspace) => workspace.id === selectedWorkspaceId) || null;

  return (
    <main className="novacodepro-development-studio">
      <header className="page-header">
        <div>
          <p className="eyebrow">NovaCodePro internal development platform</p>
          <h1>Development Studio</h1>
          <p>Governed repository browser, code generation, validation, review, approvals, and evidence.</p>
        </div>
        <div className="toolbar">
          <button type="button" className="toolbar-chip" onClick={() => navigate("/novacodepro/development/workspaces")}>Workspaces</button>
          <button type="button" className="toolbar-chip" onClick={() => navigate("/novacodepro/development/sessions")}>Sessions</button>
          <button type="button" className="toolbar-chip" onClick={() => navigate("/novacodepro/development/change-sets")}>Change sets</button>
          <button type="button" className="toolbar-chip" onClick={() => navigate("/novacodepro/development/approvals")}>Approvals</button>
          <button type="button" className="toolbar-chip" onClick={() => onLogout?.()}>Logout</button>
        </div>
      </header>

      <StateBanner state={state} error={error} />

      <section className="context-row">
        <Badge label="Tenant" value={session?.tenant?.id || session?.tenant_id || session?.organization?.id || "unknown"} />
        <Badge label="Workspace" value={selectedWorkspace?.name || selectedWorkspaceId || "none"} />
        <Badge label="Project" value={selectedSession?.project_id || selectedTask?.project_id || "none"} />
        <Badge label="Status" value={selectedSession?.status || changeSet?.status || "PLANNING"} />
        <Badge label="Correlation" value={changeSet?.correlation_id || selectedSession?.correlation_id || session?.correlation_id || session?.session_id || "n/a"} />
      </section>

      <div className="panel-grid">
        <Panel title="Development workspace" aside={<span>{workspaces.length} workspaces</span>}>
          <div className="grid-form">
            <SelectField label="Workspace" value={selectedWorkspaceId} onChange={(event) => setSelectedWorkspaceId(event.target.value)} options={workspaceOptions} />
            <Field label="Name" value={workspaceDraft.name} onChange={(event) => setWorkspaceDraft((current) => ({ ...current, name: event.target.value }))} />
            <Field label="Repository" value={workspaceDraft.repository_id} onChange={(event) => setWorkspaceDraft((current) => ({ ...current, repository_id: event.target.value }))} placeholder="Repository id or URL" />
            <TextAreaField label="Description" value={workspaceDraft.description} onChange={(event) => setWorkspaceDraft((current) => ({ ...current, description: event.target.value }))} />
            <div className="action-row">
              <ActionButton onClick={createWorkspace}>Create workspace</ActionButton>
              <ActionButton onClick={() => selectedWorkspaceId && selectWorkspace(selectedWorkspaceId)} tone="secondary">Persist selection</ActionButton>
            </div>
          </div>
          <List
            items={workspaces}
            empty="No development workspaces yet."
            renderItem={(workspace) => (
              <button key={workspace.id} type="button" className={workspace.id === selectedWorkspaceId ? "list-link active" : "list-link"} onClick={() => setSelectedWorkspaceId(workspace.id)}>
                <strong>{workspace.name}</strong>
                <span>{workspace.status} · {workspace.default_branch || "main"}</span>
              </button>
            )}
          />
        </Panel>

        <Panel title="Repository browser" aside={<span>{repoStatus?.head_sha || "unknown HEAD"}</span>}>
          <div className="grid-form">
            <Field label="Repository path" value={repositoryPath} onChange={(event) => setRepositoryPath(event.target.value)} />
            <Field label="Search query" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} />
            <div className="action-row">
              <ActionButton onClick={refreshRepositorySearch}>Search repository</ActionButton>
              <ActionButton onClick={() => selectedWorkspaceId && reload({ workspaceId: selectedWorkspaceId })} tone="secondary">Reload tree</ActionButton>
            </div>
          </div>
          <div className="split-columns">
            <div>
              <h3>Tree</h3>
              <List items={repoTree.slice(0, 14)} empty="No repository tree available." renderItem={(item) => <div key={item.path} className="stack-item"><strong>{item.path}</strong><span>{item.extension} · {item.size_bytes} bytes</span></div>} />
            </div>
            <div>
              <h3>Search</h3>
              <List items={repoSearch.slice(0, 10)} empty="No repository matches yet." renderItem={(item) => <div key={item.path} className="stack-item"><strong>{item.path}</strong><span>{item.snippet}</span></div>} />
            </div>
          </div>
          <p className="hint">HEAD: {repoStatus?.head_sha || "n/a"} · Branch: {repoStatus?.branch || "n/a"} · Dirty: {String(repoStatus?.dirty ?? false)}</p>
        </Panel>

        <Panel title="Session, task, and generation" aside={<span>{selectedSession?.status || "PLANNING"}</span>}>
          <div className="grid-form">
            <Field label="Objective" value={sessionDraft.objective} onChange={(event) => setSessionDraft((current) => ({ ...current, objective: event.target.value }))} />
            <Field label="Branch" value={sessionDraft.branch_name} onChange={(event) => setSessionDraft((current) => ({ ...current, branch_name: event.target.value }))} />
            <div className="action-row">
              <ActionButton onClick={createSession} disabled={!selectedWorkspaceId}>Create session</ActionButton>
              <ActionButton onClick={() => selectedSession?.id && reload({ workspaceId: selectedWorkspaceId, sessionId: selectedSession.id })} tone="secondary" disabled={!selectedSession?.id}>Refresh session</ActionButton>
            </div>

            <Field label="Task title" value={taskDraft.title} onChange={(event) => setTaskDraft((current) => ({ ...current, title: event.target.value }))} />
            <SelectField label="Task type" value={taskDraft.task_type} onChange={(event) => setTaskDraft((current) => ({ ...current, task_type: event.target.value }))} options={[{ value: "FEATURE", label: "Feature" }, { value: "BUG_FIX", label: "Bug fix" }, { value: "REFACTOR", label: "Refactor" }, { value: "TEST", label: "Test" }, { value: "DOCUMENTATION", label: "Documentation" }]} />
            <Field label="Risk level" value={taskDraft.risk_level} onChange={(event) => setTaskDraft((current) => ({ ...current, risk_level: event.target.value }))} />
            <TextAreaField label="Task description" value={taskDraft.description} onChange={(event) => setTaskDraft((current) => ({ ...current, description: event.target.value }))} />
            <div className="action-row">
              <ActionButton onClick={createTask} disabled={!selectedSession?.id}>Create task</ActionButton>
              <ActionButton onClick={generateChangeSet} disabled={!selectedTask?.id}>Generate change set</ActionButton>
            </div>
          </div>
          <List items={selectedTask ? [selectedTask] : []} empty="No task selected." renderItem={(task) => <div key={task.id} className="stack-item"><strong>{task.title}</strong><span>{task.task_type} · {task.status}</span></div>} />
          <List items={generationRequest ? [generationRequest] : []} empty="No generation request yet." renderItem={(request) => <div key={request.id} className="stack-item"><strong>{request.instruction}</strong><span>{request.status} · {request.model_provider}/{request.model_name}</span></div>} />
        </Panel>

        <Panel title="Change set, validation, review, and approvals" aside={<span>{changeSet?.status || "GENERATED"}</span>}>
          <div className="grid-form">
            <Field label="Validation command" value={validationDraft.command} onChange={(event) => setValidationDraft((current) => ({ ...current, command: event.target.value }))} />
            <SelectField label="Validation type" value={validationDraft.validation_type} onChange={(event) => setValidationDraft((current) => ({ ...current, validation_type: event.target.value }))} options={[{ value: "FORMAT", label: "Format" }, { value: "LINT", label: "Lint" }, { value: "TYPE_CHECK", label: "Type check" }, { value: "UNIT_TEST", label: "Unit test" }, { value: "BUILD", label: "Build" }]} />
            <div className="action-row">
              <ActionButton onClick={runValidation} disabled={!changeSet?.id}>Run validation</ActionButton>
              <ActionButton onClick={createReview} disabled={!changeSet?.id} tone="secondary">Create review</ActionButton>
              <ActionButton onClick={requestApproval} disabled={!changeSet?.id}>Request approval</ActionButton>
            </div>

            <Field label="Review summary" value={reviewDraft.summary} onChange={(event) => setReviewDraft((current) => ({ ...current, summary: event.target.value }))} />
            <Field label="Reviewer" value={reviewDraft.reviewer_id} onChange={(event) => setReviewDraft((current) => ({ ...current, reviewer_id: event.target.value }))} />
            <div className="action-row">
              <ActionButton onClick={approveLatest} disabled={!approvals.length}>Approve latest</ActionButton>
              <ActionButton onClick={createCommitProposal} disabled={!changeSet?.id} tone="secondary">Create commit proposal</ActionButton>
              <ActionButton onClick={executeCommitProposal} disabled={!commitProposal?.id}>Execute commit proposal</ActionButton>
            </div>
          </div>

          <div className="split-columns">
            <div>
              <h3>Validation runs</h3>
              <List items={validationRuns.slice(0, 5)} empty="No validations yet." renderItem={(item) => <div key={item.id} className="stack-item"><strong>{item.validation_type}</strong><span>{item.status} · exit {String(item.exit_code ?? "n/a")}</span></div>} />
            </div>
            <div>
              <h3>Reviews</h3>
              <List items={reviews.slice(0, 5)} empty="No reviews yet." renderItem={(item) => <div key={item.id} className="stack-item"><strong>{item.summary || item.id}</strong><span>{item.status} · {item.reviewer_id || "reviewer"}</span></div>} />
            </div>
            <div>
              <h3>Approvals</h3>
              <List items={approvals.slice(0, 5)} empty="No approvals yet." renderItem={(item) => <div key={item.id} className="stack-item"><strong>{item.required_role || item.approval_type}</strong><span>{item.decision} · {item.reason || "pending"}</span></div>} />
            </div>
            <div>
              <h3>Evidence</h3>
              <List items={evidence.slice(0, 5)} empty="No evidence yet." renderItem={(item) => <div key={item.id} className="stack-item"><strong>{item.id}</strong><span>{item.integrity_hash}</span></div>} />
            </div>
          </div>
          <div className="split-columns">
            <div>
              <h3>Change set</h3>
              {changeSet ? (
                <div className="stack-item">
                  <strong>{changeSet.summary}</strong>
                  <span>{changeSet.status} · {changeSet.files_added_count} added · {changeSet.files_modified_count} modified</span>
                </div>
              ) : (
                <p className="empty-state">No change set generated yet.</p>
              )}
            </div>
            <div>
              <h3>Commit proposal</h3>
              {commitProposal ? (
                <div className="stack-item">
                  <strong>{commitProposal.commit_message}</strong>
                  <span>{commitProposal.status} · {commitProposal.resulting_commit_hash || "pending execution"}</span>
                </div>
              ) : (
                <p className="empty-state">No commit proposal created yet.</p>
              )}
            </div>
          </div>
        </Panel>

        <Panel title="Commands and timeline" aside={<span>{timeline.length} events</span>}>
          <div className="grid-form">
            <TextAreaField label="Command" value={commandDraft.command} onChange={(event) => setCommandDraft((current) => ({ ...current, command: event.target.value }))} rows={3} />
            <div className="action-row">
              <ActionButton onClick={executeCommand} disabled={!selectedSession?.id}>Run command</ActionButton>
              <ActionButton onClick={() => reload({ workspaceId: selectedWorkspaceId, sessionId: selectedSession?.id, changeSetId: changeSet?.id })} tone="secondary">Reload evidence</ActionButton>
            </div>
          </div>
          {commandRun ? (
            <div className="stack-item">
              <strong>{commandRun.command?.join(" ") || "command"}</strong>
              <span>{commandRun.status} · exit {String(commandRun.exit_code ?? "n/a")}</span>
            </div>
          ) : null}
          <List items={timeline.slice(0, 10)} empty="No timeline entries yet." renderItem={(item) => <div key={item.event_id || item.id} className="stack-item"><strong>{item.event_type || item.action || item.id}</strong><span>{item.new_state || item.result || item.timestamp}</span></div>} />
        </Panel>
      </div>

      <footer className="page-footer">
        <p>Development Studio route: {route.section} · Current workspace: {selectedWorkspace?.name || "none"} · Repository root: {repoStatus?.root || "n/a"}</p>
      </footer>
    </main>
  );
}

function mapErrorState(error) {
  const code = String(error?.code || error?.status || "error").toLowerCase();
  if (code.includes("forbidden")) return "forbidden";
  if (code.includes("not_found")) return "not_found";
  if (code.includes("timeout")) return "timeout";
  if (code.includes("offline")) return "offline";
  if (code.includes("service_unavailable")) return "service_unavailable";
  return "validation_failed";
}
