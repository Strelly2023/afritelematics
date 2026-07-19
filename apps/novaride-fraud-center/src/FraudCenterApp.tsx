import React, { useMemo, useState } from "react";

type CaseStatus = "TRIAGE" | "INVESTIGATING" | "HOLD" | "CLOSED";

type QueueItem = {
  id: string;
  title: string;
  risk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: CaseStatus;
  signal: string;
};

const queue: QueueItem[] = [
  {
    id: "FC-001",
    title: "Potential account takeover",
    risk: "CRITICAL",
    status: "INVESTIGATING",
    signal: "New device, failed OTP, payout change",
  },
  {
    id: "FC-002",
    title: "Suspicious GPS pattern",
    risk: "HIGH",
    status: "TRIAGE",
    signal: "Route deviation, repeated route resets",
  },
  {
    id: "FC-003",
    title: "Promo abuse cluster",
    risk: "MEDIUM",
    status: "HOLD",
    signal: "Related accounts, repeated redemption",
  },
  {
    id: "FC-004",
    title: "Duplicate charge complaint",
    risk: "HIGH",
    status: "CLOSED",
    signal: "Payment webhook deduplicated, refund issued",
  },
];

const controls = [
  "Assign analyst",
  "Escalate to safety",
  "Freeze payout",
  "Step-up verification",
  "Suspend account",
  "Release hold",
  "Request appeal",
  "Export evidence",
] as const;

type FraudCenterAppProps = {
  authorized?: boolean;
  backendAvailable?: boolean;
  onAction?: (caseId: string, action: (typeof controls)[number]) => void;
};

function riskTone(risk: QueueItem["risk"]): string {
  return `risk-${risk.toLowerCase()}`;
}

export function FraudCenterApp({
  authorized = true,
  backendAvailable = false,
  onAction,
}: FraudCenterAppProps): JSX.Element {
  const [selectedCaseId, setSelectedCaseId] = useState(queue[0].id);
  const [statusMessage, setStatusMessage] = useState(
    backendAvailable
      ? "Fraud review actions are ready."
      : "Backend unavailable: actions are disabled in this runtime shell.",
  );

  const selectedCase = useMemo(
    () => queue.find((item) => item.id === selectedCaseId) ?? queue[0],
    [selectedCaseId],
  );

  if (!authorized) {
    return (
      <main className="fraud-center" aria-labelledby="fraud-center-title">
        <header className="fraud-hero">
          <h1 id="fraud-center-title">NovaRide Fraud Center</h1>
          <p role="alert">Access denied. NovaID authorization is required to view fraud cases.</p>
        </header>
      </main>
    );
  }

  function handleAction(action: (typeof controls)[number]): void {
    if (!backendAvailable) {
      setStatusMessage(`${action} unavailable until the governed fraud API is connected.`);
      return;
    }
    onAction?.(selectedCase.id, action);
    setStatusMessage(`${action} queued for ${selectedCase.id}.`);
  }

  return (
    <main className="fraud-center" aria-labelledby="fraud-center-title">
      <header className="fraud-hero">
        <h1 id="fraud-center-title">NovaRide Fraud Center</h1>
        <p>Evidence-led queue management for account takeover, GPS anomalies, promo abuse, and payment disputes.</p>
        <p role="status">{statusMessage}</p>
      </header>
      <section aria-label="Case queue" className="queue-grid">
        {queue.map((item) => (
          <button
            aria-pressed={item.id === selectedCase.id}
            className={`case-card ${riskTone(item.risk)}`}
            key={item.id}
            type="button"
            onClick={() => {
              setSelectedCaseId(item.id);
              setStatusMessage(`Selected ${item.id} for evidence review.`);
            }}
          >
            <div className="case-heading">
              <strong>{item.id}</strong>
              <span>{item.status}</span>
            </div>
            <h2>{item.title}</h2>
            <p>{item.signal}</p>
            <footer>
              <span>{item.risk} risk</span>
            </footer>
          </button>
        ))}
      </section>
      <section aria-label="Selected case details">
        <h2>Selected case</h2>
        <dl>
          <div>
            <dt>Case</dt>
            <dd>{selectedCase.id}</dd>
          </div>
          <div>
            <dt>Risk</dt>
            <dd>{selectedCase.risk}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{selectedCase.status}</dd>
          </div>
        </dl>
      </section>
      <section aria-label="Fraud controls">
        <h2>Actions</h2>
        <div className="control-grid">
          {controls.map((action) => (
            <button disabled={!backendAvailable} key={action} type="button" onClick={() => handleAction(action)}>
              {action}
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
