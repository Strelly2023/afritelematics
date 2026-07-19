import React, { useEffect, useMemo, useState } from "react";

import { createNovaCodeProNcp005Api } from "./api/novacodeproNcp005Api.js";

function parseRoute(pathname) {
  const parts = String(pathname || "")
    .replace(/\/+$/, "")
    .split("/")
    .filter(Boolean);
  if (parts[0] !== "novacodepro") {
    return { section: "requirements", subRoute: "/" };
  }
  const section = parts[1] || "requirements";
  return { section, subRoute: `/${parts.slice(2).join("/")}`.replace(/\/+$/, "") || "/" };
}

function StateBanner({ state, error }) {
  if (state === "ready") {
    return null;
  }
  const label = {
    loading: "Loading",
    empty: "Empty",
    unauthorized: "Unauthorized",
    forbidden: "Forbidden",
    not_found: "Not found",
    offline: "Offline",
    timeout: "Timeout",
    service_unavailable: "Service unavailable",
    validation_error: "Validation error",
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

function List({ items, empty, renderItem }) {
  if (!items.length) {
    return <p className="empty-state">{empty}</p>;
  }
  return <div className="stack">{items.map(renderItem)}</div>;
}

function StatusPill({ value }) {
  return <span className="status-pill">{value}</span>;
}

function Field({ label, value }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input readOnly value={value ?? ""} />
    </label>
  );
}

export function NCP005Portal({ session, pathname, navigate, baseUrl = "", onLogout }) {
  const client = useMemo(() => createNovaCodeProNcp005Api({ baseUrl, session }), [baseUrl, session]);
  const route = useMemo(() => parseRoute(pathname), [pathname]);
  const [loadState, setLoadState] = useState("loading");
  const [loadError, setLoadError] = useState(null);
  const [requirements, setRequirements] = useState([]);
  const [requirementSets, setRequirementSets] = useState([]);
  const [knowledgeSpaces, setKnowledgeSpaces] = useState([]);
  const [knowledgeDocuments, setKnowledgeDocuments] = useState([]);
  const [coverage, setCoverage] = useState(null);
  const [searchHistory, setSearchHistory] = useState([]);
  const [activeRequirement, setActiveRequirement] = useState(null);
  const [activeDocument, setActiveDocument] = useState(null);
  const [activeRequirementReviews, setActiveRequirementReviews] = useState([]);
  const [activeRequirementApprovals, setActiveRequirementApprovals] = useState([]);
  const [activeRequirementCriteria, setActiveRequirementCriteria] = useState([]);
  const [activeRequirementComments, setActiveRequirementComments] = useState([]);
  const [activeDocumentReviews, setActiveDocumentReviews] = useState([]);
  const [activeDocumentApprovals, setActiveDocumentApprovals] = useState([]);
  const [activeDocumentComments, setActiveDocumentComments] = useState([]);
  const [activeTraceability, setActiveTraceability] = useState([]);
  const [actionError, setActionError] = useState(null);
  const [requirementDraft, setRequirementDraft] = useState({
    title: "",
    summary: "",
    type: "FUNCTIONAL",
    priority: "MEDIUM",
    source: "MANUAL",
    content: "",
  });
  const [documentDraft, setDocumentDraft] = useState({
    title: "",
    summary: "",
    content_type: "GENERAL_DOCUMENT",
    visibility: "WORKSPACE",
    classification: "INTERNAL",
    body: "",
  });
  const [searchDraft, setSearchDraft] = useState({ query: "", strategy: "hybrid" });
  const [statusFilter, setStatusFilter] = useState("ALL");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoadState("loading");
      setLoadError(null);
      try {
        const [setList, reqList, spaceList, docList, coverageData, history] = await Promise.all([
          client.listRequirementSets(),
          client.listRequirements(),
          client.listKnowledgeSpaces(),
          client.listKnowledgeDocuments(undefined, {}),
          client.getTraceabilityCoverage(),
          client.listSearchHistory(),
        ]);
        if (cancelled) {
          return;
        }
        setRequirementSets(setList);
        setRequirements(reqList);
        setKnowledgeSpaces(spaceList);
        setKnowledgeDocuments(docList);
        setCoverage(coverageData);
        setSearchHistory(history);
        setLoadState(reqList.length || docList.length ? "ready" : "empty");
        setRequirementDraft((current) => ({ ...current, title: current.title || "New requirement" }));
        setDocumentDraft((current) => ({ ...current, title: current.title || "Knowledge document" }));
        if (route.section === "requirements" && route.subRoute !== "/" && !route.subRoute.startsWith("/new")) {
          const req = await client.getRequirement(route.subRoute.replace(/^\//, ""));
          if (!cancelled) {
            setActiveRequirement(req);
            setActiveRequirementReviews(await client.listRequirementReviews(req.id));
            setActiveRequirementApprovals(await client.listRequirementApprovals(req.id));
            setActiveRequirementCriteria(await client.listAcceptanceCriteria(req.id));
            setActiveRequirementComments(await client.listRequirementComments(req.id));
            setActiveTraceability(await client.listTraceabilityLinks());
          }
        }
        if (route.section === "knowledge" && route.subRoute !== "/" && !route.subRoute.startsWith("/new") && !route.subRoute.startsWith("/search")) {
          const doc = await client.getKnowledgeDocument(route.subRoute.replace(/^\//, ""));
          if (!cancelled) {
            setActiveDocument(doc);
            setActiveDocumentReviews(await client.listKnowledgeReviews(doc.id));
            setActiveDocumentApprovals(await client.listKnowledgeApprovals(doc.id));
            setActiveDocumentComments(await client.listKnowledgeComments(doc.id));
            setActiveTraceability(await client.listTraceabilityLinks());
          }
        }
      } catch (error) {
        if (!cancelled) {
          setLoadError(error);
          setLoadState(error.status === 401 ? "unauthorized" : error.status === 403 ? "forbidden" : error.status === 404 ? "not_found" : "service_unavailable");
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [client, route.section, route.subRoute]);

  async function submitRequirement(event) {
    event.preventDefault();
    setActionError(null);
    setLoadState("loading");
    try {
      const created = await client.createRequirement({
        title: requirementDraft.title,
        summary: requirementDraft.summary,
        type: requirementDraft.type,
        priority: requirementDraft.priority,
        source: requirementDraft.source,
        content: { body: requirementDraft.content },
      });
      navigate(`/novacodepro/requirements/${encodeURIComponent(created.id)}`);
    } catch (error) {
      setActionError(error);
      setLoadState("ready");
    }
  }

  async function submitDocument(event) {
    event.preventDefault();
    setActionError(null);
    setLoadState("loading");
    try {
      const created = await client.createKnowledgeDocument({
        title: documentDraft.title,
        summary: documentDraft.summary,
        content_type: documentDraft.content_type,
        visibility: documentDraft.visibility,
        classification: documentDraft.classification,
        body: documentDraft.body,
        space_id: knowledgeSpaces[0]?.id || "workspace-knowledge",
      });
      navigate(`/novacodepro/knowledge/documents/${encodeURIComponent(created.id)}`);
    } catch (error) {
      setActionError(error);
      setLoadState("ready");
    }
  }

  async function runSearch(event) {
    event.preventDefault();
    setActionError(null);
    try {
      const result = await client.searchKnowledge({
        query: searchDraft.query,
        strategy: searchDraft.strategy,
        maximum_results: 10,
      });
      setSearchHistory((current) => [{ query: searchDraft.query, at: new Date().toISOString() }, ...current].slice(0, 8));
      setKnowledgeDocuments(result.results || []);
      setLoadState("ready");
    } catch (error) {
      setActionError(error);
    }
  }

  const filteredRequirements = statusFilter === "ALL" ? requirements : requirements.filter((item) => String(item.status || "").toUpperCase() === statusFilter);

  return (
    <div className="app-shell novacodepro-ncp005">
      <header className="topbar">
        <div className="brand-block">
          <img className="brand-logo" src="/brand/NOVACODEPRO.webp" alt="NovaCodePro logo" />
          <div>
            <p className="eyebrow">NovaCodePro internal development platform</p>
            <strong>Requirements Manager + Knowledge Hub</strong>
          </div>
        </div>
        <div className="topbar-actions">
          <button type="button" className="toolbar-chip" onClick={() => navigate("/novacodepro/requirements")}>Requirements</button>
          <button type="button" className="toolbar-chip" onClick={() => navigate("/novacodepro/knowledge")}>Knowledge</button>
          <button type="button" className="toolbar-chip" onClick={() => onLogout()}>Logout</button>
        </div>
      </header>

      <main className="content-grid">
        <StateBanner state={loadState} error={loadError || actionError} />
        <section className="sidebar">
          <Panel
            title="Navigator"
            aside={
              <div className="chip-cloud">
                <StatusPill value={session?.active_role || session?.role || "UNKNOWN"} />
                <StatusPill value={session?.tenant_id || session?.organization_id || "novatech"} />
                <StatusPill value={route.section} />
              </div>
            }
          >
            <div className="stack">
              <button type="button" className={route.section === "requirements" ? "secondary-action active" : "secondary-action"} onClick={() => navigate("/novacodepro/requirements")}>Requirements</button>
              <button type="button" className={route.section === "knowledge" ? "secondary-action active" : "secondary-action"} onClick={() => navigate("/novacodepro/knowledge")}>Knowledge</button>
              <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/knowledge/search")}>Knowledge search</button>
              <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/requirements/new")}>New requirement</button>
              <button type="button" className="secondary-action" onClick={() => navigate("/novacodepro/knowledge/documents/new")}>New document</button>
            </div>
          </Panel>

          <Panel title="Traceability coverage" aside={coverage?.coverage_ratio != null ? <StatusPill value={`${Math.round(coverage.coverage_ratio * 100)}%`} /> : null}>
            {coverage ? (
              <div className="artifact-list">
                {Object.entries(coverage.coverage || {}).map(([key, value]) => (
                  <div className="artifact-row" key={key}>
                    <strong>{key}</strong>
                    <span>{String(value)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">No coverage data yet.</p>
            )}
          </Panel>

          <Panel title="Recent searches">
            <List
              items={searchHistory}
              empty="No searches yet."
              renderItem={(item, index) => (
                <div className="audit-row" key={`${item.query || "search"}-${index}`}>
                  <strong>{item.query || "Search"}</strong>
                  <p>{item.at || item.updated_at || ""}</p>
                </div>
              )}
            />
          </Panel>
        </section>

        <section className="main-content">
          {route.section === "knowledge" && route.subRoute.startsWith("/search") ? (
            <Panel title="Knowledge search">
              <form className="form-grid" onSubmit={runSearch}>
                <label className="form-field">
                  <span>Query</span>
                  <input value={searchDraft.query} onChange={(event) => setSearchDraft((current) => ({ ...current, query: event.target.value }))} />
                </label>
                <label className="form-field">
                  <span>Strategy</span>
                  <select value={searchDraft.strategy} onChange={(event) => setSearchDraft((current) => ({ ...current, strategy: event.target.value }))}>
                    <option value="keyword">Keyword</option>
                    <option value="semantic">Semantic</option>
                    <option value="hybrid">Hybrid</option>
                  </select>
                </label>
                <button type="submit" className="primary-action">Search</button>
              </form>
              <List
                items={knowledgeDocuments}
                empty="No results."
                renderItem={(document) => (
                  <button
                    key={document.id}
                    type="button"
                    className="list-link"
                    onClick={() => navigate(`/novacodepro/knowledge/documents/${encodeURIComponent(document.id)}`)}
                  >
                    <strong>{document.title || document.name || document.id}</strong>
                    <span>{document.classification || "INTERNAL"} · {document.status || "DRAFT"}</span>
                  </button>
                )}
              />
            </Panel>
          ) : route.section === "knowledge" && route.subRoute.startsWith("/documents/new") ? (
            <Panel title="Create knowledge document">
              <form className="form-grid" onSubmit={submitDocument}>
                <Field label="Title" value={documentDraft.title} />
                <label className="form-field">
                  <span>Title</span>
                  <input value={documentDraft.title} onChange={(event) => setDocumentDraft((current) => ({ ...current, title: event.target.value }))} />
                </label>
                <label className="form-field">
                  <span>Summary</span>
                  <input value={documentDraft.summary} onChange={(event) => setDocumentDraft((current) => ({ ...current, summary: event.target.value }))} />
                </label>
                <label className="form-field">
                  <span>Type</span>
                  <select value={documentDraft.content_type} onChange={(event) => setDocumentDraft((current) => ({ ...current, content_type: event.target.value }))}>
                    <option value="GENERAL_DOCUMENT">GENERAL_DOCUMENT</option>
                    <option value="ADR">ADR</option>
                    <option value="RUNBOOK">RUNBOOK</option>
                    <option value="POLICY">POLICY</option>
                    <option value="ARCHITECTURE_DOCUMENT">ARCHITECTURE_DOCUMENT</option>
                    <option value="POSTMORTEM">POSTMORTEM</option>
                    <option value="RELEASE_NOTE">RELEASE_NOTE</option>
                  </select>
                </label>
                <label className="form-field">
                  <span>Classification</span>
                  <select value={documentDraft.classification} onChange={(event) => setDocumentDraft((current) => ({ ...current, classification: event.target.value }))}>
                    <option value="INTERNAL">INTERNAL</option>
                    <option value="CONFIDENTIAL">CONFIDENTIAL</option>
                    <option value="RESTRICTED">RESTRICTED</option>
                    <option value="REGULATED">REGULATED</option>
                  </select>
                </label>
                <label className="form-field">
                  <span>Visibility</span>
                  <select value={documentDraft.visibility} onChange={(event) => setDocumentDraft((current) => ({ ...current, visibility: event.target.value }))}>
                    <option value="WORKSPACE">WORKSPACE</option>
                    <option value="ORGANIZATION">ORGANIZATION</option>
                    <option value="PARTNER">PARTNER</option>
                    <option value="CUSTOMER">CUSTOMER</option>
                    <option value="PUBLIC">PUBLIC</option>
                  </select>
                </label>
                <label className="form-field">
                  <span>Body</span>
                  <textarea value={documentDraft.body} onChange={(event) => setDocumentDraft((current) => ({ ...current, body: event.target.value }))} rows={8} />
                </label>
                <button type="submit" className="primary-action">Create document</button>
              </form>
            </Panel>
          ) : route.section === "knowledge" && route.subRoute !== "/" && route.subRoute.startsWith("/documents/") ? (
            <Panel title={activeDocument?.title || "Knowledge document"} aside={<StatusPill value={activeDocument?.status || "DRAFT"} />}>
              <div className="dual-grid">
                <article className="output-card">
                  <div className="artifact-list">
                    {[
                      ["Type", activeDocument?.content_type],
                      ["Classification", activeDocument?.classification],
                      ["Visibility", activeDocument?.visibility],
                      ["Version", activeDocument?.version],
                    ].map(([label, value]) => (
                      <div className="artifact-row" key={label}>
                        <strong>{label}</strong>
                        <span>{String(value || "")}</span>
                      </div>
                    ))}
                  </div>
                  <p className="studio-note">{activeDocument?.summary || "No summary provided."}</p>
                  <pre className="code-block">{JSON.stringify(activeDocument?.content || activeDocument?.body || {}, null, 2)}</pre>
                </article>
                <article className="output-card">
                  <h3>Citations and provenance</h3>
                  <List
                    items={activeDocument?.citations || []}
                    empty="No citations."
                    renderItem={(citation, index) => (
                      <div className="audit-row" key={citation.citation_id || index}>
                        <strong>{citation.source_title || citation.source_type || "Citation"}</strong>
                        <p>{citation.source_uri || citation.quoted_digest || ""}</p>
                      </div>
                    )}
                  />
                </article>
              </div>
            </Panel>
          ) : route.section === "requirements" && route.subRoute.startsWith("/new") ? (
            <Panel title="Create requirement">
              <form className="form-grid" onSubmit={submitRequirement}>
                <label className="form-field">
                  <span>Title</span>
                  <input value={requirementDraft.title} onChange={(event) => setRequirementDraft((current) => ({ ...current, title: event.target.value }))} />
                </label>
                <label className="form-field">
                  <span>Summary</span>
                  <input value={requirementDraft.summary} onChange={(event) => setRequirementDraft((current) => ({ ...current, summary: event.target.value }))} />
                </label>
                <label className="form-field">
                  <span>Type</span>
                  <select value={requirementDraft.type} onChange={(event) => setRequirementDraft((current) => ({ ...current, type: event.target.value }))}>
                    {["BUSINESS", "FUNCTIONAL", "NON_FUNCTIONAL", "SECURITY", "PRIVACY", "COMPLIANCE", "OPERATIONAL", "OBSERVABILITY"].map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>Priority</span>
                  <select value={requirementDraft.priority} onChange={(event) => setRequirementDraft((current) => ({ ...current, priority: event.target.value }))}>
                    {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((priority) => (
                      <option key={priority} value={priority}>{priority}</option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>Source</span>
                  <select value={requirementDraft.source} onChange={(event) => setRequirementDraft((current) => ({ ...current, source: event.target.value }))}>
                    {["MANUAL", "REQUEST", "AI_GENERATED", "IMPORT", "POLICY", "REGULATION", "INCIDENT", "AUDIT", "CUSTOMER"].map((source) => (
                      <option key={source} value={source}>{source}</option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>Content</span>
                  <textarea value={requirementDraft.content} onChange={(event) => setRequirementDraft((current) => ({ ...current, content: event.target.value }))} rows={8} />
                </label>
                <button type="submit" className="primary-action">Create requirement</button>
              </form>
            </Panel>
          ) : route.section === "requirements" && route.subRoute !== "/" ? (
            <Panel title={activeRequirement?.title || "Requirement"} aside={<StatusPill value={activeRequirement?.status || "DRAFT"} />}>
              <div className="dual-grid">
                <article className="output-card">
                  <div className="artifact-list">
                    {[
                      ["Type", activeRequirement?.type],
                      ["Priority", activeRequirement?.priority],
                      ["Source", activeRequirement?.source],
                      ["Version", activeRequirement?.version],
                    ].map(([label, value]) => (
                      <div className="artifact-row" key={label}>
                        <strong>{label}</strong>
                        <span>{String(value || "")}</span>
                      </div>
                    ))}
                  </div>
                  <p className="studio-note">{activeRequirement?.summary || "No summary provided."}</p>
                </article>
                <article className="output-card">
                  <h3>Reviews and approvals</h3>
                  <List
                    items={[...activeRequirementReviews, ...activeRequirementApprovals]}
                    empty="No governance items."
                    renderItem={(item, index) => (
                      <div className="audit-row" key={item.id || index}>
                        <strong>{item.review_type || item.required_role || "Governance"}</strong>
                        <p>{item.status || item.decision || ""}</p>
                      </div>
                    )}
                  />
                </article>
              </div>
              <div className="dual-grid">
                <article className="output-card">
                  <h3>Acceptance criteria</h3>
                  <List
                    items={activeRequirementCriteria}
                    empty="No criteria."
                    renderItem={(criterion, index) => (
                      <div className="audit-row" key={criterion.id || index}>
                        <strong>{criterion.description || criterion.criterion_type || "Criterion"}</strong>
                        <p>{criterion.status || ""}</p>
                      </div>
                    )}
                  />
                </article>
                <article className="output-card">
                  <h3>Comments</h3>
                  <List
                    items={activeRequirementComments}
                    empty="No comments."
                    renderItem={(comment, index) => (
                      <div className="audit-row" key={comment.id || index}>
                        <strong>{comment.author || comment.created_by || "Comment"}</strong>
                        <p>{comment.body || ""}</p>
                      </div>
                    )}
                  />
                </article>
              </div>
            </Panel>
          ) : (
            <Panel
              title="Requirements overview"
              aside={
                <div className="chip-cloud">
                  {["ALL", "DRAFT", "IN_REVIEW", "APPROVAL_REQUIRED", "APPROVED", "BASELINED", "VERIFIED", "ARCHIVED"].map((status) => (
                    <button
                      key={status}
                      type="button"
                      className={statusFilter === status ? "context-chip active" : "context-chip"}
                      onClick={() => setStatusFilter(status)}
                    >
                      {status}
                    </button>
                  ))}
                </div>
              }
            >
              <div className="dual-grid">
                <article className="output-card">
                  <h3>Requirement sets</h3>
                  <List
                    items={requirementSets}
                    empty="No requirement sets."
                    renderItem={(item) => (
                      <button key={item.id} type="button" className="list-link" onClick={() => navigate(`/novacodepro/requirements/${encodeURIComponent(item.id)}`)}>
                        <strong>{item.name || item.title || item.id}</strong>
                        <span>{item.status || "DRAFT"}</span>
                      </button>
                    )}
                  />
                </article>
                <article className="output-card">
                  <h3>Requirements</h3>
                  <List
                    items={filteredRequirements}
                    empty="No requirements."
                    renderItem={(item) => (
                      <button key={item.id} type="button" className="list-link" onClick={() => navigate(`/novacodepro/requirements/${encodeURIComponent(item.id)}`)}>
                        <strong>{item.title || item.summary || item.id}</strong>
                        <span>{item.type || "FUNCTIONAL"} · {item.status || "DRAFT"}</span>
                      </button>
                    )}
                  />
                </article>
              </div>
              <div className="dual-grid">
                <article className="output-card">
                  <h3>Knowledge spaces</h3>
                  <List
                    items={knowledgeSpaces}
                    empty="No knowledge spaces."
                    renderItem={(item) => (
                      <button key={item.id} type="button" className="list-link" onClick={() => navigate(`/novacodepro/knowledge/spaces/${encodeURIComponent(item.id)}`)}>
                        <strong>{item.name || item.title || item.id}</strong>
                        <span>{item.classification || "INTERNAL"}</span>
                      </button>
                    )}
                  />
                </article>
                <article className="output-card">
                  <h3>Knowledge documents</h3>
                  <List
                    items={knowledgeDocuments}
                    empty="No knowledge documents."
                    renderItem={(item) => (
                      <button key={item.id} type="button" className="list-link" onClick={() => navigate(`/novacodepro/knowledge/documents/${encodeURIComponent(item.id)}`)}>
                        <strong>{item.title || item.name || item.id}</strong>
                        <span>{item.content_type || item.classification || "DOCUMENT"}</span>
                      </button>
                    )}
                  />
                </article>
              </div>
              <article className="output-card">
                <h3>Traceability links</h3>
                <List
                  items={activeTraceability}
                  empty="No traceability links."
                  renderItem={(item, index) => (
                    <div className="audit-row" key={item.id || index}>
                      <strong>{item.relationship || item.link_type || "Link"}</strong>
                      <p>{item.source_type || item.target_type || ""}</p>
                    </div>
                  )}
                />
              </article>
            </Panel>
          )}
        </section>
      </main>
    </div>
  );
}
