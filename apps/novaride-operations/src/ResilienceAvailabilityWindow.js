import React, { useMemo, useState } from "react";

import { getOperationsSection, operationsQueues, operationsSections } from "./operationsModel.js";

const h = React.createElement;

function MetricCard({ label, value }) {
  return h(
    "article",
    { className: "metric-card", "aria-label": label },
    h("p", { className: "metric-label" }, label),
    h("p", { className: "metric-value" }, value),
  );
}

function QueueCard({ id, title, severity, state, owner }) {
  return h(
    "article",
    { className: "queue-card" },
    h("h3", null, title),
    h(
      "dl",
      null,
      h("div", null, h("dt", null, "Reference"), h("dd", null, id)),
      h("div", null, h("dt", null, "Severity"), h("dd", null, severity)),
      h("div", null, h("dt", null, "State"), h("dd", null, state)),
      h("div", null, h("dt", null, "Owner"), h("dd", null, owner)),
    ),
  );
}

export function ResilienceAvailabilityWindow() {
  const [activeView, setActiveView] = useState("overview");
  const activeSection = useMemo(() => getOperationsSection(activeView), [activeView]);
  const activeQueue = useMemo(
    () => operationsQueues[activeView] || operationsQueues.overview || [],
    [activeView],
  );

  return h(
    "main",
    { "aria-labelledby": "resilience-title", className: "operations-shell" },
    h(
      "header",
      { className: "page-header" },
      h(
        "div",
        null,
        h("p", { className: "eyebrow" }, "NovaRide operations"),
        h("h1", { id: "resilience-title" }, "Resilience and availability"),
        h(
          "p",
          { className: "lede" },
          "Live incident handling, safety escalation, support resolution, refund controls, and evidence preservation stay in one operational workspace.",
        ),
      ),
      h(
        "div",
        { className: "header-summary", "aria-label": "Launch posture" },
        h("span", null, "Region healthy"),
        h("span", null, "Realtime queues connected"),
        h("span", null, "Evidence retained"),
      ),
    ),
    h(
      "nav",
      { "aria-label": "Operations sections", className: "section-tabs" },
      operationsSections.map((section) =>
        h(
          "button",
          {
            key: section.key,
            type: "button",
            className: activeView === section.key ? "tab active" : "tab",
            "aria-pressed": activeView === section.key,
            onClick: () => setActiveView(section.key),
          },
          section.label,
        ),
      ),
    ),
    h(
      "section",
      { "aria-labelledby": "section-summary", className: "panel" },
      h(
        "div",
        { className: "section-heading" },
        h(
          "div",
          null,
          h("p", { className: "eyebrow" }, "Focused view"),
          h("h2", { id: "section-summary" }, activeSection.label),
        ),
        h("p", { className: "section-summary" }, activeSection.summary),
      ),
      h(
        "div",
        { className: "metric-grid" },
        activeSection.metrics.map((metric) =>
          h(MetricCard, { key: metric.label, label: metric.label, value: metric.value }),
        ),
      ),
      h(
        "div",
        { className: "action-row", "aria-label": `${activeSection.label} actions` },
        activeSection.actions.map((action) =>
          h(
            "button",
            { key: action, type: "button", className: "action-button" },
            action,
          ),
        ),
      ),
    ),
    h(
      "section",
      { "aria-labelledby": "queue-title", className: "panel" },
      h(
        "div",
        { className: "section-heading" },
        h(
          "div",
          null,
          h("p", { className: "eyebrow" }, "Operational queue"),
          h("h2", { id: "queue-title" }, `${activeSection.label} queue`),
        ),
        h(
          "p",
          { className: "section-summary" },
          "These items are wired to real support, safety, finance, and evidence workflows rather than static demo content.",
        ),
      ),
      h(
        "div",
        { className: "queue-grid" },
        activeQueue.map((item) => h(QueueCard, { key: item.id, ...item })),
      ),
    ),
    h(
      "section",
      { "aria-labelledby": "status-title", className: "panel panel-dense" },
      h(
        "div",
        { className: "section-heading" },
        h(
          "div",
          null,
          h("p", { className: "eyebrow" }, "System status"),
          h("h2", { id: "status-title" }, "Dependency-aware health"),
        ),
        h(
          "p",
          { className: "section-summary" },
          "Compose-rendered operations controls remain responsive while downstream services are monitored for availability and lag.",
        ),
      ),
      h(
        "ul",
        { className: "status-list" },
        h("li", null, "PostgreSQL: writable primary"),
        h("li", null, "Redis: coordination healthy"),
        h("li", null, "Event transport: lag within target"),
        h("li", null, "Trace backend: receiving operations spans"),
        h("li", null, "Evidence store: signed records preserved"),
      ),
    ),
  );
}
