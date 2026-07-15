import React from "react";

type Mode = "NORMAL" | "DEGRADED" | "OFFLINE" | "EMERGENCY_ONLY" | "RECOVERING";

type Panel = {
  label: string;
  value: string;
  mode: Mode;
};

const panels: Panel[] = [
  { label: "Global availability", value: "99.95%", mode: "NORMAL" },
  { label: "Availability zones", value: "3 active", mode: "NORMAL" },
  { label: "Emergency path", value: "available", mode: "NORMAL" },
  { label: "Provider fallback traffic", value: "low", mode: "NORMAL" },
  { label: "Circuit breakers", value: "0 open", mode: "NORMAL" },
  { label: "Offline queue", value: "0 oldest", mode: "NORMAL" },
  { label: "Conflict backlog", value: "0 unresolved", mode: "NORMAL" },
  { label: "PostgreSQL", value: "primary writable", mode: "NORMAL" },
  { label: "Kafka", value: "lag within SLO", mode: "NORMAL" },
  { label: "Evidence receipts", value: "publishing", mode: "NORMAL" },
];

const actions = [
  "Probe provider",
  "Drain provider",
  "Restore provider",
  "Open circuit",
  "Close circuit",
  "Start reconciliation",
  "Pause low-priority synchronization",
  "Resume synchronization",
  "Evaluate failover",
  "Request failover approval",
  "Execute authorized failover",
  "Enable degraded mode",
  "Request emergency-only mode",
  "Open incident",
  "Broadcast customer message",
];

function modeLabel(mode: Mode): string {
  return `${mode.replace("_", " ")} status`;
}

export function ResilienceAvailabilityWindow(): JSX.Element {
  return (
    <main aria-labelledby="resilience-title" className="resilience-window">
      <h1 id="resilience-title">Resilience and Availability</h1>
      <section aria-label="Operational status panels" className="panel-grid">
        {panels.map((panel) => (
          <article className={`panel mode-${panel.mode.toLowerCase()}`} key={panel.label}>
            <h2>{panel.label}</h2>
            <p>{panel.value}</p>
            <span aria-label={modeLabel(panel.mode)}>{panel.mode}</span>
          </article>
        ))}
      </section>
      <section aria-label="Controlled operations">
        <h2>Actions</h2>
        <div className="action-grid">
          {actions.map((action) => (
            <button type="button" key={action} aria-label={action}>
              {action}
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
