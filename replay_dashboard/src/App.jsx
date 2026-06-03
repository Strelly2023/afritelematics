import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { TraceList } from "./TraceList.jsx";
import { TraceViewer } from "./TraceViewer.jsx";
import "./styles.css";

// ============================================================
// CONFIG
// ============================================================

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8000";

// ============================================================
// APP
// ============================================================

function App() {
  const [traces, setTraces] = useState([]);
  const [selectedTraceId, setSelectedTraceId] = useState(null);

  const [trace, setTrace] = useState(null);
  const [replayStatus, setReplayStatus] = useState(null);

  const [loadingList, setLoadingList] = useState(false);
  const [loadingTrace, setLoadingTrace] = useState(false);
  const [loadingReplay, setLoadingReplay] = useState(false);

  const [error, setError] = useState(null);

  // ----------------------------------------------------------
  // LOAD TRACE LIST
  // ----------------------------------------------------------

  useEffect(() => {
    async function loadTraces() {
      setLoadingList(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE}/v1/traces`);

        if (!response.ok) {
          throw new Error(`Failed to load traces (${response.status})`);
        }

        const body = await response.json();
        setTraces(body.traces || []);
      } catch (err) {
        console.error("Trace list error:", err);
        setError("Failed to load traces");
      } finally {
        setLoadingList(false);
      }
    }

    loadTraces();
  }, []);

  // ----------------------------------------------------------
  // SELECT TRACE
  // ----------------------------------------------------------

  async function selectTrace(traceId) {
    if (!traceId) return;

    setSelectedTraceId(traceId);

    // Reset derived state
    setTrace(null);
    setReplayStatus(null);
    setError(null);

    setLoadingTrace(true);

    try {
      const response = await fetch(`${API_BASE}/v1/traces/${traceId}`);

      if (!response.ok) {
        throw new Error(`Failed to load trace (${response.status})`);
      }

      const data = await response.json();

      // ✅ Core trace
      setTrace(data);
    } catch (err) {
      console.error("Trace load error:", err);
      setError("Failed to load trace");
    } finally {
      setLoadingTrace(false);
    }
  }

  // ----------------------------------------------------------
  // REPLAY TRACE (READINESS CHECK)
  // ----------------------------------------------------------

  async function replayTrace() {
    if (!selectedTraceId) return;

    setReplayStatus(null);
    setError(null);
    setLoadingReplay(true);

    try {
      const response = await fetch(
        `${API_BASE}/v1/traces/${selectedTraceId}/replay`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error(`Replay failed (${response.status})`);
      }

      const data = await response.json();

      // ✅ Replay status drives ALL observability panels
      setReplayStatus(data);
    } catch (err) {
      console.error("Replay error:", err);
      setError("Replay inspection failed");
    } finally {
      setLoadingReplay(false);
    }
  }

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (
    <main className="shell">
      {/* ===================================================== */}
      {/* SIDEBAR */}
      {/* ===================================================== */}
      <aside className="sidebar">
        <h1>AfriRide Replay</h1>

        {loadingList && <div className="loading">Loading traces...</div>}

        {error && <div className="error">{error}</div>}

        <TraceList
          traces={traces}
          selectedTraceId={selectedTraceId}
          onSelect={selectTrace}
        />
      </aside>

      {/* ===================================================== */}
      {/* WORKSPACE */}
      {/* ===================================================== */}
      <section className="workspace">
        {(loadingTrace || loadingReplay) && (
          <div className="loading">
            {loadingTrace && "Loading trace..."}
            {loadingReplay && "Running replay inspection..."}
          </div>
        )}

        <TraceViewer
          trace={trace}
          replayStatus={replayStatus}
          onReplay={replayTrace}
          isLoading={loadingTrace || loadingReplay}
        />
      </section>
    </main>
  );
}

// ============================================================
// ROOT MOUNT
// ============================================================

createRoot(document.getElementById("root")).render(<App />);