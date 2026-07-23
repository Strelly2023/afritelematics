import React, { useEffect, useMemo, useRef, useState } from "react";

import { createAIWorkspaceClient } from "../platform/aiWorkspaceApi.js";
import { ROUTES } from "../platform/routes.js";

const STARTER_PROMPTS = [
  "Create product strategy",
  "Plan requirements",
  "Design experience",
  "Create architecture",
  "Generate code",
  "Run tests",
  "Review security",
  "Prepare release",
  "Investigate incident",
];

const CONTEXT_SOURCES = ["Workspace", "Repository", "Branch", "Requirement", "Release", "Evidence", "Logs", "Traces"];
const TOOL_OPTIONS = ["Planner", "Architect", "Developer", "Tester", "Security", "Release"];
const MODEL_OPTIONS = ["NovaAI Balanced", "NovaAI Reasoning", "NovaAI Fast"];
const TAB_OPTIONS = ["Context", "Artifacts", "Changes", "Validation", "Traceability", "Evidence", "History", "Approvals"];

function parseConversationPath(pathname) {
  const parts = String(pathname || "")
    .replace(/\/+$/, "")
    .split("/")
    .filter(Boolean);
  const id = parts[2] || "";
  return { id };
}

function asText(value, fallback = "") {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return fallback;
}

function listify(value) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function formatDate(value) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString();
}

function groupConversations(conversations) {
  const groups = { Pinned: [], Today: [], "Previous 7 days": [], Older: [] };
  const now = Date.now();
  const day = 24 * 60 * 60 * 1000;
  for (const conversation of conversations) {
    if (conversation.pinned) {
      groups.Pinned.push(conversation);
      continue;
    }
    const updatedAt = conversation.updated_at || conversation.updatedAt || conversation.created_at || conversation.createdAt;
    const time = updatedAt ? new Date(updatedAt).getTime() : 0;
    const age = Number.isNaN(time) ? Infinity : now - time;
    if (age < day) {
      groups.Today.push(conversation);
    } else if (age < 7 * day) {
      groups["Previous 7 days"].push(conversation);
    } else {
      groups.Older.push(conversation);
    }
  }
  return groups;
}

function conversationCacheKey(session, conversationId) {
  const tenant = session?.organization_id || session?.tenant_id || session?.tenant || "default";
  return `novacodepro.conversation.${tenant}.${conversationId || "latest"}`;
}

function readCachedConversation(session, conversationId) {
  if (typeof window === "undefined" || !conversationId) {
    return null;
  }
  try {
    const raw = window.sessionStorage.getItem(conversationCacheKey(session, conversationId));
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function writeCachedConversation(session, conversation) {
  if (typeof window === "undefined" || !conversation?.id) {
    return;
  }
  try {
    window.sessionStorage.setItem(conversationCacheKey(session, "latest"), conversation.id);
    window.sessionStorage.setItem(conversationCacheKey(session, conversation.id), JSON.stringify(conversation));
  } catch {
    // Best-effort cache only.
  }
}

function Badge({ label, value }) {
  return (
    <span className="context-chip">
      <strong>{label}</strong>
      <span>{value}</span>
    </span>
  );
}

function Panel({ title, children, aside, className = "" }) {
  return (
    <section className={`panel ${className}`.trim()}>
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

export function ConversationStudio({ session, pathname, navigate, baseUrl = "", onLogout }) {
  const aiBaseUrl = baseUrl || (typeof window !== "undefined" ? window.location.origin : "");
  const client = useMemo(
    () => createAIWorkspaceClient({ baseUrl: aiBaseUrl, session, connected: true }),
    [aiBaseUrl, session],
  );
  const route = useMemo(() => parseConversationPath(pathname), [pathname]);
  const attachmentInputRef = useRef(null);
  const pendingConversationRef = useRef(null);
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [selectedTab, setSelectedTab] = useState("Context");
  const [query, setQuery] = useState("");
  const [messageDraft, setMessageDraft] = useState("");
  const [conversationTitle, setConversationTitle] = useState("");
  const [conversationSummary, setConversationSummary] = useState("Conversation-first governed engineering workspace");
  const [selectedTool, setSelectedTool] = useState(TOOL_OPTIONS[0]);
  const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS[0]);
  const [contextSources, setContextSources] = useState(["Workspace", "Repository", "Requirement"]);
  const [attachments, setAttachments] = useState([]);
  const [conversationContext, setConversationContext] = useState({});
  const [conversationArtifacts, setConversationArtifacts] = useState([]);
  const [conversationTraceability, setConversationTraceability] = useState({});
  const [contextDraft, setContextDraft] = useState({
    workspace_id: session?.workspace_id || session?.workspace?.id || "",
    project_id: session?.project_id || "",
    repository: session?.repository || "",
    branch: session?.branch || "main",
    environment: session?.environment || "development",
    linked_requirement_id: "",
    linked_release_id: "",
  });
  const [conversationState, setConversationState] = useState({
    pinned: false,
    archived: false,
    approval_state: "NOT_REQUIRED",
    validation_state: "PENDING",
  });

  async function reload(preferredConversationId = "", preferredConversation = null) {
    setState("loading");
    setError(null);
    try {
      const optimisticConversation = preferredConversation || pendingConversationRef.current;
      const payload = await client.listConversations({
        query: query || undefined,
        workspace_id: session?.workspace_id || session?.workspace?.id || undefined,
      });
      const items = payload.conversations || [];
      setConversations(items);
      const nextSelected =
        items.find((item) => item.id === route.id) ||
        items.find((item) => item.id === preferredConversationId) ||
        items.find((item) => item.id === selectedConversation?.id) ||
        optimisticConversation ||
        readCachedConversation(session, window.sessionStorage?.getItem(conversationCacheKey(session, "latest"))) ||
        items[0] ||
        null;
      let hydratedSelected = nextSelected;
      if (nextSelected) {
        const [detailResult, contextResult, artifactsResult, traceabilityResult] = await Promise.all([
          client.getConversation(nextSelected.id).catch(() => nextSelected),
          client.getConversationContext(nextSelected.id),
          client.getConversationArtifacts(nextSelected.id),
          client.getConversationTraceability(nextSelected.id),
        ]);
        const cachedSelected = readCachedConversation(session, nextSelected.id);
        hydratedSelected =
          detailResult && detailResult.id
            ? {
                ...nextSelected,
                ...(cachedSelected?.messages?.length && !detailResult.messages?.length ? { messages: cachedSelected.messages } : {}),
                ...detailResult,
                ...(cachedSelected?.messages?.length && !detailResult.messages?.length ? { messages: cachedSelected.messages } : {}),
              }
            : cachedSelected || nextSelected;
        setSelectedConversation(hydratedSelected);
        writeCachedConversation(session, hydratedSelected);
        setConversationContext(contextResult);
        setConversationArtifacts(artifactsResult.artifacts || []);
        setConversationTraceability(traceabilityResult || {});
        setContextDraft((current) => ({
          ...current,
          workspace_id: contextResult.workspace_id || current.workspace_id,
          project_id: contextResult.project_id || current.project_id,
          repository: contextResult.repository || current.repository,
          branch: contextResult.branch || current.branch,
          environment: contextResult.environment || current.environment,
        }));
        setConversationState({
          pinned: Boolean(hydratedSelected.pinned),
          archived: Boolean(hydratedSelected.archived),
          approval_state: asText(hydratedSelected.approval_state, "NOT_REQUIRED"),
          validation_state: asText(hydratedSelected.validation_state, "PENDING"),
        });
      } else {
        setSelectedConversation(null);
        setConversationContext({});
        setConversationArtifacts([]);
        setConversationTraceability({});
      }
      if (nextSelected?.id && pendingConversationRef.current?.id === nextSelected.id) {
        pendingConversationRef.current = null;
      }
      setState("ready");
    } catch (nextError) {
      setError(nextError);
      setState(
        nextError?.status === 401
          ? "unauthorized"
          : nextError?.status === 403
            ? "forbidden"
            : nextError?.status === 404
              ? "not_found"
              : nextError?.status === 504
                ? "timeout"
                : "service_unavailable",
      );
    }
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname, query]);

  const groupedConversations = useMemo(() => groupConversations(conversations), [conversations]);
  const selectedMetadata = {
    organisation: session?.organization_id || session?.organization || "NovaTech",
    workspace: selectedConversation?.workspace_id || session?.workspace_id || session?.workspace?.id || "—",
    project: selectedConversation?.project_id || contextDraft.project_id || "—",
    repository: selectedConversation?.repository || contextDraft.repository || "—",
    branch: selectedConversation?.branch || contextDraft.branch || "—",
    environment: selectedConversation?.environment || contextDraft.environment || "—",
    requirement: selectedConversation?.linked_requirement_id || "—",
    release: selectedConversation?.linked_release_id || "—",
    actor: session?.display_name || session?.email || session?.sub || "Signed in user",
    model: selectedModel,
    timestamp: selectedConversation?.updated_at || selectedConversation?.created_at || "—",
    correlation: selectedConversation?.correlation_id || "—",
    validation: selectedConversation?.validation_state || "PENDING",
    approval: selectedConversation?.approval_state || "NOT_REQUIRED",
  };

  const switchConversation = (conversationId) => {
    const target = `/novacodepro/conversation/${encodeURIComponent(conversationId)}`;
    navigate(target);
    if (window.location.pathname !== target) {
      window.history.pushState({}, "", target);
      window.dispatchEvent(new PopStateEvent("popstate"));
    }
  };

  const toggleContextSource = (source) => {
    setContextSources((current) =>
      current.includes(source) ? current.filter((item) => item !== source) : [...current, source],
    );
  };

  const addAttachment = async (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) {
      return;
    }
    setAttachments((current) => [
      ...current,
      ...files.map((file) => ({
        id: `${file.name}-${file.size}-${file.lastModified}`,
        name: file.name,
        type: file.type || "file",
        size: file.size,
      })),
    ]);
    event.target.value = "";
  };

  const createConversation = async () => {
    const prompt = messageDraft.trim() || conversationSummary.trim();
    const result = await client.createConversation(
      {
        title: conversationTitle.trim() || prompt || "Conversation",
        summary: conversationSummary.trim() || prompt || "Conversation-first request",
        prompt,
        workspace_id: contextDraft.workspace_id || session?.workspace_id || session?.workspace?.id,
        project_id: contextDraft.project_id || session?.project_id,
        repository: contextDraft.repository || session?.repository,
        branch: contextDraft.branch || session?.branch || "main",
        environment: contextDraft.environment || session?.environment || "development",
        linked_requirement_id: contextDraft.linked_requirement_id,
        linked_release_id: contextDraft.linked_release_id,
        context_sources: contextSources,
        attachments,
        model: selectedModel,
        provider: "governed-backend",
        actor_id: session?.sub || session?.user_id || session?.display_name || "NovaCodePro",
        idempotency_key: `${session?.workspace_id || session?.workspace?.id || "workspace"}:${Date.now()}:${prompt.slice(0, 32)}`,
        context: {
          organization: session?.organization_id || session?.organization || "NovaTech",
          workspace: contextDraft.workspace_id || session?.workspace_id || session?.workspace?.id || "",
          project: contextDraft.project_id || session?.project_id || "",
          repository: contextDraft.repository || "",
          branch: contextDraft.branch || "main",
          environment: contextDraft.environment || "development",
        },
      },
      `${session?.workspace_id || session?.workspace?.id || "workspace"}:${Date.now()}:${prompt.slice(0, 16)}`,
    );
    setMessageDraft("");
    pendingConversationRef.current = result;
      setSelectedConversation(result);
    writeCachedConversation(session, result);
    setConversationState({
      pinned: Boolean(result.pinned),
      archived: Boolean(result.archived),
      approval_state: asText(result.approval_state, "NOT_REQUIRED"),
      validation_state: asText(result.validation_state, "PENDING"),
    });
    setConversations((current) => [result, ...current.filter((item) => item.id !== result.id)]);
    const target = result.conversation_url || `/novacodepro/conversation/${encodeURIComponent(result.id)}`;
    navigate(target);
    if (window.location.pathname !== target) {
      window.history.pushState({}, "", target);
      window.dispatchEvent(new PopStateEvent("popstate"));
    }
    await reload(result.id, result);
  };

  const postMessage = async () => {
    if (!selectedConversation?.id) {
      await createConversation();
      return;
    }
    const body = messageDraft.trim();
    if (!body) {
      return;
    }
    const updatedConversation = await client.postConversationMessage(selectedConversation.id, {
      type: "user_request",
      role: "user",
      actor: session?.display_name || session?.email || session?.sub || "Signed in user",
      body,
      attachments,
      context_sources: contextSources,
      metadata: {
        tool: selectedTool,
        model: selectedModel,
      },
    });
    setMessageDraft("");
    setAttachments([]);
    if (updatedConversation?.id) {
      const hydratedConversation = {
        ...selectedConversation,
        ...updatedConversation,
      };
      setSelectedConversation(hydratedConversation);
      writeCachedConversation(session, hydratedConversation);
      setConversations((current) => [hydratedConversation, ...current.filter((item) => item.id !== hydratedConversation.id)]);
    } else {
      setSelectedConversation((current) => {
        if (!current?.id) {
          return current;
        }
        const optimisticMessage = {
          id: `optimistic-${Date.now()}`,
          type: "user_request",
          role: "user",
          actor: session?.display_name || session?.email || session?.sub || "Signed in user",
          body,
          attachments,
          context_sources: contextSources,
          metadata: { tool: selectedTool, model: selectedModel },
          at: new Date().toISOString(),
        };
        return {
          ...current,
          messages: [optimisticMessage, ...listify(current.messages)],
          message_count: (current.message_count || 0) + 1,
        };
      });
    }
    writeCachedConversation(session, {
      ...selectedConversation,
      messages: [
        {
          id: `optimistic-${Date.now()}`,
          type: "user_request",
          role: "user",
          actor: session?.display_name || session?.email || session?.sub || "Signed in user",
          body,
          attachments,
          context_sources: contextSources,
          metadata: { tool: selectedTool, model: selectedModel },
          at: new Date().toISOString(),
        },
        ...listify(selectedConversation?.messages),
      ],
    });
    await reload();
  };

  const generate = async () => {
    if (!selectedConversation?.id) {
      await createConversation();
      return;
    }
    const prompt = messageDraft.trim() || selectedConversation.title;
    await client.postConversationMessage(selectedConversation.id, {
      type: "tool_execution",
      role: "NovaAI",
      actor: "NovaAI",
      body: `NovaAI is generating a governed response for: ${prompt}`,
      context_sources: contextSources,
      metadata: { tool: selectedTool, model: selectedModel, action: "generate" },
    });
    try {
      await client.submitAIRequest({
        request_text: prompt,
        conversation_id: selectedConversation.id,
        project_id: contextDraft.project_id || selectedConversation.project_id,
        workspace_id: contextDraft.workspace_id || selectedConversation.workspace_id,
        repository: contextDraft.repository || selectedConversation.repository,
        branch: contextDraft.branch || selectedConversation.branch,
        environment: contextDraft.environment || selectedConversation.environment,
        context_sources: contextSources,
        model: selectedModel,
        provider: "governed-backend",
      });
    } catch (submitError) {
      await client.postConversationMessage(selectedConversation.id, {
        type: "warning",
        role: "system",
        actor: "NovaAI",
        body: `AI request could not be started: ${submitError?.message || submitError?.code || "unknown error"}`,
      });
    }
    setMessageDraft("");
    setAttachments([]);
    await reload();
  };

  const togglePin = async () => {
    if (!selectedConversation?.id) return;
    await client.updateConversation(selectedConversation.id, { pinned: !conversationState.pinned });
    await reload();
  };

  const archiveConversation = async () => {
    if (!selectedConversation?.id) return;
    await client.archiveConversation(selectedConversation.id);
    await reload();
  };

  const restoreConversation = async () => {
    if (!selectedConversation?.id) return;
    await client.restoreConversation(selectedConversation.id);
    await reload();
  };

  const deleteConversation = async () => {
    if (!selectedConversation?.id) return;
    await client.deleteConversation(selectedConversation.id);
    await reload();
  };

  const saveContext = async () => {
    if (!selectedConversation?.id) return;
    await client.updateConversationContext(selectedConversation.id, {
      context: {
        organization: selectedMetadata.organisation,
        workspace: contextDraft.workspace_id,
        project: contextDraft.project_id,
        repository: contextDraft.repository,
        branch: contextDraft.branch,
        environment: contextDraft.environment,
        requirement: contextDraft.linked_requirement_id,
        release: contextDraft.linked_release_id,
      },
      context_sources: contextSources,
      workspace_id: contextDraft.workspace_id,
      project_id: contextDraft.project_id,
      repository: contextDraft.repository,
      branch: contextDraft.branch,
      environment: contextDraft.environment,
    });
    await reload();
  };

  const openFullStudio = () => navigate(ROUTES.roleDashboard(session?.active_role || "ADMIN"));

  const selectedMessages = listify(selectedConversation?.messages);

  return (
    <div className="conversation-studio" data-testid="conversation-studio">
      <header className="conversation-header">
        <div className="conversation-header__brand">
          <button type="button" className="brand-badge" onClick={() => navigate(ROUTES.conversationRoot)} aria-label="NovaCodePro">
            N
          </button>
          <div>
            <p className="section-label">Conversation-first studio</p>
            <h1>What would you like to build today?</h1>
            <p className="studio-note">
              NovaCodePro keeps the conversation tied to the authorised workspace, repository, branch, release, and evidence trail.
            </p>
          </div>
        </div>
        <div className="conversation-header__actions">
          <button type="button" className="secondary-action" onClick={openFullStudio}>
            Open Full Studio
          </button>
          <button type="button" className="secondary-action" onClick={() => navigate(ROUTES.conversationRoot)}>
            Return to Conversation
          </button>
          <button type="button" className="danger-action" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </header>

      <StateBanner state={state} error={error} />

      <div className="conversation-shell">
        <aside className="conversation-sidebar" aria-label="Conversations and workspaces">
          <label className="field">
            <span>Search conversations</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search history, artifacts, evidence…" />
          </label>
          <button type="button" className="primary-action" onClick={() => setSelectedConversation(null)}>
            + New Conversation
          </button>
          <div className="conversation-sidebar__filters">
            <button type="button" className="context-chip active">
              Workspace: {session?.workspace_id || session?.workspace?.id || "Current"}
            </button>
            <button type="button" className="context-chip">
              Branch: {contextDraft.branch || "main"}
            </button>
            <button type="button" className="context-chip">
              Environment: {contextDraft.environment}
            </button>
          </div>
          {Object.entries(groupConversations(conversations)).map(([group, items]) => (
            <section key={group} className="conversation-group">
              <h2>{group}</h2>
              {items.length ? (
                <div className="stack">
                  {items.map((conversation) => (
                    <button
                      key={conversation.id}
                      type="button"
                      className={selectedConversation?.id === conversation.id ? "list-row active" : "list-row"}
                      onClick={() => switchConversation(conversation.id)}
                    >
                      <strong>{conversation.title}</strong>
                      <span>{conversation.summary || conversation.scope}</span>
                      <small>
                        {conversation.project_id || "No project"} · {conversation.message_count || 0} messages
                      </small>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="empty-state">No conversations.</p>
              )}
            </section>
          ))}
          <section className="conversation-group">
            <h2>Projects</h2>
            <p className="empty-state">Project: {selectedConversation?.project_id || session?.project_id || "Not selected"}</p>
          </section>
        </aside>

        <main className="conversation-main">
          {selectedConversation ? (
            <>
              <section className="conversation-canvas">
                <div className="conversation-canvas__header">
                  <div>
                    <p className="section-label">Conversation canvas</p>
                    <h2>{selectedConversation.title}</h2>
                    <p className="studio-note">{selectedConversation.summary || selectedConversation.scope}</p>
                  </div>
                  <div className="conversation-canvas__meta">
                    <Badge label="Approval" value={selectedConversation.approval_state || "NOT_REQUIRED"} />
                    <Badge label="Validation" value={selectedConversation.validation_state || "PENDING"} />
                    <Badge label="Messages" value={String(selectedConversation.message_count || selectedMessages.length || 0)} />
                    <Badge label="Pinned" value={conversationState.pinned ? "Yes" : "No"} />
                  </div>
                </div>

                <div className="conversation-message-stream" aria-live="polite">
                  {selectedMessages.length ? (
                    selectedMessages.map((message) => (
                      <article className={`conversation-message ${message.role === "user" ? "user" : "assistant"}`} key={message.id}>
                        <div className="conversation-message__header">
                          <strong>{message.type || message.role || "message"}</strong>
                          <span>{formatDate(message.at || message.created_at || message.timestamp)}</span>
                        </div>
                        <p>{message.body}</p>
                        <details>
                          <summary>Details</summary>
                          <div className="conversation-message__details">
                            <span>Organisation: {selectedMetadata.organisation}</span>
                            <span>Workspace: {selectedMetadata.workspace}</span>
                            <span>Project: {selectedMetadata.project}</span>
                            <span>Repository: {selectedMetadata.repository}</span>
                            <span>Branch: {selectedMetadata.branch}</span>
                            <span>Environment: {selectedMetadata.environment}</span>
                            <span>Requirement: {selectedMetadata.requirement}</span>
                            <span>Release: {selectedMetadata.release}</span>
                            <span>Actor: {message.actor || selectedMetadata.actor}</span>
                            <span>AI model: {message.metadata?.model || selectedMetadata.model}</span>
                            <span>Correlation ID: {selectedConversation.correlation_id || "—"}</span>
                            <span>Validation state: {selectedConversation.validation_state || "PENDING"}</span>
                            <span>Approval state: {selectedConversation.approval_state || "NOT_REQUIRED"}</span>
                          </div>
                        </details>
                      </article>
                    ))
                  ) : (
                    <article className="empty-state conversation-empty">
                      <p>Start with a request.</p>
                      <div className="starter-grid">
                        {STARTER_PROMPTS.map((prompt) => (
                          <button key={prompt} type="button" className="starter-card" onClick={() => setMessageDraft(prompt)}>
                            {prompt}
                          </button>
                        ))}
                      </div>
                    </article>
                  )}
                </div>

                <div className="conversation-composer">
                  <input ref={attachmentInputRef} type="file" hidden multiple onChange={addAttachment} />
                  <label className="field">
                    <span>Conversation title</span>
                    <input value={conversationTitle} onChange={(event) => setConversationTitle(event.target.value)} />
                  </label>
                  <label className="field">
                    <span>Conversation summary</span>
                    <input value={conversationSummary} onChange={(event) => setConversationSummary(event.target.value)} />
                  </label>
                  <label className="field">
                    <span>Prompt</span>
                    <textarea
                      rows={5}
                      value={messageDraft}
                      onChange={(event) => setMessageDraft(event.target.value)}
                      placeholder="Create architecture for a trusted rideshare platform."
                    />
                  </label>
                  <div className="conversation-composer__toolbar">
                    <button type="button" className="toolbar-chip" onClick={() => attachmentInputRef.current?.click()}>
                      Attach
                    </button>
                    <button type="button" className="toolbar-chip" onClick={() => setSelectedTab("Context")}>
                      Select Context
                    </button>
                    <select value={selectedTool} onChange={(event) => setSelectedTool(event.target.value)} aria-label="Tools">
                      {TOOL_OPTIONS.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                    <select value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)} aria-label="Model">
                      {MODEL_OPTIONS.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                    <button type="button" className="primary-action" onClick={createConversation}>
                      Create
                    </button>
                    <button type="button" className="secondary-action" onClick={postMessage}>
                      Send
                    </button>
                    <button type="button" className="secondary-action" onClick={generate}>
                      Generate
                    </button>
                  </div>
                  <div className="chip-cloud">
                    {CONTEXT_SOURCES.map((source) => (
                      <button
                        key={source}
                        type="button"
                        className={contextSources.includes(source) ? "context-chip active" : "context-chip"}
                        onClick={() => toggleContextSource(source)}
                      >
                        {source}
                      </button>
                    ))}
                  </div>
                  {attachments.length ? (
                    <div className="attachment-strip">
                      {attachments.map((attachment) => (
                        <span key={attachment.id} className="attachment-chip">
                          {attachment.name}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </section>

              <section className="conversation-actions">
                <button type="button" className="secondary-action" onClick={togglePin}>
                  {conversationState.pinned ? "Unpin" : "Pin"}
                </button>
                <button type="button" className="secondary-action" onClick={selectedConversation.archived ? restoreConversation : archiveConversation}>
                  {selectedConversation.archived ? "Restore" : "Archive"}
                </button>
                <button type="button" className="danger-action" onClick={deleteConversation}>
                  Delete
                </button>
                <button type="button" className="secondary-action" onClick={saveContext}>
                  Save context
                </button>
                <button
                  type="button"
                  className="secondary-action"
                  onClick={() => {
                    const target = `/novacodepro/conversation/${selectedConversation.id}`;
                    navigate(target);
                    if (window.location.pathname !== target) {
                      window.history.pushState({}, "", target);
                      window.dispatchEvent(new PopStateEvent("popstate"));
                    }
                  }}
                >
                  Refresh route
                </button>
              </section>
            </>
          ) : (
            <section className="conversation-empty-shell">
              <h2>What would you like to build today?</h2>
              <p>
                The conversation remains tied to the authorised project, branch, environment, requirements, and evidence package.
              </p>
              <div className="conversation-composer">
                <label className="field">
                  <span>Prompt</span>
                  <textarea
                    rows={5}
                    value={messageDraft}
                    onChange={(event) => setMessageDraft(event.target.value)}
                    placeholder="Create architecture for a trusted rideshare platform."
                  />
                </label>
                <div className="conversation-composer__toolbar">
                  <button type="button" className="toolbar-chip" onClick={() => attachmentInputRef.current?.click()}>
                    Attach
                  </button>
                  <button type="button" className="toolbar-chip" onClick={() => setSelectedTab("Context")}>
                    Select Context
                  </button>
                  <select value={selectedTool} onChange={(event) => setSelectedTool(event.target.value)} aria-label="Tools">
                    {TOOL_OPTIONS.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                  <select value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)} aria-label="Model">
                    {MODEL_OPTIONS.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                  <button type="button" className="primary-action" onClick={createConversation}>
                    Create
                  </button>
                  <button type="button" className="secondary-action" onClick={generate}>
                    Generate
                  </button>
                </div>
                <div className="chip-cloud">
                  {CONTEXT_SOURCES.map((source) => (
                    <button
                      key={source}
                      type="button"
                      className={contextSources.includes(source) ? "context-chip active" : "context-chip"}
                      onClick={() => toggleContextSource(source)}
                    >
                      {source}
                    </button>
                  ))}
                </div>
              </div>
              <div className="starter-grid">
                {STARTER_PROMPTS.map((prompt) => (
                  <button key={prompt} type="button" className="starter-card" onClick={() => setMessageDraft(prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>
            </section>
          )}
        </main>

        <aside className="conversation-context" aria-label="Context and artifacts">
          <div className="tab-strip" role="tablist" aria-label="Conversation detail tabs">
            {TAB_OPTIONS.map((tab) => (
              <button
                key={tab}
                type="button"
                role="tab"
                aria-selected={selectedTab === tab}
                className={selectedTab === tab ? "workspace-tab active" : "workspace-tab"}
                onClick={() => setSelectedTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>

          <Panel title="Context" aside={<span className="context-chip active">Server-bound</span>}>
            <div className="conversation-context__grid">
              {Object.entries(selectedMetadata).map(([label, value]) => (
                <div className="artifact-row" key={label}>
                  <strong>{label}</strong>
                  <span>{value}</span>
                </div>
              ))}
            </div>
          </Panel>

          {selectedTab === "Artifacts" ? (
            <Panel title="Artifacts">
              <div className="artifact-list">
                {conversationArtifacts.length ? (
                  conversationArtifacts.map((artifact) => (
                    <div className="artifact-row" key={artifact.id || artifact.title}>
                      <strong>{artifact.title || artifact.name || artifact.id}</strong>
                      <span>{artifact.type || artifact.artifact_type || "artifact"}</span>
                    </div>
                  ))
                ) : (
                  <p className="empty-state">No artifacts linked yet.</p>
                )}
              </div>
            </Panel>
          ) : null}

          {selectedTab === "Changes" ? (
            <Panel title="Changes">
              <div className="artifact-list">
                {selectedMessages.map((message) => (
                  <div className="audit-row" key={message.id}>
                    <span>{formatDate(message.at)}</span>
                    <strong>{message.type || message.role}</strong>
                    <p>{asText(message.body, "No message body")}</p>
                  </div>
                ))}
              </div>
            </Panel>
          ) : null}

          {selectedTab === "Validation" ? (
            <Panel title="Validation">
              <div className="artifact-list">
                <div className="artifact-row">
                  <strong>Validation state</strong>
                  <span>{selectedConversation?.validation_state || "PENDING"}</span>
                </div>
                {listify(selectedConversation?.validation_results).map((result, index) => (
                  <div className="artifact-row" key={`${result.id || result.name || index}`}>
                    <strong>{result.name || result.title || result.id || `Result ${index + 1}`}</strong>
                    <span>{result.status || result.state || "unknown"}</span>
                  </div>
                ))}
              </div>
            </Panel>
          ) : null}

          {selectedTab === "Traceability" ? (
            <Panel title="Traceability">
              <div className="artifact-list">
                {Object.entries({
                  requirements: conversationTraceability.requirements || [],
                  releases: conversationTraceability.releases || [],
                  incidents: conversationTraceability.incidents || [],
                  evidence: conversationTraceability.evidence || [],
                }).map(([label, items]) => (
                  <div className="artifact-row" key={label}>
                    <strong>{label}</strong>
                    <span>{items.length ? items.join(", ") : "None"}</span>
                  </div>
                ))}
              </div>
            </Panel>
          ) : null}

          {selectedTab === "Evidence" ? (
            <Panel title="Evidence">
              <div className="artifact-list">
                {listify(selectedConversation?.evidence).length ? (
                  listify(selectedConversation?.evidence).map((item) => (
                    <div className="artifact-row" key={item.id || item}>
                      <strong>{item.id || item}</strong>
                      <span>{item.status || item.type || "evidence"}</span>
                    </div>
                  ))
                ) : (
                  <p className="empty-state">No evidence attached.</p>
                )}
              </div>
            </Panel>
          ) : null}

          {selectedTab === "History" ? (
            <Panel title="History">
              <div className="artifact-list">
                {selectedMessages.length ? (
                  selectedMessages.map((message) => (
                    <div className="audit-row" key={`history-${message.id}`}>
                      <span>{formatDate(message.at)}</span>
                      <strong>{message.role}</strong>
                      <p>{message.body}</p>
                    </div>
                  ))
                ) : (
                  <p className="empty-state">History is empty.</p>
                )}
              </div>
            </Panel>
          ) : null}

          {selectedTab === "Approvals" ? (
            <Panel title="Approvals">
              <div className="artifact-list">
                {listify(selectedConversation?.approvals).length ? (
                  listify(selectedConversation?.approvals).map((item) => (
                    <div className="artifact-row" key={item.id || item.approval_id || item}>
                      <strong>{item.required_role || item.role || item.id || "Approval"}</strong>
                      <span>{item.decision || item.status || "PENDING"}</span>
                    </div>
                  ))
                ) : (
                  <p className="empty-state">No approval records linked yet.</p>
                )}
              </div>
            </Panel>
          ) : null}
        </aside>
      </div>

      <footer className="conversation-statusbar">
        <span>{selectedMetadata.workspace}</span>
        <span>{selectedMetadata.repository}</span>
        <span>{selectedMetadata.branch}</span>
        <span>{selectedMetadata.environment}</span>
        <span>Requirement: {selectedMetadata.requirement}</span>
        <span>Release: {selectedMetadata.release}</span>
      </footer>
    </div>
  );
}
