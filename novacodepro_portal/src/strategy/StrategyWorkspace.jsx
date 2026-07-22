import React, { useEffect, useMemo, useState } from "react";

import { ROUTES } from "../platform/routes.js";

const STRATEGY_SECTIONS = [
  {
    id: "vision",
    title: "Enterprise Vision",
    description: "Define the long-term platform direction, scope, and differentiating outcomes.",
    bullets: ["Narrative", "Success measures", "North-star outcomes", "Decision boundaries"],
  },
  {
    id: "goals",
    title: "Business Goals",
    description: "Translate the vision into measurable objectives, constraints, and target outcomes.",
    bullets: ["Growth", "Retention", "Trust", "Delivery predictability"],
  },
  {
    id: "market",
    title: "Market Research",
    description: "Capture segmentation, demand signals, stakeholder evidence, and launch assumptions.",
    bullets: ["Segments", "Research notes", "Signals", "Evidence"],
  },
  {
    id: "competition",
    title: "Competitive Analysis",
    description: "Compare alternatives, tradeoffs, and platform positioning with traceable evidence.",
    bullets: ["Peers", "Differentiators", "Threats", "Moats"],
  },
  {
    id: "business-case",
    title: "Business Case",
    description: "Track cost, revenue, risk, and value hypotheses before execution starts.",
    bullets: ["Cost model", "Revenue model", "Risk register", "Approval state"],
  },
  {
    id: "roadmap",
    title: "Product Roadmap",
    description: "Sequence strategic themes into time-bound initiatives and release windows.",
    bullets: ["Now", "Next", "Later", "Release gates"],
  },
  {
    id: "personas",
    title: "Customer Personas",
    description: "Keep the strategy grounded in distinct user types, goals, and friction points.",
    bullets: ["Primary personas", "Needs", "Pain points", "Accessibility"],
  },
  {
    id: "governance",
    title: "Program Governance",
    description: "Keep approvals, review status, audit trail, and traceability visible at all times.",
    bullets: ["Approval workflow", "Audit", "Traceability", "Owners"],
  },
];

const STRATEGY_TOOLS = [
  {
    id: "product-strategy-center",
    title: "Product Strategy Center",
    summary: "Draft the strategic narrative, market position, and success measures.",
  },
  {
    id: "roadmap-center",
    title: "Roadmap Center",
    summary: "Plan initiatives, dependencies, milestones, and release sequencing.",
  },
  {
    id: "market-regional-planning",
    title: "Market and Regional Planning",
    summary: "Compare localization, regulation, and launch order across regions.",
  },
  {
    id: "pricing-packaging-center",
    title: "Pricing and Packaging Center",
    summary: "Shape monetization scenarios and approval-ready commercial proposals.",
  },
  {
    id: "discovery-studio",
    title: "Discovery Studio",
    summary: "Capture hypotheses, interviews, and evidence-backed strategy input.",
  },
  {
    id: "requirements-center",
    title: "Requirements Center",
    summary: "Turn approved strategy into traceable requirements and release scope.",
  },
];

async function fetchJson(baseUrl, path, signal) {
  const response = await fetch(`${baseUrl}${path}`, {
    credentials: "include",
    signal,
    headers: {
      "x-requested-with": "fetch",
    },
  });
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const message = body?.detail?.message || body?.detail || "Unable to load strategy workspace.";
    throw new Error(typeof message === "string" ? message : "Unable to load strategy workspace.");
  }
  return body;
}

function ToolCard({ tool, onLaunch }) {
  return (
    <article className="studio-card">
      <p className="section-label">{tool.title}</p>
      <p>{tool.summary}</p>
      <button type="button" className="toolbar-chip" onClick={() => onLaunch(tool.id)}>
        Open tool
      </button>
    </article>
  );
}

export function StrategyWorkspace({ session, pathname, navigate, baseUrl = "", onLogout, strategySnapshot = null }) {
  const [snapshot, setSnapshot] = useState(strategySnapshot);
  const [state, setState] = useState(strategySnapshot ? "ready" : "loading");
  const [error, setError] = useState("");

  useEffect(() => {
    if (strategySnapshot) {
      setSnapshot(strategySnapshot);
      setState("ready");
      setError("");
      return undefined;
    }
    const controller = new AbortController();
    let cancelled = false;
    async function load() {
      setState("loading");
      setError("");
      try {
        const results = await Promise.allSettled([
          fetchJson(baseUrl, "/v1/novacodepro/workspace", controller.signal),
          fetchJson(baseUrl, "/v1/novacodepro/tools/product-strategy-center", controller.signal),
          fetchJson(baseUrl, "/v1/novacodepro/tools/roadmap-center", controller.signal),
          fetchJson(baseUrl, "/v1/novacodepro/tools/market-regional-planning", controller.signal),
          fetchJson(baseUrl, "/v1/novacodepro/tools/pricing-packaging-center", controller.signal),
          fetchJson(baseUrl, "/v1/novacodepro/tools/discovery-studio", controller.signal),
          fetchJson(baseUrl, "/v1/novacodepro/tools/requirements-center", controller.signal),
        ]);
        const [workspaceResult, ...toolResults] = results;
        if (cancelled) {
          return;
        }
        if (workspaceResult.status !== "fulfilled") {
          throw workspaceResult.reason;
        }
        setSnapshot({
          workspace: workspaceResult.value?.workspace || null,
          tools: toolResults.filter((item) => item.status === "fulfilled").map((item) => item.value),
        });
        setState("ready");
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        setState("error");
        setError(loadError?.message || "Unable to load strategy workspace.");
      }
    }
    load();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [baseUrl, strategySnapshot]);

  const workspace = snapshot?.workspace || session?.workspace || {};
  const tools = snapshot?.tools || [];
  const context = useMemo(
    () => [
      ["Organisation", session?.organization?.name || session?.organization?.id || "NovaTech"],
      ["Workspace", workspace?.title || workspace?.name || workspace?.id || "Strategy Workspace"],
      ["Product", workspace?.product_name || session?.product?.name || "NovaCodePro"],
      ["Branch", session?.branch || "main"],
      ["Environment", workspace?.selected_environment || session?.environment || "development"],
    ],
    [session, workspace],
  );

  const launchTool = (toolId) => {
    const origin = baseUrl ? baseUrl.replace(/\/+$/, "") : "";
    const target = `${origin}/novacodepro/tools/${encodeURIComponent(toolId)}`;
    window.location.assign(target);
  };

  const launchWorkspace = () => {
    navigate?.(ROUTES.strategyRoot);
  };

  return (
    <main className="app-shell studio-shell strategy-workspace" data-testid="strategy-workspace">
      <header className="topbar">
        <div className="brand-block">
          <img className="brand-logo" src="/brand/NOVACODEPRO.webp" alt="NovaCodePro logo" />
          <div>
            <p className="eyebrow">NovaCodePro strategy workspace</p>
            <strong>Enterprise Strategy Workspace</strong>
            <div className="topbar-context">
              {context.map(([label, value]) => (
                <span key={label}>
                  {label}: {value}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="topbar-actions">
          <button type="button" className="toolbar-chip" onClick={launchWorkspace}>
            Strategy home
          </button>
          <button type="button" className="toolbar-chip" onClick={() => navigate?.("/novacodepro/product-factory")}>
            Product Factory
          </button>
          <button type="button" className="toolbar-chip" onClick={() => onLogout?.()}>
            Log out
          </button>
        </div>
      </header>

      <section className="surface-band">
        <div className="band-header">
          <div>
            <p className="section-label">Phase 1</p>
            <h2>Strategy and planning</h2>
            <p className="window-summary">
              Enterprise vision, goals, market evidence, competitive analysis, business case, roadmap, personas, and governance.
            </p>
          </div>
          <div className="layout-hint">
            <span>{state === "ready" ? "Live backend tools connected" : "Loading authoritative manifests"}</span>
            <span>{workspace?.home_route || "/novacodepro/dashboard"}</span>
          </div>
        </div>

        {error ? (
          <div className="studio-note" role="alert">
            {error}
          </div>
        ) : null}

        <div className="center-grid">
          {STRATEGY_SECTIONS.map((section) => (
            <article className="center-card" key={section.id}>
              <p className="section-label">{section.title}</p>
              <p>{section.description}</p>
              <div className="chip-cloud">
                {section.bullets.map((bullet) => (
                  <span className="context-chip" key={bullet}>
                    {bullet}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="surface-band">
        <div className="band-header">
          <div>
            <p className="section-label">Authoritative tools</p>
            <h2>Backend-backed strategy surfaces</h2>
          </div>
        </div>
        <div className="center-grid">
          {tools.length ? tools.map((tool) => <ToolCard key={tool.id || tool.title} tool={{ id: tool.id || tool.tool?.id || "tool", title: tool.name || tool.title || "Tool", summary: tool.description || "Backend strategy surface." }} onLaunch={launchTool} />) : STRATEGY_TOOLS.map((tool) => <ToolCard key={tool.id} tool={tool} onLaunch={launchTool} />)}
        </div>
      </section>

      <section className="surface-band">
        <div className="band-header">
          <div>
            <p className="section-label">Traceability</p>
            <h2>Connect strategy to requirements, architecture, design, and release</h2>
          </div>
        </div>
        <div className="studio-grid">
          <article className="studio-card">
            <p className="section-label">Trace matrix</p>
            <strong>Business objective to release evidence</strong>
            <div className="artifact-list">
              {[
                ["Vision", "Business goals and success metrics"],
                ["Goals", "Requirements and acceptance criteria"],
                ["Market", "Competitor and segment evidence"],
                ["Roadmap", "Architecture, design, development, testing"],
                ["Governance", "Approvals, audits, evidence"],
              ].map(([label, detail]) => (
                <div className="artifact-row" key={label}>
                  <strong>{label}</strong>
                  <span>{detail}</span>
                </div>
              ))}
            </div>
          </article>
          <article className="studio-card">
            <p className="section-label">Approval workflow</p>
            <strong>Review, approve, and publish strategy decisions</strong>
            <div className="compact-list">
              {["Draft", "Review", "Approve", "Publish", "Track"].map((step) => (
                <span className="compact-pill" key={step}>
                  {step}
                </span>
              ))}
            </div>
            <p className="studio-note">
              Strategy remains governed until the workspace, roadmap, and downstream requirements are approved and audited.
            </p>
          </article>
        </div>
      </section>

      <footer className="status-bar">
        <span className="studio-status-item">
          <strong>Route</strong>
          <span>{pathname || ROUTES.strategyRoot}</span>
        </span>
        <span className="studio-status-item">
          <strong>State</strong>
          <span>{state}</span>
        </span>
      </footer>
    </main>
  );
}

export default StrategyWorkspace;
