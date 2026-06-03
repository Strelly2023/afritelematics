import React from "react";

// ============================================================
// TRACE LIST
// ============================================================

export function TraceList({
  traces,
  selectedTraceId,
  onSelect,
  isLoading = false,
}) {
  // ----------------------------------------------------------
  // EMPTY STATE
  // ----------------------------------------------------------

  if (isLoading) {
    return (
      <nav className="trace-list" aria-label="Pilot traces">
        <div className="loading">Loading traces...</div>
      </nav>
    );
  }

  if (!traces || traces.length === 0) {
    return (
      <nav className="trace-list" aria-label="Pilot traces">
        <p className="empty">No traces recorded.</p>
      </nav>
    );
  }

  // ----------------------------------------------------------
  // RENDER LIST
  // ----------------------------------------------------------

  return (
    <nav className="trace-list" aria-label="Pilot traces">
      <ul className="trace-list-items">
        {traces.map((traceId, index) => {
          const isSelected = traceId === selectedTraceId;

          return (
            <li key={traceId || index}>
              <button
                className={`trace ${isSelected ? "selected" : ""}`}
                onClick={() => onSelect(traceId)}
                type="button"
                aria-current={isSelected ? "true" : "false"}
                aria-label={`Select trace ${traceId}`}
              >
                {/* ------------------------------------------------ */}
                {/* TRACE LABEL */}
                {/* ------------------------------------------------ */}
                <div className="trace-main">
                  <span className="trace-id">{traceId}</span>
                </div>

                {/* ------------------------------------------------ */}
                {/* OPTIONAL META (future-ready) */}
                {/* ------------------------------------------------ */}
                <div className="trace-meta">
                  {/* Placeholder for future metadata:
                      - timestamp
                      - status badge
                      - replay-ready indicator */}
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
