import React from "react";

// ============================================================
// HELPERS
// ============================================================

function StatusBadge({ status }) {
  if (!status) return null;

  const color =
    status === "ready"
      ? "green"
      : status === "incomplete"
      ? "orange"
      : "gray";

  return <span className={`badge ${color}`}>{status}</span>;
}

// ============================================================
// COMPONENT
// ============================================================

export function TraceViewer({ trace, replayStatus, onReplay }) {
  // ----------------------------------------------------------
  // EMPTY STATE
  // ----------------------------------------------------------

  if (!trace) {
    return (
      <div className="trace-viewer empty">
        <p>Select a trace to inspect</p>
      </div>
    );
  }

  // ----------------------------------------------------------
  // RENDER TRACE CORE
  // ----------------------------------------------------------

  return (
    <div className="trace-viewer">
      <header className="trace-header">
        <h2>Trace Viewer</h2>

        <button onClick={onReplay} className="replay-button">
          Run Replay Check
        </button>
      </header>

      {/* -------------------------------------------------- */}
      {/* TRACE SUMMARY */}
      {/* -------------------------------------------------- */}

      <section className="trace-summary">
        <h3>Summary</h3>

        <div className="summary-grid">
          <div>
            <strong>Trace ID:</strong>
            <div>{trace.trace_id || "unknown"}</div>
          </div>

          <div>
            <strong>Events:</strong>
            <div>{trace.events?.length || 0}</div>
          </div>

          <div>
            <strong>States:</strong>
            <div>{trace.execution_states?.length || 0}</div>
          </div>

          <div>
            <strong>Witnesses:</strong>
            <div>{trace.witnesses?.length || 0}</div>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------- */}
      {/* REPLAY STATUS */}
      {/* -------------------------------------------------- */}

      {replayStatus && (
        <section className="replay-status">
          <h3>
            Replay Inspection <StatusBadge status={replayStatus.status} />
          </h3>

          {/* Missing sections */}
          {replayStatus.missing?.length > 0 && (
            <div className="missing">
              <strong>Missing Sections:</strong>
              <ul>
                {replayStatus.missing.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Hash details */}
          <div className="hash-info">
            <div>
              <strong>Recorded Hash:</strong>
              <code>{replayStatus.recorded_hash || "none"}</code>
            </div>

            <div>
              <strong>Computed Hash:</strong>
              <code>{replayStatus.computed_hash}</code>
            </div>

            <div>
              <strong>Hash Match:</strong>{" "}
              <span
                className={
                  replayStatus.hash_matches ? "ok" : "not-ok"
                }
              >
                {replayStatus.hash_matches ? "YES ✅" : "NO ❌"}
              </span>
            </div>
          </div>
        </section>
      )}

      {/* -------------------------------------------------- */}
      {/* EVENTS */}
      {/* -------------------------------------------------- */}

      <section className="trace-section">
        <h3>Events</h3>

        {trace.events && trace.events.length > 0 ? (
          <ul className="event-list">
            {trace.events.map((event) => (
              <li key={event.event_id} className="event-item">
                <strong>{event.type}</strong>
                <div>ID: {event.event_id}</div>
                <div>Time: {event.timestamp}</div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="empty">No events</div>
        )}
      </section>

      {/* -------------------------------------------------- */}
      {/* EXECUTION STATES */}
      {/* -------------------------------------------------- */}

      <section className="trace-section">
        <h3>Execution States</h3>

        {trace.execution_states && trace.execution_states.length > 0 ? (
          <ul className="state-list">
            {trace.execution_states.map((state) => (
              <li key={state.state_id} className="state-item">
                <strong>{state.status}</strong>
                <div>ID: {state.state_id}</div>
                <div>Time: {state.timestamp}</div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="empty">No execution states</div>
        )}
      </section>

      {/* -------------------------------------------------- */}
      {/* RAW JSON VIEW */}
      {/* -------------------------------------------------- */}

      <section className="trace-section">
        <h3>Raw Trace</h3>

        <pre className="raw-json">
          {JSON.stringify(trace, null, 2)}
        </pre>
      </section>
    </div>
  );
}