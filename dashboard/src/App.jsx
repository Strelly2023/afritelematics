import React, { useEffect, useMemo, useState } from "react";

const API_BASE_URL =
  import.meta?.env?.VITE_AFRIRIDE_API_URL || "http://127.0.0.1:8000";
const TEST_MODE = import.meta?.env?.VITE_AFRIRIDE_TEST_MODE !== "false";
const APP_VERSION = import.meta?.env?.VITE_AFRIRIDE_APP_VERSION || "0.1";
const DEVICE_ID =
  import.meta?.env?.VITE_AFRIRIDE_DEVICE_ID || "operator-test-device";

const EMPTY_OPERATOR_STATE = {
  activeRides: [],
  replayHealth: {
    replay_success_rate: "0%",
    failures: 0,
    status: "NO_DATA",
  },
  evidence: {
    receipts_count: 0,
    trace_count: 0,
    missing_traces: 0,
  },
  guards: [],
};

const PROPOSALS = [
  {
    id: "PROP-1198",
    title: "Require payment before shipping",
    surface: "Order execution",
    status: "Governance required",
    replay: "PASS",
    contracts: "PASS",
    driftRisk: "LOW",
    rollback: "Available",
    approvals: "1 of 2",
    summary:
      "Moves shipment activation behind a confirmed payment receipt and preserves the existing cancellation path.",
  },
  {
    id: "PROP-1187",
    title: "Normalize driver event timestamps",
    surface: "Mobile event stream",
    status: "Rejected",
    replay: "PASS",
    contracts: "FAIL",
    driftRisk: "MEDIUM",
    rollback: "Ready",
    approvals: "0 of 1",
    summary:
      "Rejected because the proposed timestamp coercion weakened the event contract for offline trip recovery.",
  },
  {
    id: "PROP-1172",
    title: "Tighten dispatch retry boundary",
    surface: "Dispatch service",
    status: "Ready to execute",
    replay: "PASS",
    contracts: "PASS",
    driftRisk: "LOW",
    rollback: "Available",
    approvals: "2 of 2",
    summary:
      "Adds a governed retry ceiling and records decision evidence for every skipped dispatch attempt.",
  },
];

const GOVERNANCE_RULES = [
  {
    name: "Protected systems",
    value: "Payments, inventory, dispatch",
    detail: "Changes touching protected systems require explicit authority.",
  },
  {
    name: "Approval thresholds",
    value: "Low: 1 approver | High: 2 approvers",
    detail: "Risk decides the minimum decision record required before execution.",
  },
  {
    name: "Rollback policy",
    value: "Required",
    detail: "No governed change reaches execution without rollback readiness.",
  },
  {
    name: "Contract enforcement",
    value: "Strict",
    detail: "Contract failures block execution even when replay validation passes.",
  },
];

const CHANGE_HISTORY = [
  {
    time: "14:22",
    id: "PROP-1198",
    state: "Approved",
    detail: "Payment-before-shipping change approved with replay proof attached.",
  },
  {
    time: "14:20",
    id: "PROP-1187",
    state: "Rejected",
    detail: "Contract failure recorded against mobile event timestamp coercion.",
  },
  {
    time: "14:19",
    id: "DRIFT-043",
    state: "Resolved",
    detail: "Runtime drift mapped to proposal evidence and closed.",
  },
  {
    time: "14:18",
    id: "RB-031",
    state: "Rollback success",
    detail: "Rollback executed and decision record linked to the trust graph.",
  },
];

const EXECUTION_EVENTS = [
  {
    name: "OrderShipped",
    state: "Consistent",
    detail: "Runtime contract matched approved proposal behavior.",
  },
  {
    name: "PaymentProcessed",
    state: "Enforced",
    detail: "Payment receipt verified before downstream execution.",
  },
  {
    name: "DispatchRetrySkipped",
    state: "Recorded",
    detail: "Governed retry ceiling created a decision record.",
  },
];

function clientHeaders() {
  const eventId =
    globalThis.crypto && "randomUUID" in globalThis.crypto
      ? globalThis.crypto.randomUUID()
      : `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`;

  return {
    "X-AfriRide-Device-Id": DEVICE_ID,
    "X-AfriRide-App-Version": APP_VERSION,
    "X-AfriRide-Event-Id": eventId,
    "X-AfriRide-Client-Timestamp": new Date().toISOString(),
    "X-AfriRide-Test-Mode": String(TEST_MODE),
  };
}

async function readJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: clientHeaders(),
  });
  if (!response.ok) {
    throw new Error(`operator_fetch_failed:${path}`);
  }
  return response.json();
}

async function writeJson(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...clientHeaders(),
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`operator_post_failed:${path}`);
  }
  return response.json();
}

function normalizeActiveRides(payload) {
  const rides = payload.rides || payload.active_rides || [];
  return rides.map((ride) => ({
    rideId: ride.ride_id || ride.rideId,
    state: ride.state || ride.status,
    driverId: ride.driver_id || ride.driverId || ride.assigned_driver_id,
    riderId: ride.rider_id || ride.riderId || ride.passenger_id,
  }));
}

function normalizeGuards(payload) {
  const violations = payload.violations || payload.guards || [];
  return violations.map((violation, index) => ({
    id: violation.id || `${violation.type || "guard"}-${index}`,
    type: violation.type || violation.violation_type || "UNKNOWN",
    timestamp: violation.timestamp || violation.created_at || "unavailable",
    severity: violation.severity || "INFO",
  }));
}

function deriveTrustState(state) {
  const failures = Number(state.replayHealth.failures || 0);
  const missingTraces = Number(state.evidence.missing_traces || 0);
  const guardCount = state.guards.length;
  const successRate = String(state.replayHealth.replay_success_rate || "0%");
  const replayVerified =
    successRate === "100%" ||
    String(state.replayHealth.status || "").toUpperCase() === "VERIFIED";

  if (failures > 0 || missingTraces > 0 || guardCount > 0) {
    return {
      label: "Action required",
      tone: "warning",
      summary:
        "Trust is observable, but one or more validation, evidence, or governance signals need review.",
    };
  }

  if (replayVerified || Number(state.evidence.receipts_count || 0) > 0) {
    return {
      label: "Verified",
      tone: "success",
      summary:
        "Validation, governance evidence, and rollback readiness are aligned for current execution.",
    };
  }

  return {
    label: "Awaiting evidence",
    tone: "neutral",
    summary:
      "The trust surface is online and waiting for validation receipts, decision records, and replay evidence.",
  };
}

export default function OperatorDashboard() {
  const [state, setState] = useState(EMPTY_OPERATOR_STATE);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const [conversation, setConversation] = useState([
    {
      role: "system",
      text:
        "Ask why a change was approved, whether it was safe, what happened before it, or what would happen if it were rejected.",
      evidence: null,
    },
  ]);
  const [conversationInput, setConversationInput] = useState("Why was this ride approved?");
  const [conversationPending, setConversationPending] = useState(false);

  useEffect(() => {
    fetchOperatorState();
    const interval = setInterval(fetchOperatorState, 3000);
    return () => clearInterval(interval);
  }, []);

  async function fetchOperatorState() {
    try {
      const [activeRides, replayHealth, evidence, guards] = await Promise.all([
        readJson("/rides/active"),
        readJson("/system/replay/health"),
        readJson("/system/evidence"),
        readJson("/system/guards"),
      ]);

      setState({
        activeRides: normalizeActiveRides(activeRides),
        replayHealth,
        evidence,
        guards: normalizeGuards(guards),
      });
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "operator_fetch_failed");
    }
  }

  async function askTrustSystem(event) {
    event.preventDefault();
    const query = conversationInput.trim();
    if (!query) {
      return;
    }

    setConversation((messages) => [
      ...messages,
      { role: "user", text: query, evidence: null },
    ]);
    setConversationInput("");
    setConversationPending(true);

    try {
      const response = await writeJson("/trust/conversation", { query });
      setConversation((messages) => [
        ...messages,
        {
          role: "system",
          text: response.answer,
          evidence: response.evidence,
        },
      ]);
    } catch (err) {
      setConversation((messages) => [
        ...messages,
        {
          role: "system",
          text:
            err instanceof Error
              ? `Conversation evidence is unavailable: ${err.message}`
              : "Conversation evidence is unavailable.",
          evidence: null,
        },
      ]);
    } finally {
      setConversationPending(false);
    }
  }

  const trustState = useMemo(() => deriveTrustState(state), [state]);
  const rollbackReady =
    Number(state.evidence.missing_traces || 0) === 0 &&
    Number(state.replayHealth.failures || 0) === 0;

  return (
    <main className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Afriprogramming trusted execution layer</p>
          <h1>We turn AI output into trusted execution.</h1>
          <p className="hero-summary">
            Afriprogramming is the missing layer between AI generation and
            real-world execution, validating, governing, and recording
            AI-driven changes before they reach real systems.
          </p>
          <div className="hero-actions" aria-label="Primary actions">
            <a className="button primary" href="mailto:pilot@afriprogramming.ai">
              Request pilot
            </a>
            <a className="button secondary" href="#proposal-view">
              View demo
            </a>
          </div>
        </div>
        <SystemTrustStatus
          trustState={trustState}
          lastUpdated={lastUpdated}
          rollbackReady={rollbackReady}
        />
      </header>

      <nav className="pipeline" aria-label="Trusted execution stages">
        {["Validate", "Govern", "Record", "Execute"].map((stage) => (
          <a key={stage} href={`#${stage.toLowerCase()}`}>
            {stage}
          </a>
        ))}
      </nav>

      {error && (
        <section className="error-banner" role="status">
          Live trust data is unavailable: {error}. Demo evidence remains visible
          for product review.
        </section>
      )}

      <section id="validate" className="section-band">
        <SectionIntro
          eyebrow="Dashboard"
          title="System Trust State"
          question="Can I trust what is currently running?"
        />
        <div className="metric-grid">
          <TrustMetric
            label="Active proposals"
            value={PROPOSALS.length}
            helper="Controlled change artifacts waiting on validation or authority."
          />
          <TrustMetric
            label="Validation failures"
            value={state.replayHealth.failures || 0}
            helper="Replay and contract checks that blocked trusted execution."
            tone={Number(state.replayHealth.failures || 0) > 0 ? "warning" : "success"}
          />
          <TrustMetric
            label="Rollback readiness"
            value={rollbackReady ? "100%" : "Review"}
            helper="Evidence that governed changes can be reversed."
            tone={rollbackReady ? "success" : "warning"}
          />
          <TrustMetric
            label="Decision records"
            value={state.evidence.receipts_count || 0}
            helper="Recorded approvals, rejections, and validation receipts."
          />
        </div>
      </section>

      <section id="proposal-view" className="section-band">
        <SectionIntro
          eyebrow="Validate"
          title="Controlled Change Interface"
          question="Is this safe to change?"
        />
        <div className="proposal-grid">
          {PROPOSALS.map((proposal) => (
            <ProposalCard key={proposal.id} proposal={proposal} />
          ))}
        </div>
      </section>

      <section id="govern" className="section-band">
        <SectionIntro
          eyebrow="Govern"
          title="Authority Layer"
          question="Under what conditions is change allowed?"
        />
        <div className="rules-grid">
          {GOVERNANCE_RULES.map((rule) => (
            <RuleCard key={rule.name} rule={rule} />
          ))}
        </div>
      </section>

      <section id="record" className="section-band split-layout">
        <div>
          <SectionIntro
            eyebrow="Record"
            title="Trust Graph"
            question="Why is the system the way it is today?"
          />
          <p className="section-note">
            Change history is auditable system memory: every replay result,
            rollback event, and governance decision becomes customer-specific
            evidence over time.
          </p>
        </div>
        <ol className="timeline">
          {CHANGE_HISTORY.map((event) => (
            <li key={`${event.time}-${event.id}`}>
              <span className="timeline-time">{event.time}</span>
              <div>
                <strong>
                  {event.id} | {event.state}
                </strong>
                <p>{event.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="section-band conversation-layout">
        <div>
          <SectionIntro
            eyebrow="Explain"
            title="Conversation Layer"
            question="Ask the trust graph why the system behaved the way it did."
          />
          <p className="section-note">
            Responses resolve to recorded evidence: proposal id, validation,
            governance decision, and execution state.
          </p>
        </div>
        <ConversationPanel
          messages={conversation}
          value={conversationInput}
          pending={conversationPending}
          onChange={setConversationInput}
          onSubmit={askTrustSystem}
        />
      </section>

      <section id="execute" className="section-band split-layout">
        <div>
          <SectionIntro
            eyebrow="Execute"
            title="Reality Check"
            question="Is the system behaving as expected right now?"
          />
          <div className="execution-state">
            <KeyValue label="Running state" value="Consistent" />
            <KeyValue
              label="Drift alerts"
              value={state.guards.length}
              tone={state.guards.length > 0 ? "warning" : "success"}
            />
            <KeyValue
              label="Contracts"
              value={state.replayHealth.status || "Enforced"}
            />
            <KeyValue
              label="Rollback readiness"
              value={rollbackReady ? "Available" : "Review required"}
              tone={rollbackReady ? "success" : "warning"}
            />
          </div>
        </div>
        <div className="event-list">
          {EXECUTION_EVENTS.map((event) => (
            <article key={event.name} className="event-row">
              <div>
                <strong>{event.name}</strong>
                <p>{event.detail}</p>
              </div>
              <span>{event.state}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="section-band">
        <SectionIntro
          eyebrow="Live operator evidence"
          title="Replay & Evidence Control"
          question="What live signals are feeding the trust surface?"
        />
        <div className="operator-grid">
          <OperatorPanel title="Active Rides">
            {state.activeRides.length === 0 ? (
              <EmptyState label="No active rides" />
            ) : (
              <div className="stack">
                {state.activeRides.map((ride) => (
                  <article key={ride.rideId} className="record-card">
                    <div className="record-card-header">
                      <strong>{ride.rideId}</strong>
                      <span>{ride.state}</span>
                    </div>
                    <p>
                      Driver: {ride.driverId || "unassigned"} | Rider:{" "}
                      {ride.riderId || "unknown"}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </OperatorPanel>

          <OperatorPanel title="Replay Health">
            <KeyValue
              label="Status"
              value={state.replayHealth.status || "NO_DATA"}
            />
            <KeyValue
              label="Replay success rate"
              value={state.replayHealth.replay_success_rate || "0%"}
            />
            <KeyValue label="Failures" value={state.replayHealth.failures || 0} />
          </OperatorPanel>

          <OperatorPanel title="Evidence Pipeline">
            <KeyValue
              label="Receipts count"
              value={state.evidence.receipts_count || 0}
            />
            <KeyValue label="Trace count" value={state.evidence.trace_count || 0} />
            <KeyValue
              label="Missing traces"
              value={state.evidence.missing_traces || 0}
              tone={
                Number(state.evidence.missing_traces || 0) > 0
                  ? "warning"
                  : "success"
              }
            />
          </OperatorPanel>

          <OperatorPanel title="Guard Violations">
            {state.guards.length === 0 ? (
              <EmptyState label="No guard violations" />
            ) : (
              <div className="stack">
                {state.guards.map((violation) => (
                  <article key={violation.id} className="record-card">
                    <div className="record-card-header">
                      <strong>{violation.type}</strong>
                      <span>{violation.severity}</span>
                    </div>
                    <p>{violation.timestamp}</p>
                  </article>
                ))}
              </div>
            )}
          </OperatorPanel>
        </div>
      </section>
    </main>
  );
}

function SystemTrustStatus({ trustState, lastUpdated, rollbackReady }) {
  return (
    <aside className="trust-status" aria-label="System trust status">
      <p>System Trust Status</p>
      <strong className={`status-${trustState.tone}`}>{trustState.label}</strong>
      <span>{trustState.summary}</span>
      <div className="trust-meta">
        <KeyValue label="Device" value={DEVICE_ID} />
        <KeyValue label="Mode" value={TEST_MODE ? "TEST_MODE" : "STANDARD"} />
        <KeyValue label="Updated" value={lastUpdated || "pending"} />
        <KeyValue
          label="Rollback"
          value={rollbackReady ? "Ready" : "Needs review"}
          tone={rollbackReady ? "success" : "warning"}
        />
      </div>
    </aside>
  );
}

function SectionIntro({ eyebrow, title, question }) {
  return (
    <div className="section-intro">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p>{question}</p>
    </div>
  );
}

function TrustMetric({ label, value, helper, tone = "neutral" }) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{helper}</p>
    </article>
  );
}

function ProposalCard({ proposal }) {
  return (
    <article className="proposal-card">
      <div className="proposal-header">
        <div>
          <span>{proposal.id}</span>
          <h3>{proposal.title}</h3>
        </div>
        <strong>{proposal.status}</strong>
      </div>
      <p>{proposal.summary}</p>
      <div className="proposal-facts">
        <KeyValue label="Surface" value={proposal.surface} />
        <KeyValue
          label="Replay validation"
          value={proposal.replay}
          tone={proposal.replay === "PASS" ? "success" : "warning"}
        />
        <KeyValue
          label="Contracts"
          value={proposal.contracts}
          tone={proposal.contracts === "PASS" ? "success" : "warning"}
        />
        <KeyValue label="Drift risk" value={proposal.driftRisk} />
        <KeyValue label="Rollback readiness" value={proposal.rollback} />
        <KeyValue label="Decision records" value={proposal.approvals} />
      </div>
    </article>
  );
}

function RuleCard({ rule }) {
  return (
    <article className="rule-card">
      <span>{rule.name}</span>
      <strong>{rule.value}</strong>
      <p>{rule.detail}</p>
    </article>
  );
}

function OperatorPanel({ title, children }) {
  return (
    <section className="operator-panel">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function ConversationPanel({ messages, value, pending, onChange, onSubmit }) {
  return (
    <aside className="conversation-panel" aria-label="Trust conversation">
      <div className="conversation-status">
        <span>Trust conversation</span>
        <strong>Evidence only</strong>
      </div>
      <div className="conversation-messages">
        {messages.map((message, index) => (
          <article
            key={`${message.role}-${index}`}
            className={`conversation-message message-${message.role}`}
          >
            <span>{message.role === "user" ? "You" : "System"}</span>
            <p>{message.text}</p>
            {message.evidence && (
              <div className="evidence-chip">
                {message.evidence.proposal_id} | {message.evidence.decision.status}
              </div>
            )}
          </article>
        ))}
      </div>
      <form className="conversation-form" onSubmit={onSubmit}>
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Ask why this was approved"
          aria-label="Trust question"
        />
        <button type="submit" disabled={pending}>
          {pending ? "Checking" : "Ask"}
        </button>
      </form>
    </aside>
  );
}

function KeyValue({ label, value, tone = "neutral" }) {
  return (
    <div className="key-value">
      <span>{label}</span>
      <strong className={`value-${tone}`}>{value}</strong>
    </div>
  );
}

function EmptyState({ label }) {
  return <div className="empty-state">{label}</div>;
}
