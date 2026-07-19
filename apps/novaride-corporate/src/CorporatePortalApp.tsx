import React, { useMemo, useState } from "react";

const policies = [
  "Department billing",
  "Travel approval",
  "Guest ride consent",
  "Ride pass entitlement",
  "Cost-centre reconciliation",
  "Monthly invoicing",
];

const views = [
  { id: "policy", label: "Policies" },
  { id: "billing", label: "Billing" },
  { id: "approvals", label: "Approvals" },
] as const;

type CorporatePortalAppProps = {
  authorized?: boolean;
  backendAvailable?: boolean;
  onApprove?: (scope: string, reason: string) => void;
};

export function CorporatePortalApp({
  authorized = true,
  backendAvailable = false,
  onApprove,
}: CorporatePortalAppProps): JSX.Element {
  const [activeView, setActiveView] = useState<(typeof views)[number]["id"]>("policy");
  const [reason, setReason] = useState("");
  const [statusMessage, setStatusMessage] = useState(
    backendAvailable
      ? "Corporate governance backend connected."
      : "Backend unavailable: approvals are disabled in this runtime shell.",
  );

  const activeViewLabel = useMemo(
    () => views.find((view) => view.id === activeView)?.label ?? "Policies",
    [activeView],
  );

  if (!authorized) {
    return (
      <main className="corporate-portal" aria-labelledby="corporate-portal-title">
        <header>
          <h1 id="corporate-portal-title">NovaRide Corporate Portal</h1>
          <p role="alert">Access denied. NovaID authorization is required for corporate controls.</p>
        </header>
      </main>
    );
  }

  function submitApproval(): void {
    if (!backendAvailable) {
      setStatusMessage("Approval unavailable until the governed corporate API is connected.");
      return;
    }
    onApprove?.("department-billing", reason.trim());
    setStatusMessage(`Approval submitted for department billing: ${reason.trim()}.`);
  }

  return (
    <main className="corporate-portal" aria-labelledby="corporate-portal-title">
      <header>
        <h1 id="corporate-portal-title">NovaRide Corporate Portal</h1>
        <p>Managed travel policy, guest ride control, and cost-centre billing for enterprise mobility.</p>
        <p role="status">{statusMessage}</p>
      </header>
      <nav aria-label="Corporate sections" className="tab-list">
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
      <section aria-label="Corporate controls" aria-live="polite">
        <h2>{activeViewLabel}</h2>
        {activeView === "policy" ? (
          <ul>
            {policies.map((policy) => (
              <li key={policy}>{policy}</li>
            ))}
          </ul>
        ) : null}
        {activeView === "billing" ? (
          <table>
            <tbody>
              <tr>
                <th scope="row">Active departments</th>
                <td>8</td>
              </tr>
              <tr>
                <th scope="row">Open invoices</th>
                <td>14</td>
              </tr>
              <tr>
                <th scope="row">Expense exports</th>
                <td>Monthly CSV and ERP feed</td>
              </tr>
            </tbody>
          </table>
        ) : null}
        {activeView === "approvals" ? (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              submitApproval();
            }}
          >
            <label htmlFor="approval-reason">Approval reason</label>
            <textarea
              id="approval-reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Explain why the travel request is approved"
              rows={4}
            />
            <button type="submit" disabled={!backendAvailable || reason.trim().length < 8}>
              Submit approval
            </button>
          </form>
        ) : null}
      </section>
    </main>
  );
}
