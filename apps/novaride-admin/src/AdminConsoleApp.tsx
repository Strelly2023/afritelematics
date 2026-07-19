import React, { useMemo, useState } from "react";

const controls = [
  "Pause region",
  "Freeze pricing",
  "Restrict new drivers",
  "Review incidents",
  "Export audit pack",
  "Open replay viewer",
] as const;

const views = [
  { id: "regions", label: "Regions" },
  { id: "incidents", label: "Incidents" },
  { id: "evidence", label: "Evidence" },
] as const;

type AdminConsoleAppProps = {
  authorized?: boolean;
  backendAvailable?: boolean;
  onSwitch?: (action: (typeof controls)[number], reason: string) => void;
};

export function AdminConsoleApp({
  authorized = true,
  backendAvailable = false,
  onSwitch,
}: AdminConsoleAppProps): JSX.Element {
  const [activeView, setActiveView] = useState<(typeof views)[number]["id"]>("regions");
  const [reason, setReason] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);
  const [statusMessage, setStatusMessage] = useState(
    backendAvailable
      ? "Governed admin actions are available."
      : "Backend unavailable: operational switches are disabled in this runtime shell.",
  );

  const activeViewLabel = useMemo(
    () => views.find((view) => view.id === activeView)?.label ?? "Regions",
    [activeView],
  );

  if (!authorized) {
    return (
      <main className="admin-console" aria-labelledby="admin-console-title">
        <header>
          <h1 id="admin-console-title">NovaRide Admin Console</h1>
          <p role="alert">Access denied. NovaID authorization is required for administrative controls.</p>
        </header>
      </main>
    );
  }

  function submitSwitch(action: (typeof controls)[number]): void {
    if (!backendAvailable) {
      setStatusMessage(`${action} unavailable until the governed admin API is connected.`);
      return;
    }
    onSwitch?.(action, reason.trim());
    setStatusMessage(`${action} recorded with reason: ${reason.trim()}.`);
  }

  return (
    <main className="admin-console" aria-labelledby="admin-console-title">
      <header>
        <h1 id="admin-console-title">NovaRide Admin Console</h1>
        <p>Governed controls for release health, region operations, incident response, and audit evidence.</p>
        <p role="status">{statusMessage}</p>
      </header>
      <nav aria-label="Admin sections" className="tab-list">
        {views.map((view) => (
          <button
            aria-pressed={view.id === activeView}
            key={view.id}
            type="button"
            onClick={() => {
              setActiveView(view.id);
              setStatusMessage(`Viewing ${view.label.toLowerCase()} controls.`);
            }}
          >
            {view.label}
          </button>
        ))}
      </nav>
      <section aria-label="Admin controls">
        <h2>{activeViewLabel}</h2>
        <p>All privileged actions require NovaID authentication, policy evaluation, confirmation, and audit logging.</p>
        <label htmlFor="admin-reason">Operator reason</label>
        <textarea
          id="admin-reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="Explain the operational reason"
          rows={4}
        />
        <label className="checkbox-row">
          <input checked={acknowledged} type="checkbox" onChange={(event) => setAcknowledged(event.target.checked)} />
          I confirm this action is authorized and time-bounded.
        </label>
        <div className="control-grid">
          {controls.map((item) => (
            <button
              disabled={!backendAvailable || reason.trim().length < 8 || !acknowledged}
              key={item}
              type="button"
              onClick={() => submitSwitch(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
