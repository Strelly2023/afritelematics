import React, { useEffect, useMemo, useState } from "react";

import { createAIWorkspaceClient } from "../platform/aiWorkspaceApi.js";

function parseRoute(pathname) {
  const parts = String(pathname || "")
    .replace(/\/+$/, "")
    .split("/")
    .filter(Boolean);
  const section = parts[2] || "executions";
  const id = parts[3] || "";
  const subRoute = parts[4] || "";
  return { section, id, subRoute };
}

function Badge({ label, value }) {
  return (
    <span className="context-chip">
      <strong>{label}</strong>
      <span>{value}</span>
    </span>
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

function StateBanner({ state, error }) {
  const label =
    state === "loading"
      ? "Loading"
      : state === "ready"
        ? "Ready"
        : state === "forbidden"
          ? "Forbidden"
          : state === "unauthorized"
            ? "Unauthorized"
            : state === "not_found"
              ? "Not found"
              : state === "service_unavailable"
                ? "Service unavailable"
                : state === "timeout"
                  ? "Timeout"
                  : "Error";
  return (
    <div className={`state-banner ${state || "error"}`} role="status" aria-live="polite">
      <strong>{label}</strong>
      <span>{error?.message || error?.code || "N/A"}</span>
    </div>
  );
}

function listify(value) {
  return Array.isArray(value) ? value : [];
}

export function NCP004Portal({ session, pathname, navigate, baseUrl = "", onLogout }) {
  const client = useMemo(
    () => createAIWorkspaceClient({ baseUrl, session, connected: Boolean(baseUrl) }),
    [baseUrl, session],
  );
  const route = useMemo(() => parseRoute(pathname), [pathname]);
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [agents, setAgents] = useState([]);
  const [tools, setTools] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [execution, setExecution] = useState(null);
  const [clarifications, setClarifications] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [replay, setReplay] = useState(null);
  const [requestText, setRequestText] = useState("Build rider registration with NovaID identity verification.");
  const [projectId, setProjectId] = useState(session?.project_id || "");
  const [requestId, setRequestId] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [clarificationAnswers, setClarificationAnswers] = useState({});
  const [approvalReason, setApprovalReason] = useState("Approved for governed execution.");

  async function reload() {
    setState("loading");
    setError(null);
    try {
      const [executionList, agentList, toolList, approvalList, notificationList] = await Promise.all([
        client.listExecutions(),
        client.listAgents(),
        client.listTools(),
        client.listApprovals(),
        client.listNotifications(),
      ]);
      setExecutions(executionList.executions || []);
      setAgents(agentList.agents || []);
      setTools(toolList.tools || []);
      setApprovals(approvalList.approvals || []);
      setNotifications(notificationList.notifications || []);
      const nextExecutionId = route.id || executionList.executions?.[0]?.id || "";
      if (nextExecutionId) {
        const detail = await client.getExecution(nextExecutionId);
        setExecution(detail);
        const [clarificationList, timelineList, evidenceList, replayItem] = await Promise.all([
          client.listClarifications(nextExecutionId),
          client.getTimeline(nextExecutionId),
          client.getEvidence(nextExecutionId),
          client.getReplay(nextExecutionId).catch(() => null),
        ]);
        setClarifications(clarificationList.clarifications || []);
        setTimeline(timelineList.timeline || []);
        setEvidence(evidenceList.evidence || []);
        setReplay(replayItem);
      } else {
        setExecution(null);
        setClarifications([]);
        setTimeline([]);
        setEvidence([]);
        setReplay(null);
      }
      setState("ready");
    } catch (nextError) {
      setError(nextError);
      setState(nextError?.status === 401 ? "unauthorized" : nextError?.status === 403 ? "forbidden" : nextError?.status === 404 ? "not_found" : nextError?.status === 504 ? "timeout" : "service_unavailable");
    }
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  const selectedApproval = useMemo(
    () => approvals.find((item) => item.execution_id === execution?.id) || null,
    [approvals, execution],
  );

  const createExecution = async () => {
    const result = await client.createExecution(
      {
        request_text: requestText,
        request_id: requestId || undefined,
        project_id: projectId || undefined,
        workspace_id: session?.workspace_id || session?.workspace?.id || undefined,
        idempotency_key: idempotencyKey || undefined,
      },
      idempotencyKey || undefined,
    );
    navigate(`/novacodepro/ai/executions/${result.id}`);
  };

  const refreshDetail = async (executionId) => {
    const detail = await client.getExecution(executionId);
    setExecution(detail);
    const [clarificationList, timelineList, evidenceList, replayItem] = await Promise.all([
      client.listClarifications(executionId),
      client.getTimeline(executionId),
      client.getEvidence(executionId),
      client.getReplay(executionId).catch(() => null),
    ]);
    setClarifications(clarificationList.clarifications || []);
    setTimeline(timelineList.timeline || []);
    setEvidence(evidenceList.evidence || []);
    setReplay(replayItem);
    const [executionList, approvalList, notificationList] = await Promise.all([
      client.listExecutions(),
      client.listApprovals(),
      client.listNotifications(),
    ]);
    setExecutions(executionList.executions || []);
    setApprovals(approvalList.approvals || []);
    setNotifications(notificationList.notifications || []);
  };

  const mutate = async (action) => {
    if (!execution?.id) return;
    await action(execution.id);
    await refreshDetail(execution.id);
  };

  const answerClarification = async (clarificationId) => {
    if (!execution?.id) return;
    await client.answerClarification(execution.id, clarificationId, { answer: clarificationAnswers[clarificationId] || "" });
    await refreshDetail(execution.id);
  };

  const executionSummary = execution
    ? `${execution.status} · ${execution.risk_class || "unknown"} · ${execution.request_type || "unclassified"}`
    : "No execution selected";

  return (
    <div className="solution-portal">
      <header className="panel">
        <div className="panel-header">
          <div>
            <p className="section-label">NovaCodePro NovaAI</p>
            <h1>Governed NovaAI orchestration</h1>
            <p className="studio-note">Execution lifecycle, approvals, evidence, and replay are persisted server-side.</p>
          </div>
          <div className="panel-aside">
            <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/ai")}>
              Execution list
            </button>
            <button type="button" className="danger-action" onClick={onLogout}>
              Sign out
            </button>
          </div>
        </div>
        <div className="chip-cloud">
          <Badge label="Tenant" value={session?.tenant_id || session?.tenant || "Unknown"} />
          <Badge label="Workspace" value={session?.workspace?.id || session?.workspace_id || "Required"} />
          <Badge label="Role" value={session?.active_role || "Unknown"} />
          <Badge label="Execution" value={executionSummary} />
        </div>
      </header>

      <StateBanner state={state} error={error} />

      <div className="dual-grid">
        <Panel
          title="Create execution"
          aside={<span className="context-chip active">{executions.length} executions</span>}
        >
          <label className="field">
            <span>Request text</span>
            <textarea value={requestText} onChange={(event) => setRequestText(event.target.value)} rows={5} />
          </label>
          <div className="input-row">
            <label className="field">
              <span>Project ID</span>
              <input value={projectId} onChange={(event) => setProjectId(event.target.value)} />
            </label>
            <label className="field">
              <span>Request ID</span>
              <input value={requestId} onChange={(event) => setRequestId(event.target.value)} />
            </label>
          </div>
          <label className="field">
            <span>Idempotency key</span>
            <input value={idempotencyKey} onChange={(event) => setIdempotencyKey(event.target.value)} placeholder="optional" />
          </label>
          <button type="button" className="primary-action" onClick={createExecution}>
            Start NovaAI execution
          </button>
        </Panel>

        <Panel title="Executions" aside={<span className="context-chip">{notifications.length} notifications</span>}>
          {executions.length ? (
            <div className="stack">
              {executions.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  className={item.id === execution?.id ? "list-row active" : "list-row"}
                  onClick={() => navigate(`/novacodepro/ai/executions/${item.id}`)}
                >
                  <strong>{item.request_text || item.id}</strong>
                  <span>
                    {item.status} · {item.risk_class}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <p className="empty-state">No executions yet.</p>
          )}
        </Panel>
      </div>

      {execution ? (
        <>
          <Panel title="Execution controls" aside={<span className="context-chip active">{execution.status}</span>}>
            <div className="chip-cloud">
              <Badge label="Request type" value={execution.request_type || "unknown"} />
              <Badge label="Risk" value={execution.risk_class || "unknown"} />
              <Badge label="Policy" value={execution.policy_decision || "pending"} />
              <Badge label="Approval" value={execution.approval_state || "pending"} />
            </div>
            <div className="action-grid">
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.analyseExecution(id))}>
                Analyse
              </button>
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.generateRequirements(id))}>
                Generate requirements
              </button>
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.generatePlan(id))}>
                Generate plan
              </button>
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.validatePlan(id))}>
                Validate plan
              </button>
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.requestApproval(id))}>
                Request approval
              </button>
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.execute(id))}>
                Execute
              </button>
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.verifyExecution(id))}>
                Verify
              </button>
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.cancelExecution(id))}>
                Cancel
              </button>
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.pauseExecution(id))}>
                Pause
              </button>
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.resumeExecution(id))}>
                Resume
              </button>
              <button type="button" className="secondary-action" onClick={() => mutate((id) => client.rollbackExecution(id))}>
                Rollback
              </button>
            </div>
          </Panel>

          <div className="triple-grid">
            <Panel title="Clarifications">
              {clarifications.length ? (
                <div className="stack">
                  {clarifications.map((item) => (
                    <div className="artifact-row" key={item.id}>
                      <strong>{item.question}</strong>
                      <p className="studio-note">{item.why}</p>
                      <input
                        value={clarificationAnswers[item.id] || item.answer || ""}
                        onChange={(event) => setClarificationAnswers((current) => ({ ...current, [item.id]: event.target.value }))}
                        placeholder="Answer"
                      />
                      <button type="button" className="secondary-action" onClick={() => answerClarification(item.id)}>
                        Save answer
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-state">No clarifications.</p>
              )}
            </Panel>

            <Panel title="Approval">
              {selectedApproval ? (
                <div className="stack">
                  <strong>{selectedApproval.required_role}</strong>
                  <p className="studio-note">Decision: {selectedApproval.decision}</p>
                  <label className="field">
                    <span>Reason</span>
                    <textarea value={approvalReason} onChange={(event) => setApprovalReason(event.target.value)} rows={3} />
                  </label>
                  <div className="action-grid">
                    <button type="button" className="secondary-action" onClick={() => client.approve(selectedApproval.id, { decision: "APPROVED", reason: approvalReason }).then(() => refreshDetail(execution.id))}>
                      Approve
                    </button>
                    <button type="button" className="secondary-action" onClick={() => client.reject(selectedApproval.id, { reason: approvalReason }).then(() => refreshDetail(execution.id))}>
                      Reject
                    </button>
                    <button type="button" className="secondary-action" onClick={() => client.requestChanges(selectedApproval.id, { reason: approvalReason }).then(() => refreshDetail(execution.id))}>
                      Request changes
                    </button>
                  </div>
                </div>
              ) : (
                <p className="empty-state">No approval requested yet.</p>
              )}
            </Panel>

            <Panel title="Verification and evidence">
              <div className="stack">
                <strong>{execution.verification?.status || "Pending"}</strong>
                <p className="studio-note">Evidence: {execution.evidence_reference || "Not recorded"}</p>
                <div className="artifact-list">
                  {listify(evidence).map((item) => (
                    <div className="artifact-row" key={item.id}>
                      <strong>{item.id}</strong>
                      <span>{item.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            </Panel>
          </div>

          <div className="dual-grid">
            <Panel title="Timeline">
              <div className="artifact-list">
                {timeline.length ? (
                  timeline.map((item) => (
                    <div className="audit-row" key={item.id}>
                      <span>{item.timestamp}</span>
                      <strong>{item.summary}</strong>
                      <p>{item.event_type}</p>
                    </div>
                  ))
                ) : (
                  <p className="empty-state">Timeline is empty.</p>
                )}
              </div>
            </Panel>

            <Panel title="Replay">
              {replay ? (
                <div className="stack">
                  <strong>{replay.status}</strong>
                  <p className="studio-note">Replay contains {replay.timeline?.length || 0} timeline events.</p>
                  <div className="artifact-list">
                    {listify(replay.timeline).slice(0, 8).map((item) => (
                      <div className="artifact-row" key={item.id}>
                        <strong>{item.summary}</strong>
                        <span>{item.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="empty-state">Replay is not available yet.</p>
              )}
            </Panel>
          </div>

          <Panel title="Agents and tools">
            <div className="dual-grid">
              <div className="stack">
                <h3>Agents</h3>
                {agents.map((agent) => (
                  <div className="artifact-row" key={agent.agent_id}>
                    <strong>{agent.name}</strong>
                    <span>{agent.active_version || agent.version}</span>
                  </div>
                ))}
              </div>
              <div className="stack">
                <h3>Tools</h3>
                {tools.map((tool) => (
                  <div className="artifact-row" key={tool.tool_id}>
                    <strong>{tool.tool_id}</strong>
                    <span>{tool.risk_level}</span>
                  </div>
                ))}
              </div>
            </div>
          </Panel>
        </>
      ) : null}
    </div>
  );
}
